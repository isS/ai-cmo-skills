#!/usr/bin/env python3
"""fetch_site.py — Fetch and analyze a website's structure, metadata, content, and sitemap.

Part of the `website-research` skill. Prints a JSON site profile to stdout.

Python 3.10+ standard library only (urllib + html.parser). No third-party deps.

Environment variables (secrets are NEVER hardcoded):
    SITE_FETCH_USER_AGENT  Optional custom User-Agent string.
    SITE_FETCH_TIMEOUT     Optional request timeout in seconds (default: 15).
    SITE_FETCH_AUTH_TOKEN  Optional bearer token sent as an Authorization header.

Usage:
    python fetch_site.py --url https://example.com [--max-pages 5]
"""

from __future__ import annotations

import argparse
import gzip
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from html.parser import HTMLParser

DEFAULT_USER_AGENT = "website-research-bot/1.0 (+ai-cmo-skills)"
MAX_BYTES = 5 * 1024 * 1024  # cap each response body at 5 MB
MAX_BODY_CHARS = 4000        # cap extracted visible text per page
MAX_SITEMAP_URLS = 10000     # cap sitemap URL list

SKIP_LINK_EXTENSIONS = {
    ".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg", ".ico", ".css", ".js",
    ".pdf", ".zip", ".mp4", ".mp3", ".webm", ".woff", ".woff2", ".ttf",
    ".xml", ".json", ".csv", ".xlsx", ".docx", ".pptx", ".gz", ".tar",
}


class SiteHTMLParser(HTMLParser):
    """Extract title, meta tags, OG/Twitter tags, H1/H2 headings, links, and visible body text."""

    SKIP_TAGS = {"script", "style", "noscript", "template", "iframe", "svg"}

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.title: str = ""
        self.meta_description: str = ""
        self.meta_keywords: str = ""
        self.og_tags: dict[str, str] = {}
        self.headings: dict[str, list[str]] = {"h1": [], "h2": []}
        self.links: list[dict[str, str]] = []
        self.body_text_parts: list[str] = []

        self._in_title = False
        self._heading: str | None = None
        self._heading_parts: list[str] = []
        self._in_a = False
        self._a_href = ""
        self._a_parts: list[str] = []
        self._in_body = False
        self._skip_depth = 0

    def handle_starttag(self, tag: str, attrs) -> None:
        attrs = dict(attrs)
        if tag == "title":
            self._in_title = True
        elif tag == "meta":
            name = (attrs.get("name") or "").strip().lower()
            prop = (attrs.get("property") or attrs.get("itemprop") or "").strip().lower()
            content = attrs.get("content", "").strip()
            if name == "description" and not self.meta_description:
                self.meta_description = content
            elif name == "keywords" and not self.meta_keywords:
                self.meta_keywords = content
            if prop.startswith(("og:", "twitter:")):
                self.og_tags[prop] = content
        elif tag in ("h1", "h2") and self._heading is None:
            self._heading = tag
            self._heading_parts = []
        elif tag == "a":
            self._in_a = True
            self._a_href = attrs.get("href", "")
            self._a_parts = []
        elif tag == "body":
            self._in_body = True
        if tag in self.SKIP_TAGS:
            self._skip_depth += 1

    def handle_endtag(self, tag: str) -> None:
        if tag == "title":
            self._in_title = False
        elif tag in ("h1", "h2") and self._heading == tag:
            text = " ".join(" ".join(self._heading_parts).split())
            if text:
                self.headings[tag].append(text)
            self._heading = None
        elif tag == "a" and self._in_a:
            text = " ".join(" ".join(self._a_parts).split())
            self.links.append({"href": self._a_href, "text": text})
            self._in_a = False
        if tag in self.SKIP_TAGS:
            self._skip_depth = max(0, self._skip_depth - 1)

    def handle_data(self, data: str) -> None:
        if self._in_title:
            self.title += data
        elif self._heading is not None:
            self._heading_parts.append(data)
        elif self._in_a:
            self._a_parts.append(data)
        elif self._in_body and self._skip_depth == 0:
            stripped = data.strip()
            if stripped:
                self.body_text_parts.append(stripped)


def is_http_url(url: str) -> bool:
    return url.startswith(("http://", "https://"))


def same_host(url: str, host: str) -> bool:
    try:
        return urllib.parse.urlsplit(url).netloc.lower() == host
    except ValueError:
        return False


def link_path_ok(url: str) -> bool:
    """Reject non-page links (mailto/tel/javascript and binary assets)."""
    parsed = urllib.parse.urlsplit(url)
    if parsed.scheme not in ("http", "https"):
        return False
    return not parsed.path.lower().endswith(tuple(SKIP_LINK_EXTENSIONS))


def http_fetch(url: str, headers: dict[str, str], timeout: float) -> tuple[str, int, str, bytes]:
    """Return (final_url, status, content_type, body). Raises urllib.error on failure."""
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        status = getattr(resp, "status", 200)
        content_type = resp.headers.get("Content-Type", "")
        body = resp.read(MAX_BYTES + 1)
        if len(body) > MAX_BYTES:
            body = body[:MAX_BYTES]
        return resp.geturl(), status, content_type, body


def fetch_robots(origin: str, headers: dict[str, str], timeout: float) -> dict:
    """Fetch robots.txt; extract sitemap directives and blanket disallow. Never raises."""
    result: dict = {"found": False, "url": None, "sitemaps": [], "disallow_all": False, "error": None}
    robots_url = urllib.parse.urljoin(origin, "/robots.txt")
    result["url"] = robots_url
    try:
        _, status, _, raw = http_fetch(robots_url, headers, timeout)
        if status >= 400:
            result["error"] = f"HTTP {status}"
            return result
        text = raw.decode("utf-8", errors="replace")
        result["found"] = True
        result["sitemaps"] = re.findall(r"(?im)^\s*sitemap\s*:\s*(\S+)", text)
        result["disallow_all"] = any(
            re.match(r"(?im)^\s*disallow\s*:\s*/\s*$", line) for line in text.splitlines()
        )
    except urllib.error.HTTPError as exc:
        result["error"] = f"HTTP {exc.code}"
    except Exception as exc:  # noqa: BLE001 — graceful degradation for network/DNS/timeout
        result["error"] = f"{type(exc).__name__}: {exc}"
    return result


def fetch_sitemap(candidates: list[str], headers: dict[str, str], timeout: float) -> dict:
    """Try each candidate sitemap URL until one parses. Handles gzip and sitemap indexes. Never raises."""
    result: dict = {"found": False, "source": None, "urls": [], "url_count": 0, "error": None}
    for url in candidates:
        try:
            _, status, ctype, raw = http_fetch(url, headers, timeout)
            if status >= 400:
                result["error"] = f"HTTP {status} for {url}"
                continue
            if raw[:2] == b"\x1f\x8b":  # gzip magic number
                raw = gzip.decompress(raw)
            if not raw.lstrip().startswith(b"<"):
                result["error"] = f"not XML: {url}"
                continue
            root = ET.fromstring(raw)
            ns_match = re.match(r"\{[^}]*\}", root.tag)
            ns = ns_match.group(0) if ns_match else ""
            locs = [e.text.strip() for e in root.iter(f"{ns}loc") if e.text and e.text.strip()]
            result["found"] = True
            result["source"] = url
            result["url_count"] = len(locs)
            result["urls"] = locs[:MAX_SITEMAP_URLS]
            return result
        except ET.ParseError as exc:
            result["error"] = f"ParseError for {url}: {exc}"
        except Exception as exc:  # noqa: BLE001
            result["error"] = f"{type(exc).__name__} for {url}: {exc}"
    return result


def parse_html(raw: bytes) -> SiteHTMLParser:
    parser = SiteHTMLParser()
    parser.feed(raw.decode("utf-8", errors="replace"))
    parser.close()
    return parser


def classify_links(links: list[dict[str, str]], base_url: str, host: str) -> tuple[list[dict], list[dict]]:
    internal: list[dict] = []
    external: list[dict] = []
    seen: set[str] = set()
    for link in links:
        href = link["href"].strip()
        if not href or href.startswith(("#", "mailto:", "tel:", "javascript:", "data:")):
            continue
        abs_url = urllib.parse.urljoin(base_url, href)
        if not link_path_ok(abs_url):
            continue
        key = abs_url.split("#", 1)[0]
        if key in seen:
            continue
        seen.add(key)
        item = {"url": abs_url, "text": link["text"][:200]}
        if same_host(abs_url, host):
            internal.append(item)
        else:
            external.append(item)
    return internal, external


def analyze_page(url: str, headers: dict[str, str], timeout: float) -> dict:
    """Fetch one page and extract its profile. Never raises."""
    entry: dict = {
        "url": url,
        "final_url": None,
        "redirected": False,
        "status": None,
        "title": "",
        "meta_description": "",
        "meta_keywords": "",
        "og_tags": {},
        "h1": [],
        "h2": [],
        "internal_links": [],
        "external_links": [],
        "body_text": "",
        "word_count": 0,
        "error": None,
    }
    try:
        final_url, status, ctype, raw = http_fetch(url, headers, timeout)
        entry["final_url"] = final_url
        entry["status"] = status
        entry["redirected"] = final_url.rstrip("/") != url.rstrip("/")
        if "html" not in ctype.lower() and not re.search(rb"<html|<body", raw[:512], re.IGNORECASE):
            entry["error"] = f"non-HTML content ({ctype or 'unknown'})"
            return entry
        parser = parse_html(raw)
        entry["title"] = " ".join(parser.title.split())
        entry["meta_description"] = parser.meta_description
        entry["meta_keywords"] = parser.meta_keywords
        entry["og_tags"] = parser.og_tags
        entry["h1"] = parser.headings["h1"][:20]
        entry["h2"] = parser.headings["h2"][:50]
        body_text = " ".join(" ".join(parser.body_text_parts).split())
        entry["body_text"] = body_text[:MAX_BODY_CHARS]
        entry["word_count"] = len(body_text.split())
        host = urllib.parse.urlsplit(final_url).netloc.lower()
        entry["internal_links"], entry["external_links"] = classify_links(parser.links, final_url, host)
    except urllib.error.HTTPError as exc:
        entry["error"] = f"HTTP {exc.code}"
    except Exception as exc:  # noqa: BLE001
        entry["error"] = f"{type(exc).__name__}: {exc}"
    return entry


def crawl(start_url: str, headers: dict[str, str], timeout: float, max_pages: int) -> list[dict]:
    """Breadth-first crawl of up to max_pages internal pages, starting from start_url."""
    pages: list[dict] = []
    queue = [start_url]
    visited: set[str] = set()
    while queue and len(pages) < max_pages:
        url = queue.pop(0)
        if url in visited:
            continue
        visited.add(url)
        entry = analyze_page(url, headers, timeout)
        pages.append(entry)
        if entry.get("error") or not entry.get("final_url"):
            continue
        for link in entry["internal_links"]:
            clean = link["url"].split("#", 1)[0]
            if clean not in visited and clean not in queue:
                queue.append(clean)
    return pages


def build_headers() -> dict[str, str]:
    headers = {
        "User-Agent": os.environ.get("SITE_FETCH_USER_AGENT", DEFAULT_USER_AGENT),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    }
    token = os.environ.get("SITE_FETCH_AUTH_TOKEN", "").strip()
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


def dedupe(items: list[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for item in items:
        if item and item not in seen:
            seen.add(item)
            out.append(item)
    return out


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="fetch_site.py",
        description=(
            "Fetch and analyze a website (robots.txt, sitemap.xml, metadata, headings, "
            "links, body text) and print a JSON site profile to stdout."
        ),
    )
    parser.add_argument("--url", required=True, help="Target website URL, e.g. https://example.com")
    parser.add_argument(
        "--max-pages", type=int, default=5, help="Maximum number of pages to crawl (default: 5)"
    )
    args = parser.parse_args(argv)

    start_url = args.url.strip()
    if not is_http_url(start_url):
        print(json.dumps({"error": f"invalid URL: {args.url!r}", "hint": "URL must start with http:// or https://"}, ensure_ascii=False), file=sys.stderr)
        return 2

    timeout = float(os.environ.get("SITE_FETCH_TIMEOUT", "15"))
    max_pages = max(1, args.max_pages)
    headers = build_headers()

    parsed = urllib.parse.urlsplit(start_url)
    host = parsed.netloc.lower()
    origin = f"{parsed.scheme}://{parsed.netloc}"

    robots = fetch_robots(origin, headers, timeout)
    sitemap_candidates = dedupe(list(robots.get("sitemaps") or []))
    sitemap_candidates.append(urllib.parse.urljoin(origin, "/sitemap.xml"))

    profile = {
        "requested_url": start_url,
        "domain": host,
        "origin": origin,
        "robots_txt": robots,
        "sitemap": fetch_sitemap(sitemap_candidates, headers, timeout),
        "pages": crawl(start_url, headers, timeout, max_pages),
    }
    profile["page_count"] = len(profile["pages"])
    profile["redirected"] = bool(
        profile["pages"]
        and profile["pages"][0].get("final_url")
        and profile["pages"][0]["final_url"].rstrip("/") != start_url.rstrip("/")
    )
    profile["errors"] = [p["error"] for p in profile["pages"] if p.get("error")]

    print(json.dumps(profile, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
