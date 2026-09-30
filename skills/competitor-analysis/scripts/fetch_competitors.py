#!/usr/bin/env python3
"""Fetch competitor websites and extract positioning/SEO signals.

Usage:
    python fetch_competitors.py competitors.json
    python fetch_competitors.py competitors.json --output matrix.json

Input JSON file (either shape is accepted):
    ["https://competitor-a.com", "https://competitor-b.com"]
    {"competitors": ["https://competitor-a.com", "https://competitor-b.com"]}

For each URL the script fetches the page, extracts <title>, meta
description/keywords (plus Open Graph equivalents), and h1/h2/h3 headings,
then derives keyword hints from that text. Results are printed as a single
JSON document to stdout (and optionally written to --output).

Configuration is read from environment variables only — never hardcoded:
    COMPETITOR_USER_AGENT     custom User-Agent header for requests
    COMPETITOR_FETCH_TIMEOUT  per-request timeout in seconds (default: 15)
    HTTP_PROXY / HTTPS_PROXY  honored automatically by urllib

Requires Python 3.10+ (standard library only, no third-party deps).
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from datetime import datetime, timezone
from html.parser import HTMLParser
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen

MAX_BYTES = 1_500_000  # cap page size we read

# Common English stopwords so keyword hints focus on meaningful terms.
STOPWORDS = frozenset(
    """
    a about above after again all also am an and any are as at be because been
    before being below between both but by can could did do does doing down
    during each few for from further had has have having he her here hers him
    his how i if in into is it its itself just me more most my no nor not now
    of off on once only or other our out over own same she should so some such
    than that the their them then there these they this those through to too
    under until up very was we were what when where which while who whom why
    will with you your your yours free get best new top way use using make
    made need want know see work works working get started learn more about
    with without per via amp com www org net html https http
    """.split()
)

WORD_RE = re.compile(r"[a-zA-Z][a-zA-Z0-9\-]{2,}")


class PageParser(HTMLParser):
    """Extract title, meta tags, and headings from HTML (stdlib only)."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.title_parts: list[str] = []
        self.in_title = False
        self.meta_description = ""
        self.meta_keywords = ""
        self.og_title = ""
        self.og_description = ""
        self.h1: list[str] = []
        self.h2: list[str] = []
        self.h3: list[str] = []
        self._heading_tag: str | None = None
        self._heading_buf: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        tag = tag.lower()
        attr_map = {k.lower(): (v or "") for k, v in attrs}
        if tag == "title":
            self.in_title = True
        elif tag == "meta":
            name = attr_map.get("name", "").lower()
            prop = attr_map.get("property", "").lower()
            content = attr_map.get("content", "")
            if name == "description" and not self.meta_description:
                self.meta_description = content
            elif name == "keywords" and not self.meta_keywords:
                self.meta_keywords = content
            elif prop == "og:title" and not self.og_title:
                self.og_title = content
            elif prop == "og:description" and not self.og_description:
                self.og_description = content
        elif tag in ("h1", "h2", "h3"):
            self._heading_tag = tag
            self._heading_buf = []

    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()
        if tag == "title":
            self.in_title = False
        elif tag == self._heading_tag:
            text = " ".join("".join(self._heading_buf).split())
            if text:
                getattr(self, self._heading_tag).append(text)
            self._heading_tag = None
            self._heading_buf = []

    def handle_data(self, data: str) -> None:
        if self.in_title:
            self.title_parts.append(data)
        if self._heading_tag is not None:
            self._heading_buf.append(data)


def extract_keyword_hints(text: str, limit: int = 10) -> list[dict]:
    """Count frequent non-stopword tokens; return top `limit` as hints."""
    counts: dict[str, int] = {}
    for word in WORD_RE.findall(text.lower()):
        if word in STOPWORDS:
            continue
        counts[word] = counts.get(word, 0) + 1
    ranked = sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))[:limit]
    return [{"keyword": word, "count": count} for word, count in ranked]


def load_urls(path: str) -> list[str]:
    """Read a JSON file that is a list of URLs or {"competitors": [...]}."""
    with open(path, encoding="utf-8") as fh:
        data = json.load(fh)
    if isinstance(data, dict):
        data = data.get("competitors") or data.get("urls") or []
    if isinstance(data, str):
        data = [data]
    if not isinstance(data, list):
        raise ValueError("input JSON must be a list of URLs or {\"competitors\": [...]}")
    urls: list[str] = []
    for item in data:
        if not isinstance(item, str):
            raise ValueError(f"expected URL string, got {type(item).__name__}: {item!r}")
        parsed = urlparse(item)
        if parsed.scheme not in ("http", "https") or not parsed.netloc:
            raise ValueError(f"invalid http(s) URL: {item!r}")
        urls.append(item)
    return urls


def fetch_html(url: str, timeout: float, user_agent: str) -> str:
    headers = {"Accept-Encoding": "identity"}
    if user_agent:
        headers["User-Agent"] = user_agent
    request = Request(url, headers=headers)
    with urlopen(request, timeout=timeout) as resp:
        raw = resp.read(MAX_BYTES)
        charset = resp.headers.get_content_charset() or "utf-8"
    return raw.decode(charset, errors="replace")


def analyze(url: str, timeout: float, user_agent: str) -> dict:
    entry: dict = {"url": url}
    try:
        html = fetch_html(url, timeout, user_agent)
    except (HTTPError, URLError, ValueError, OSError) as exc:
        entry["status"] = "error"
        entry["error"] = f"{type(exc).__name__}: {exc}"
        return entry

    parser = PageParser()
    try:
        parser.feed(html)
        parser.close()
    except Exception as exc:  # noqa: BLE001 - report parse failures, never crash
        entry["status"] = "error"
        entry["error"] = f"parse: {type(exc).__name__}: {exc}"
        return entry

    title = parser.og_title or " ".join("".join(parser.title_parts).split())
    text_pool = " ".join(
        [title, parser.meta_description, parser.meta_keywords, parser.og_description]
        + parser.h1
        + parser.h2
        + parser.h3
    )
    entry.update(
        {
            "status": "ok",
            "title": title,
            "meta_description": parser.meta_description,
            "meta_keywords": parser.meta_keywords,
            "headings": {"h1": parser.h1, "h2": parser.h2, "h3": parser.h3},
            "keyword_hints": extract_keyword_hints(text_pool),
        }
    )
    return entry


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="fetch_competitors.py",
        description=(
            "Fetch a list of competitor URLs, extract title/meta/headings and "
            "keyword hints, and print a comparison JSON document to stdout."
        ),
    )
    parser.add_argument(
        "input",
        help='path to a JSON file with competitor URLs (a list or {"competitors": [...]})',
    )
    parser.add_argument(
        "-o",
        "--output",
        help="optional path to also write the JSON result to a file",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    try:
        timeout = float(os.environ.get("COMPETITOR_FETCH_TIMEOUT", "15"))
    except ValueError:
        print("error: COMPETITOR_FETCH_TIMEOUT must be a number", file=sys.stderr)
        return 2
    user_agent = os.environ.get("COMPETITOR_USER_AGENT", "")

    try:
        urls = load_urls(args.input)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"error: cannot load input file: {exc}", file=sys.stderr)
        return 2
    if not urls:
        print("error: no competitor URLs found in input file", file=sys.stderr)
        return 2

    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source_file": args.input,
        "competitors": [analyze(url, timeout, user_agent) for url in urls],
    }
    text = json.dumps(payload, ensure_ascii=False, indent=2)
    print(text)
    if args.output:
        with open(args.output, "w", encoding="utf-8") as fh:
            fh.write(text + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
