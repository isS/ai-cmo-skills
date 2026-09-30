#!/usr/bin/env python3
"""seo_audit.py — technical + on-page SEO audit CLI.

Audits a single URL or crawls the site's sitemap, then prints a prioritized
JSON fix plan (each fix: issue, severity, location, fix) to stdout.

Checks performed:
  - <title> presence and length
  - meta description presence and length
  - H1 uniqueness (exactly one non-empty H1 per page)
  - image alt attributes
  - canonical link presence and conflicts
  - schema.org structured data (JSON-LD)
  - robots.txt / sitemap.xml presence
  - internal linking (orphan pages, dead-end pages)

Python 3.10+ stdlib only. No third-party dependencies.

Secrets/configuration are read from environment variables only (never hardcoded):
  SEO_AUDIT_USER_AGENT        optional custom User-Agent string
  SEO_AUDIT_BASIC_AUTH_USER   optional HTTP Basic auth username
  SEO_AUDIT_BASIC_AUTH_PASS   optional HTTP Basic auth password
  SEO_AUDIT_TIMEOUT           optional request timeout in seconds (default 15)
"""

from __future__ import annotations

import argparse
import base64
import json
import os
import sys
import time
from collections import defaultdict
from html.parser import HTMLParser
from typing import Any, Optional
from urllib import error as urlerror
from urllib import parse as urlparse
from urllib import request as urlrequest
from xml.etree import ElementTree

DEFAULT_USER_AGENT = "seo-audit-skill/1.0 (+https://example.local; stdlib-urllib)"
SEVERITY_WEIGHT = {"critical": 4, "high": 3, "medium": 2, "low": 1}


# --------------------------------------------------------------------------- #
# HTML parsing
# --------------------------------------------------------------------------- #

class PageParser(HTMLParser):
    """Extracts the on-page SEO signals we care about from one HTML document."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.title: Optional[str] = None
        self.meta_description: Optional[str] = None
        self.h1_texts: list[str] = []
        self.images: list[dict[str, str]] = []  # {"src": ..., "alt": ...}
        self.canonical_links: list[str] = []
        self.json_ld: list[dict[str, Any]] = []
        self.links: list[str] = []

        self._in_title = False
        self._title_buf: list[str] = []
        self._in_h1 = False
        self._h1_buf: list[str] = []
        self._in_json_ld = False
        self._json_ld_buf: list[str] = []

    # -- helpers ----------------------------------------------------------- #

    def _flush_h1(self) -> None:
        text = " ".join("".join(self._h1_buf).split())
        self._h1_buf = []
        if text:
            self.h1_texts.append(text)

    def _flush_json_ld(self) -> None:
        raw = "".join(self._json_ld_buf).strip()
        self._json_ld_buf = []
        if not raw:
            return
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            data = {"_parse_error": True, "_raw": raw}
        self.json_ld.append(data)

    # -- element handling -------------------------------------------------- #

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self._handle_any_tag(tag, attrs)

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self._handle_any_tag(tag, attrs)

    def _handle_any_tag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attr_map = {k.lower(): (v or "") for k, v in attrs}
        tag = tag.lower()

        if tag == "title":
            self._in_title = True
            self._title_buf = []
        elif tag == "h1":
            self._in_h1 = True
            self._h1_buf = []
        elif tag == "script" and attr_map.get("type", "").lower() == "application/ld+json":
            self._in_json_ld = True
            self._json_ld_buf = []
        elif tag == "meta":
            name = attr_map.get("name", "").lower()
            if name == "description":
                self.meta_description = attr_map.get("content", "")
        elif tag == "link":
            rel = attr_map.get("rel", "").lower()
            if rel == "canonical" and attr_map.get("href"):
                self.canonical_links.append(attr_map["href"])
        elif tag == "img":
            self.images.append({"src": attr_map.get("src", ""), "alt": attr_map.get("alt", "")})
        elif tag in ("a", "area") and attr_map.get("href"):
            self.links.append(attr_map["href"])

    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()
        if tag == "title":
            self._in_title = False
            self.title = " ".join("".join(self._title_buf).split())
            self._title_buf = []
        elif tag == "h1":
            self._in_h1 = False
            self._flush_h1()
        elif tag == "script" and self._in_json_ld:
            self._in_json_ld = False
            self._flush_json_ld()

    def handle_data(self, data: str) -> None:
        if self._in_title:
            self._title_buf.append(data)
        if self._in_h1:
            self._h1_buf.append(data)
        if self._in_json_ld:
            self._json_ld_buf.append(data)


# --------------------------------------------------------------------------- #
# HTTP helpers
# --------------------------------------------------------------------------- #

def build_opener(user_agent: str) -> urlrequest.OpenerDirector:
    opener = urlrequest.build_opener()
    opener.addheaders = [("User-Agent", user_agent)]
    user = os.environ.get("SEO_AUDIT_BASIC_AUTH_USER")
    if user:
        password = os.environ.get("SEO_AUDIT_BASIC_AUTH_PASS", "")
        token = base64.b64encode(f"{user}:{password}".encode("utf-8")).decode("ascii")
        opener.addheaders.append(("Authorization", f"Basic {token}"))
    return opener


def fetch(url: str, opener: urlrequest.OpenerDirector, timeout: float) -> tuple[int | None, bytes]:
    """Return (status, body). status is None when the request failed entirely."""
    req = urlrequest.Request(url, headers={"Accept": "text/html,application/xml,application/xhtml+xml;q=0.9,*/*;q=0.8"})
    try:
        with opener.open(req, timeout=timeout) as resp:
            return resp.status, resp.read()
    except urlerror.HTTPError as exc:  # HTTP error status (e.g. 404) — return code
        return exc.code, b""
    except (urlerror.URLError, TimeoutError, OSError):
        return None, b""


def normalize_url(url: str) -> str:
    parts = urlparse.urlsplit(url.strip())
    if parts.scheme not in ("http", "https"):
        return f"https://{url.strip()}"
    return url.strip()


def origin_of(url: str) -> tuple[str, str]:
    """Return (origin, netloc) for a normalized URL."""
    parts = urlparse.urlsplit(normalize_url(url))
    origin = f"{parts.scheme}://{parts.netloc}"
    return origin, parts.netloc


# --------------------------------------------------------------------------- #
# Sitemap handling
# --------------------------------------------------------------------------- #

def _local(tag: str) -> str:
    """Strip XML namespace from a tag name."""
    return tag.rsplit("}", 1)[-1]


def _find_locs(root: ElementTree.Element, parent: str, child: str, cap: int) -> list[str]:
    out: list[str] = []
    for elem in root.iter():
        if _local(elem.tag) == parent:
            for sub in elem:
                if _local(sub.tag) == child and sub.text and sub.text.strip():
                    out.append(sub.text.strip())
                    if len(out) >= cap:
                        return out
    return out


def fetch_sitemap_locs(
    sitemap_url: str,
    opener: urlrequest.OpenerDirector,
    timeout: float,
    cap: int,
    depth: int = 0,
) -> Optional[list[str]]:
    """Return page URLs from a sitemap (following nested indexes), or None if unavailable."""
    if depth > 3:
        return None
    status, body = fetch(sitemap_url, opener, timeout)
    if status != 200 or not body:
        return None
    try:
        root = ElementTree.fromstring(body)
    except ElementTree.ParseError:
        return None

    locs: list[str] = []
    nested = _find_locs(root, "sitemap", "loc", 64)
    if nested:
        for sub_url in nested:
            if len(locs) >= cap:
                break
            more = fetch_sitemap_locs(sub_url, opener, timeout, cap - len(locs), depth + 1)
            if more:
                locs.extend(more)
    locs.extend(_find_locs(root, "url", "loc", max(cap - len(locs), 0)))
    return locs[:cap]


# --------------------------------------------------------------------------- #
# Audit checks
# --------------------------------------------------------------------------- #

def audit_page(url: str, parser: PageParser) -> list[dict[str, str]]:
    """Run all on-page checks for one page. Returns a list of fix dicts."""
    fixes: list[dict[str, str]] = []

    # 1. <title> presence + length ---------------------------------------- #
    title = (parser.title or "").strip()
    if not title:
        fixes.append({
            "issue": "Missing <title> tag",
            "severity": "critical",
            "location": url,
            "fix": "Add a unique <title> of 50-60 characters with the primary keyword near the front.",
        })
    elif len(title) < 30:
        fixes.append({
            "issue": f"<title> too short ({len(title)} chars): {title!r}",
            "severity": "high",
            "location": url,
            "fix": "Expand the <title> to 50-60 characters, leading with the target keyword for this page.",
        })
    elif len(title) > 60:
        fixes.append({
            "issue": f"<title> too long ({len(title)} chars): {title[:50]!r}...",
            "severity": "medium",
            "location": url,
            "fix": "Trim the <title> to <=60 characters so it is not truncated in SERPs; keep the keyword near the front.",
        })

    # 2. meta description -------------------------------------------------- #
    desc = (parser.meta_description or "").strip()
    if not desc:
        fixes.append({
            "issue": "Missing meta description",
            "severity": "high",
            "location": url,
            "fix": "Add a <meta name=\"description\"> of 70-160 characters that summarizes the page and includes the target keyword.",
        })
    elif len(desc) < 70:
        fixes.append({
            "issue": f"Meta description too short ({len(desc)} chars)",
            "severity": "medium",
            "location": url,
            "fix": "Expand the meta description to 70-160 characters with a clear value proposition.",
        })
    elif len(desc) > 160:
        fixes.append({
            "issue": f"Meta description too long ({len(desc)} chars)",
            "severity": "medium",
            "location": url,
            "fix": "Trim the meta description to <=160 characters so it is not truncated in SERPs.",
        })

    # 3. H1 uniqueness ------------------------------------------------------ #
    if not parser.h1_texts:
        fixes.append({
            "issue": "Page has no <h1> heading",
            "severity": "high",
            "location": url,
            "fix": "Add exactly one <h1> describing the page topic and containing the target keyword.",
        })
    elif len(parser.h1_texts) > 1:
        fixes.append({
            "issue": f"Page has {len(parser.h1_texts)} <h1> headings (must be unique)",
            "severity": "critical",
            "location": url,
            "fix": "Keep a single <h1> per page; demote the others to <h2>/<h3>.",
        })

    # 4. image alt ---------------------------------------------------------- #
    missing_alt = [img for img in parser.images if not img["alt"].strip()]
    if missing_alt:
        examples = ", ".join(img["src"][:60] or "(no src)" for img in missing_alt[:5])
        extra = f" and {len(missing_alt) - 5} more" if len(missing_alt) > 5 else ""
        fixes.append({
            "issue": f"{len(missing_alt)} <img> element(s) missing alt text: {examples}{extra}",
            "severity": "medium",
            "location": url,
            "fix": "Add descriptive alt text to every content <img> (empty alt=\"\" is fine only for decorative images).",
        })

    # 5. canonical ---------------------------------------------------------- #
    if not parser.canonical_links:
        fixes.append({
            "issue": "Missing canonical link",
            "severity": "critical",
            "location": url,
            "fix": "Add <link rel=\"canonical\" href=\"...\"> pointing to the preferred version of this URL.",
        })
    elif len(parser.canonical_links) > 1:
        fixes.append({
            "issue": f"{len(parser.canonical_links)} conflicting canonical links on one page",
            "severity": "high",
            "location": url,
            "fix": "Keep exactly one canonical link; remove the duplicates and consolidate to the preferred URL.",
        })

    # 6. schema.org markup -------------------------------------------------- #
    if not parser.json_ld:
        fixes.append({
            "issue": "No schema.org structured data (JSON-LD)",
            "severity": "medium",
            "location": url,
            "fix": "Add JSON-LD structured data (e.g. Organization, WebSite, Product, Article) matching the page type.",
        })
    elif any(isinstance(b, dict) and b.get("_parse_error") for b in parser.json_ld):
        fixes.append({
            "issue": "Invalid JSON-LD markup (failed to parse)",
            "severity": "low",
            "location": url,
            "fix": "Validate the JSON-LD with the Rich Results test and fix the syntax error.",
        })

    # 7. internal links (per-page) ----------------------------------------- #
    internal = [h for h in parser.links if is_internal_link(url, h)]
    if not internal:
        fixes.append({
            "issue": "Page has no outgoing internal links",
            "severity": "low",
            "location": url,
            "fix": "Link from this page to at least 3-5 related internal pages to pass link equity and aid crawling.",
        })

    return fixes


def is_internal_link(page_url: str, href: str) -> bool:
    target = urlparse.urljoin(page_url, href)
    page_parts = urlparse.urlsplit(page_url)
    target_parts = urlparse.urlsplit(target)
    if target_parts.scheme not in ("http", "https"):
        return False  # mailto:, tel:, javascript: etc.
    if target_parts.netloc != page_parts.netloc:
        return False  # external link
    if target_parts.path == page_parts.path and not target_parts.fragment:
        return False  # self-link without fragment
    return True


# --------------------------------------------------------------------------- #
# Main
# --------------------------------------------------------------------------- #

def parse_args(argv: Optional[list[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="seo_audit.py",
        description="Technical + on-page SEO audit. Prints a prioritized JSON fix plan to stdout.",
        epilog="Secrets via env vars: SEO_AUDIT_USER_AGENT, SEO_AUDIT_BASIC_AUTH_USER, "
               "SEO_AUDIT_BASIC_AUTH_PASS, SEO_AUDIT_TIMEOUT.",
    )
    parser.add_argument("url", help="Website URL to audit (e.g. https://example.com)")
    parser.add_argument("--crawl", action="store_true",
                        help="Crawl the sitemap and audit multiple pages (default: single page only)")
    parser.add_argument("--sitemap", help="Explicit sitemap URL (default: <origin>/sitemap.xml)")
    parser.add_argument("--max-pages", type=int, default=20,
                        help="Max pages to audit when crawling (default: 20)")
    parser.add_argument("--timeout", type=float, default=None,
                        help="Request timeout in seconds (default: SEO_AUDIT_TIMEOUT or 15)")
    parser.add_argument("--output", help="Also write the JSON fix plan to this file path")
    return parser.parse_args(argv)


def main(argv: Optional[list[str]] = None) -> int:
    args = parse_args(argv)

    timeout = args.timeout or float(os.environ.get("SEO_AUDIT_TIMEOUT", "15"))
    user_agent = os.environ.get("SEO_AUDIT_USER_AGENT", DEFAULT_USER_AGENT)
    opener = build_opener(user_agent)

    target_url = normalize_url(args.url)
    origin, netloc = origin_of(target_url)
    sitemap_url = args.sitemap or urlparse.urljoin(origin + "/", "sitemap.xml")

    fixes: list[dict[str, str]] = []
    audit_info: dict[str, Any] = {
        "url": target_url,
        "mode": "crawl" if args.crawl else "single",
        "pages_audited": 0,
        "sitemap_url": sitemap_url,
    }

    # ---- decide which pages to audit ------------------------------------ #
    pages: list[str] = []
    if args.crawl:
        locs = fetch_sitemap_locs(sitemap_url, opener, timeout, args.max_pages)
        if locs is None:
            fixes.append({
                "issue": f"Sitemap not found or unparsable at {sitemap_url}",
                "severity": "high",
                "location": origin,
                "fix": "Publish a valid XML sitemap at /sitemap.xml and reference it from robots.txt.",
            })
            audit_info["mode"] = "crawl (sitemap failed — fell back to single page)"
            pages = [target_url]
        else:
            pages = list(dict.fromkeys([target_url, *locs]))[: args.max_pages]
    else:
        pages = [target_url]

    # ---- audit each page ------------------------------------------------- #
    page_parsers: dict[str, PageParser] = {}
    for page_url in pages:
        status, body = fetch(page_url, opener, timeout)
        if status is None:
            fixes.append({
                "issue": f"Page unreachable (network error): {page_url}",
                "severity": "critical",
                "location": page_url,
                "fix": "Check DNS, SSL certificate, and server availability; retry the audit.",
            })
            continue
        if status != 200:
            fixes.append({
                "issue": f"Page returns HTTP {status}",
                "severity": "critical",
                "location": page_url,
                "fix": "Fix the HTTP status (redirect or serve 200) and remove internal links pointing at this URL.",
            })
            continue
        parser = PageParser()
        parser.feed(body.decode("utf-8", errors="replace"))
        page_parsers[page_url] = parser
        audit_info["pages_audited"] += 1
        fixes.extend(audit_page(page_url, parser))

    # ---- site-level checks: robots.txt + sitemap -------------------------- #
    robots_url = urlparse.urljoin(origin + "/", "robots.txt")
    status, body = fetch(robots_url, opener, timeout)
    if status != 200 or not body:
        fixes.append({
            "issue": "robots.txt missing",
            "severity": "medium",
            "location": robots_url,
            "fix": "Publish a robots.txt at the site root (even an empty one) to guide crawlers.",
        })
    else:
        text = body.decode("utf-8", errors="replace")
        if "sitemap:" not in text.lower():
            fixes.append({
                "issue": "robots.txt does not reference the sitemap",
                "severity": "low",
                "location": robots_url,
                "fix": f"Add a line 'Sitemap: {sitemap_url}' to robots.txt.",
            })

    if not args.crawl:
        status, _ = fetch(sitemap_url, opener, timeout)
        if status != 200:
            fixes.append({
                "issue": f"Sitemap not found at {sitemap_url}",
                "severity": "high",
                "location": origin,
                "fix": "Generate and publish an XML sitemap at /sitemap.xml and reference it from robots.txt.",
            })

    # ---- internal linking across the crawl ------------------------------- #
    if len(page_parsers) > 1:
        inlinks: dict[str, int] = defaultdict(int)
        for page_url, parser in page_parsers.items():
            seen: set[str] = set()
            for href in parser.links:
                target = urlparse.urljoin(page_url, href)
                parts = urlparse.urlsplit(target)
                if parts.netloc == netloc and target in page_parsers and target != page_url:
                    if target not in seen:
                        seen.add(target)
                        inlinks[target] += 1
        for page_url in page_parsers:
            if inlinks[page_url] == 0:
                fixes.append({
                    "issue": "Orphan page: no internal links point to it from other audited pages",
                    "severity": "medium",
                    "location": page_url,
                    "fix": "Add internal links to this page from at least one related page (nav, related posts, or hub page).",
                })

        # duplicate titles across pages ------------------------------------ #
        titles_by: dict[str, list[str]] = defaultdict(list)
        for page_url, parser in page_parsers.items():
            titles_by[(parser.title or "").strip().lower()].append(page_url)
        for title, urls in titles_by.items():
            if title and len(urls) > 1:
                fixes.append({
                    "issue": f"Duplicate <title> across {len(urls)} pages: {title[:60]!r}",
                    "severity": "high",
                    "location": urls[0],
                    "fix": f"Rewrite unique titles for {', '.join(urls[1:4])} so each page targets a distinct keyword.",
                })

    # ---- rank and summarize ---------------------------------------------- #
    fixes.sort(key=lambda f: SEVERITY_WEIGHT.get(f["severity"], 0), reverse=True)
    summary = {"critical": 0, "high": 0, "medium": 0, "low": 0, "total": len(fixes)}
    for fix in fixes:
        sev = fix["severity"]
        if sev in summary:
            summary[sev] += 1

    result = {
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "audit": audit_info,
        "fixes": fixes,
        "summary": summary,
    }

    print(json.dumps(result, indent=2, ensure_ascii=False))
    if args.output:
        try:
            os.makedirs(os.path.dirname(os.path.abspath(args.output)), exist_ok=True)
            with open(args.output, "w", encoding="utf-8") as fh:
                json.dump(result, fh, indent=2, ensure_ascii=False)
            print(f"[seo_audit] fix plan written to {args.output}", file=sys.stderr)
        except OSError as exc:
            print(f"[seo_audit] could not write output file: {exc}", file=sys.stderr)
            return 3

    # exit 2 when nothing at all could be audited; else success
    return 0 if audit_info["pages_audited"] > 0 else 2


if __name__ == "__main__":
    sys.exit(main())
