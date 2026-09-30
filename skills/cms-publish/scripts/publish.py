#!/usr/bin/env python3
"""cms-publish: POST a content file (Markdown/HTML) to a CMS REST API as a draft or a live publish.

Supported CMS backends (set via the CMS_TYPE environment variable):
  wordpress  — posts to {CMS_API_URL}/wp-json/wp/v2/posts (or the full endpoint if CMS_API_URL already contains /wp-json/)
  webflow    — posts to CMS_API_URL (a full endpoint, e.g. .../collections/{id}/items) with fieldData payload
  custom     — posts to CMS_API_URL with a plain {title, slug, content, status} payload

All secrets are read from environment variables and are NEVER hardcoded:
  CMS_TYPE       wordpress | webflow | custom   (required)
  CMS_API_URL    base URL or full REST endpoint (required)
  CMS_API_TOKEN  bearer token                    (required)

Exit codes: 0 on success, 1 on any error. Exactly one JSON object is printed
to stdout on success; errors are printed as JSON to stderr.

Requires Python 3.10+ and the standard library only (urllib).
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request
from html import escape
from pathlib import Path

RETRYABLE_STATUS = {429, 500, 502, 503, 504}
DEFAULT_MAX_RETRIES = 3
REQUEST_TIMEOUT_SECONDS = 30

FRONTMATTER_RE = re.compile(r"\A---\s*\n(.*?)\n---\s*\n?", re.DOTALL)

INLINE_PATTERNS = [
    (re.compile(r"`([^`]+)`"), r"<code>\1</code>"),
    (re.compile(r"!\[([^\]]*)\]\(([^)\s]+)\)"), r'<img src="\2" alt="\1">'),
    (re.compile(r"\[([^\]]+)\]\(([^)\s]+)\)"), r'<a href="\2">\1</a>'),
    (re.compile(r"\*\*([^*]+)\*\*"), r"<strong>\1</strong>"),
    (re.compile(r"\*([^*]+)\*"), r"<em>\1</em>"),
]


def fail(message: str, http_status=None) -> None:
    """Print a machine-readable error JSON to stderr and exit non-zero."""
    payload = {"ok": False, "error": message}
    if http_status is not None:
        payload["http_status"] = http_status
    print(json.dumps(payload, ensure_ascii=False), file=sys.stderr)
    sys.exit(1)


def split_frontmatter(text: str):
    """Return (metadata_dict, body) with an optional leading YAML-ish frontmatter block."""
    match = FRONTMATTER_RE.match(text)
    if not match:
        return {}, text
    meta = {}
    for line in match.group(1).splitlines():
        if ":" in line:
            key, value = line.split(":", 1)
            meta[key.strip()] = value.strip().strip("'\"")
    return meta, text[match.end():]


def slugify(text: str) -> str:
    slug = text.lower().strip()
    slug = re.sub(r"[^a-z0-9\u4e00-\u9fff]+", "-", slug)
    return slug.strip("-") or "post"


def inline(text: str) -> str:
    """Minimal Markdown inline conversion (code, images, links, bold, italic)."""
    text = escape(text)
    for pattern, repl in INLINE_PATTERNS:
        text = pattern.sub(repl, text)
    return text


def md_to_html(md: str) -> str:
    """Minimal stdlib Markdown-to-HTML converter: headings, hr, blockquotes, lists, code fences, paragraphs."""
    lines = md.strip().split("\n")
    out = []
    list_tag = None
    in_quote = False
    i = 0

    def close_list():
        nonlocal list_tag
        if list_tag:
            out.append(f"</{list_tag}>")
            list_tag = None

    def close_quote():
        nonlocal in_quote
        if in_quote:
            out.append("</blockquote>")
            in_quote = False

    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        if stripped.startswith("```"):
            close_list()
            close_quote()
            buf = []
            i += 1
            while i < len(lines) and not lines[i].strip().startswith("```"):
                buf.append(lines[i])
                i += 1
            i += 1  # skip the closing fence
            out.append("<pre><code>" + escape("\n".join(buf)) + "</code></pre>")
            continue

        heading = re.match(r"^(#{1,6})\s+(.*)$", stripped)
        if heading:
            close_list()
            close_quote()
            level = len(heading.group(1))
            out.append(f"<h{level}>{inline(heading.group(2))}</h{level}>")
            i += 1
            continue

        if re.fullmatch(r"([-*_])(\s*\1){2,}", stripped) or re.fullmatch(r"-{3,}", stripped):
            close_list()
            close_quote()
            out.append("<hr>")
            i += 1
            continue

        if stripped.startswith(">"):
            close_list()
            if not in_quote:
                out.append("<blockquote>")
                in_quote = True
            out.append(inline(stripped.lstrip(">").strip()))
            i += 1
            continue

        if in_quote and stripped:
            close_quote()
            continue  # reprocess this line as normal content

        bullet = re.match(r"^[-*+]\s+(.*)$", stripped)
        if bullet:
            close_quote()
            if list_tag != "ul":
                close_list()
                out.append("<ul>")
                list_tag = "ul"
            out.append("<li>" + inline(bullet.group(1)) + "</li>")
            i += 1
            continue

        numbered = re.match(r"^\d+[.)]\s+(.*)$", stripped)
        if numbered:
            close_quote()
            if list_tag != "ol":
                close_list()
                out.append("<ol>")
                list_tag = "ol"
            out.append("<li>" + inline(numbered.group(1)) + "</li>")
            i += 1
            continue

        close_list()
        if stripped:
            close_quote()
            out.append("<p>" + inline(stripped) + "</p>")
        i += 1

    close_list()
    close_quote()
    return "\n".join(out)


def build_payload(cms_type: str, meta: dict, html_content: str, status: str, title: str, slug: str) -> dict:
    final_title = (title or meta.get("title") or "").strip()
    final_slug = (slug or meta.get("slug") or slugify(final_title)).strip()
    excerpt = (meta.get("description") or meta.get("excerpt") or "").strip()

    if cms_type == "wordpress":
        payload = {"title": final_title, "slug": final_slug, "content": html_content, "status": status}
        if excerpt:
            payload["excerpt"] = excerpt
        return payload
    if cms_type == "webflow":
        payload = {
            "fieldData": {"name": final_title, "slug": final_slug, "content": html_content},
            "isDraft": status == "draft",
        }
        return payload
    # custom
    return {"title": final_title, "slug": final_slug, "content": html_content, "status": status}


def resolve_endpoint(cms_type: str, api_url: str) -> str:
    url = api_url.rstrip("/")
    if cms_type == "wordpress" and "/wp-json/" not in url:
        return url + "/wp-json/wp/v2/posts"
    return url


def backoff_seconds(headers, attempt: int) -> float:
    """Honor the Retry-After header when present, otherwise exponential backoff."""
    retry_after = headers.get("Retry-After") if headers else None
    if retry_after:
        try:
            return float(retry_after)
        except ValueError:
            pass
    return min(2 ** attempt, 8)


def post_with_retry(endpoint: str, payload: dict, token: str, max_retries: int):
    """POST the payload, retrying on 429/5xx. Returns (http_status_or_None, response_body)."""
    data = json.dumps(payload).encode("utf-8")
    headers = {
        "Content-Type": "application/json",
        "User-Agent": "ai-cmo-cms-publish/1.0",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"

    for attempt in range(max_retries + 1):
        request = urllib.request.Request(endpoint, data=data, headers=headers, method="POST")
        try:
            with urllib.request.urlopen(request, timeout=REQUEST_TIMEOUT_SECONDS) as response:
                return response.status, response.read().decode("utf-8", "replace")
        except urllib.error.HTTPError as error:
            body = error.read().decode("utf-8", "replace")
            if error.code in RETRYABLE_STATUS and attempt < max_retries:
                time.sleep(backoff_seconds(error.headers, attempt))
                continue
            return error.code, body
        except (urllib.error.URLError, TimeoutError, OSError) as error:
            if attempt < max_retries:
                time.sleep(min(2 ** attempt, 8))
                continue
            return None, str(error)
    return None, "request failed after retries"


def extract_result(cms_type: str, parsed: dict) -> dict:
    if cms_type == "wordpress":
        return {
            "post_id": parsed.get("id"),
            "url": parsed.get("link") or parsed.get("url"),
        }
    if cms_type == "webflow":
        return {
            "item_id": parsed.get("id") or parsed.get("_id"),
            "url": parsed.get("url"),
        }
    return {
        "post_id": parsed.get("id") or parsed.get("_id"),
        "url": parsed.get("url") or parsed.get("link"),
    }


def main(argv=None) -> None:
    parser = argparse.ArgumentParser(
        prog="publish.py",
        description=(
            "POST a content file (Markdown/HTML) to a CMS REST API as a draft or a live publish. "
            "Secrets come from env vars CMS_TYPE / CMS_API_URL / CMS_API_TOKEN."
        ),
        epilog=(
            "Default is --draft (safe). A live publish requires the explicit --publish flag "
            "AND prior two-phase human approval (see skills/cms-publish/SKILL.md)."
        ),
    )
    parser.add_argument("content_file", help="path to a Markdown or HTML content file")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--draft", dest="publish", action="store_false", help="create as draft (default)")
    mode.add_argument("--publish", dest="publish", action="store_true", help="publish live — requires two-phase human approval")
    parser.set_defaults(publish=False)
    parser.add_argument("--title", help="override the title (default: frontmatter title, first H1, or filename)")
    parser.add_argument("--slug", help="override the slug (default: frontmatter slug or slugified title)")
    parser.add_argument(
        "--max-retries",
        type=int,
        default=DEFAULT_MAX_RETRIES,
        help=f"max retries on 429/5xx (default: {DEFAULT_MAX_RETRIES})",
    )
    args = parser.parse_args(argv)

    cms_type = os.environ.get("CMS_TYPE", "").strip().lower()
    api_url = os.environ.get("CMS_API_URL", "").strip()
    token = os.environ.get("CMS_API_TOKEN", "").strip()

    if cms_type not in {"wordpress", "webflow", "custom"}:
        fail(f"CMS_TYPE must be one of wordpress/webflow/custom, got {cms_type!r}")
    if not api_url.startswith(("http://", "https://")):
        fail(f"CMS_API_URL must start with http:// or https://, got {api_url!r}")
    if not token:
        fail("CMS_API_TOKEN is required — read from the environment, never hardcoded")

    try:
        raw = Path(args.content_file).read_text(encoding="utf-8")
    except OSError as error:
        fail(f"cannot read content file: {error}")

    is_html = args.content_file.lower().endswith((".html", ".htm"))
    meta, body = split_frontmatter(raw)
    html_content = body if is_html else md_to_html(body)

    title = (args.title or meta.get("title") or "").strip()
    if not title:
        first_h1 = re.search(r"^#\s+(.+)$", body, re.MULTILINE)
        title = (first_h1.group(1).strip() if first_h1 else Path(args.content_file).stem).strip()
    if not title:
        fail("cannot determine a title — pass --title or add one to the file's frontmatter")

    status = "publish" if args.publish else "draft"
    endpoint = resolve_endpoint(cms_type, api_url)
    payload = build_payload(cms_type, meta, html_content, status, title, args.slug)

    http_status, response_body = post_with_retry(endpoint, payload, token, args.max_retries)

    try:
        parsed = json.loads(response_body) if response_body else {}
    except json.JSONDecodeError:
        parsed = {}

    if http_status is None or http_status >= 400:
        snippet = response_body[:500] if isinstance(response_body, str) else str(response_body)
        fail(f"CMS request failed: {snippet}", http_status=http_status)

    result = {
        "ok": True,
        "cms_type": cms_type,
        "status": status,
        "http_status": http_status,
    }
    if parsed.get("status") and isinstance(parsed.get("status"), str):
        result["cms_status"] = parsed["status"]
    result.update(extract_result(cms_type, parsed))
    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
