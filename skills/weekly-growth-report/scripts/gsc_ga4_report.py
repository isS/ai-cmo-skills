#!/usr/bin/env python3
"""gsc_ga4_report.py — Pull GSC + GA4 data and produce a weekly growth report.

Ingests Google Search Console + Google Analytics 4 data (CSV exports or, in
`--fetch` mode, the Google APIs) and produces a weekly growth report:
- traffic / click / impression trends with week-over-week deltas
- top pages and top keywords
- wins and losses vs the prior period, attributed to pages/queries
- a concrete next-week priority list, optionally tied to content-gap and
  seo-audit artifacts

Outputs:
- JSON report on stdout (always, for the orchestrating Agent to parse)
- Markdown report at --output (default outputs/weekly-growth-report/weekly-report.md)
- optional JSON copy via --output-json

Requirements:
- CSV mode: Python 3.10+ standard library only (no third-party deps)
- --fetch API mode: google-api-python-client + google-auth
  (see scripts/requirements.txt)

Secrets are read from environment variables ONLY, never hardcoded:
- GOOGLE_APPLICATION_CREDENTIALS: path to a service-account JSON (shared by
  GSC and GA4; GSC_CREDENTIALS / GA4_CREDENTIALS override per-source)
- GA4_PROPERTY_ID: numeric GA4 property id (API mode)
- GSC_SITE: Search Console site URL, e.g. sc-domain:example.com (API mode)
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import sys
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any, Callable, Dict, Iterable, List, Optional, Tuple

DEFAULT_OUTPUT = "outputs/weekly-growth-report/weekly-report.md"

# ---------------------------------------------------------------------------
# CSV column aliases (headers are lowercased/stripped before matching)
# ---------------------------------------------------------------------------

GSC_QUERY_COLS = ("query", "top queries", "top query", "search query", "keyword")
GSC_PAGE_COLS = ("page", "top pages", "url", "landing page")
GSC_CLICK_COLS = ("clicks",)
GSC_IMPR_COLS = ("impressions",)
GSC_CTR_COLS = ("ctr",)
GSC_POS_COLS = ("position", "average position")

GA4_PAGE_COLS = (
    "page path and screen class",
    "page path",
    "page",
    "landing page",
    "path",
    "page location",
)
GA4_SESSION_COLS = ("sessions",)
GA4_USER_COLS = ("total users", "users", "active users")
GA4_CONV_COLS = ("key events", "conversions", "purchases", "transactions")
GA4_ENGAGED_COLS = ("engaged sessions",)

TOP_N = 10  # top pages / queries in the report
WIN_LOSS_N = 5  # number of wins / losses to surface


# ---------------------------------------------------------------------------
# small helpers
# ---------------------------------------------------------------------------


def warn(msg: str) -> None:
    """Log a warning to stderr (stdout is reserved for the JSON report)."""
    print(f"[warn] {msg}", file=sys.stderr)


def to_number(value: Any) -> float:
    """Parse a numeric value from CSV/API input; return 0.0 when absent."""
    if value is None or value == "":
        return 0.0
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def pct(new: float, old: float) -> Optional[float]:
    """Percentage change from old to new; None when old is zero/absent."""
    if not old:
        return None
    return round((new - old) / old * 100.0, 1)


def find_col(headers: Iterable[str], aliases: Iterable[str]) -> Optional[str]:
    """Find the first header (by original name) matching any alias."""
    wanted = {a.strip().lower() for a in aliases}
    for header in headers:
        h = str(header).strip().lower()
        if h in wanted or any(a in h for a in wanted if len(a) > 4):
            return str(header)
    return None


def parse_date(value: str) -> date:
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError as exc:
        raise SystemExit(f"invalid date '{value}' (expected YYYY-MM-DD)") from exc


# ---------------------------------------------------------------------------
# loading rows (CSV or JSON)
# ---------------------------------------------------------------------------


def read_rows(path: str) -> List[Dict[str, Any]]:
    """Load rows from a CSV or JSON file.

    JSON may be a list of row objects, or an object with a "rows"/"results"
    key (e.g. a pre-normalized export).
    """
    p = Path(path)
    if not p.exists():
        raise SystemExit(f"file not found: {path}")
    if p.suffix.lower() == ".json":
        with open(p, encoding="utf-8") as fh:
            data = json.load(fh)
        if isinstance(data, list):
            return data
        if isinstance(data, dict):
            return data.get("rows") or data.get("results") or []
        raise SystemExit(f"unsupported JSON structure in {path}")
    if p.suffix.lower() == ".csv":
        with open(p, encoding="utf-8-sig", newline="") as fh:
            return list(csv.DictReader(fh))
    raise SystemExit(f"unsupported file type (use .csv or .json): {path}")


# ---------------------------------------------------------------------------
# GSC parsing
# ---------------------------------------------------------------------------


def parse_gsc_rows(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Normalize GSC rows to {query, page, clicks, impressions, ctr, position}.

    Handles both CSV exports (column aliases) and the GSC API row format
    ({"keys": ["page", "query"], "clicks": ..., ...}).
    """
    parsed: List[Dict[str, Any]] = []
    headers = list(rows[0].keys()) if rows else []
    q_col = find_col(headers, GSC_QUERY_COLS)
    p_col = find_col(headers, GSC_PAGE_COLS)
    c_col = find_col(headers, GSC_CLICK_COLS)
    i_col = find_col(headers, GSC_IMPR_COLS)
    ctr_col = find_col(headers, GSC_CTR_COLS)
    pos_col = find_col(headers, GSC_POS_COLS)

    for row in rows:
        if "keys" in row and isinstance(row.get("keys"), list):
            keys = row["keys"]
            item = {
                "query": keys[1] if len(keys) > 1 else "",
                "page": keys[0] if keys else "",
                "clicks": to_number(row.get("clicks")),
                "impressions": to_number(row.get("impressions")),
                "ctr": to_number(row.get("ctr")),
                "position": to_number(row.get("position")),
            }
        else:
            item = {
                "query": str(row.get(q_col) or "") if q_col else "",
                "page": str(row.get(p_col) or "") if p_col else "",
                "clicks": to_number(row.get(c_col) if c_col else 0),
                "impressions": to_number(row.get(i_col) if i_col else 0),
                "ctr": to_number(row.get(ctr_col) if ctr_col else 0),
                "position": to_number(row.get(pos_col) if pos_col else 0),
            }
        if not item["query"] and not item["page"]:
            continue
        if item["impressions"] and not item["ctr"]:
            item["ctr"] = item["clicks"] / item["impressions"]
        parsed.append(item)
    return parsed


def summarize_gsc(rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Aggregate GSC rows into totals + top pages + top queries."""
    totals = {"clicks": 0.0, "impressions": 0.0, "ctr": 0.0, "position": 0.0}
    pages: Dict[str, Dict[str, float]] = {}
    queries: Dict[str, Dict[str, float]] = {}

    for r in rows:
        cl = r["clicks"]
        im = r["impressions"]
        totals["clicks"] += cl
        totals["impressions"] += im
        totals["position"] += r["position"] * im

        for bucket, key in ((pages, r["page"]), (queries, r["query"])):
            if not key:
                continue
            entry = bucket.setdefault(key, {"clicks": 0.0, "impressions": 0.0, "position": 0.0})
            entry["clicks"] += cl
            entry["impressions"] += im
            entry["position"] += r["position"] * im

    if totals["impressions"]:
        totals["ctr"] = totals["clicks"] / totals["impressions"]
        totals["position"] = totals["position"] / totals["impressions"]

    def finalize(bucket: Dict[str, Dict[str, float]]) -> List[Dict[str, Any]]:
        out = []
        for key, v in bucket.items():
            pos = v["position"] / v["impressions"] if v["impressions"] else 0.0
            out.append(
                {
                    "key": key,
                    "clicks": round(v["clicks"], 1),
                    "impressions": round(v["impressions"], 1),
                    "position": round(pos, 1),
                }
            )
        return sorted(out, key=lambda x: x["clicks"], reverse=True)[:TOP_N]

    return {
        "totals": {k: round(v, 4) for k, v in totals.items()},
        "top_pages": finalize(pages),
        "top_queries": finalize(queries),
    }


# ---------------------------------------------------------------------------
# GA4 parsing
# ---------------------------------------------------------------------------


def parse_ga4_rows(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Normalize GA4 rows to {page, sessions, users, conversions}."""
    parsed: List[Dict[str, Any]] = []
    headers = list(rows[0].keys()) if rows else []
    p_col = find_col(headers, GA4_PAGE_COLS)
    s_col = find_col(headers, GA4_SESSION_COLS)
    u_col = find_col(headers, GA4_USER_COLS)
    c_col = find_col(headers, GA4_CONV_COLS)

    for row in rows:
        item = {
            "page": str(row.get(p_col) or "") if p_col else "",
            "sessions": to_number(row.get(s_col) if s_col else 0),
            "users": to_number(row.get(u_col) if u_col else 0),
            "conversions": to_number(row.get(c_col) if c_col else 0),
        }
        if not item["page"]:
            continue
        parsed.append(item)
    return parsed


def summarize_ga4(rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    totals = {"sessions": 0.0, "users": 0.0, "conversions": 0.0}
    pages: Dict[str, Dict[str, float]] = {}
    for r in rows:
        totals["sessions"] += r["sessions"]
        totals["users"] += r["users"]
        totals["conversions"] += r["conversions"]
        key = r["page"]
        entry = pages.setdefault(key, {"sessions": 0.0, "users": 0.0, "conversions": 0.0})
        for metric in ("sessions", "users", "conversions"):
            entry[metric] += r[metric]
    top_pages = sorted(
        (
            {"key": k, **{m: round(v[m], 1) for m in ("sessions", "users", "conversions")}}
            for k, v in pages.items()
        ),
        key=lambda x: x["sessions"],
        reverse=True,
    )[:TOP_N]
    return {"totals": {k: round(v, 1) for k, v in totals.items()}, "top_pages": top_pages}


# ---------------------------------------------------------------------------
# API mode (optional third-party deps)
# ---------------------------------------------------------------------------

GSC_SCOPES = ["https://www.googleapis.com/auth/webmasters.readonly"]
GA4_SCOPES = ["https://www.googleapis.com/auth/analytics.readonly"]


def _load_api_credentials(scopes: List[str], env_key: Optional[str]) -> Any:
    from google.oauth2 import service_account  # noqa: PLC0415
    import google.auth  # noqa: PLC0415

    path = (
        (os.environ.get(env_key) if env_key else None)
        or os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
        or ""
    )
    if path:
        return service_account.Credentials.from_service_account_file(path, scopes=scopes)
    creds, _ = google.auth.default(scopes=scopes)
    return creds


def fetch_gsc_api(site: str, start: str, end: str) -> List[Dict[str, Any]]:
    """Fetch GSC search-analytics rows via the Search Console API."""
    try:
        from googleapiclient.discovery import build  # noqa: PLC0415
    except ImportError as exc:
        raise SystemExit(
            "--fetch gsc requires third-party deps; install scripts/requirements.txt "
            "(pip install google-api-python-client google-auth)"
        ) from exc
    creds = _load_api_credentials(GSC_SCOPES, "GSC_CREDENTIALS")
    service = build("webmasters", "v3", credentials=creds)
    body = {
        "startDate": start,
        "endDate": end,
        "dimensions": ["page", "query"],
        "rowLimit": 25000,
    }
    response = (
        service.searchanalytics().query(siteUrl=site, body=body).execute()
    )
    rows = []
    for row in response.get("rows", []):
        keys = row.get("keys", [])
        rows.append(
            {
                "keys": keys,
                "clicks": row.get("clicks", 0),
                "impressions": row.get("impressions", 0),
                "ctr": row.get("ctr", 0),
                "position": row.get("position", 0),
            }
        )
    return rows


def fetch_ga4_api(property_id: str, start: str, end: str) -> List[Dict[str, Any]]:
    """Fetch GA4 page-level metrics via the Google Analytics Data API."""
    try:
        from googleapiclient.discovery import build  # noqa: PLC0415
    except ImportError as exc:
        raise SystemExit(
            "--fetch ga4 requires third-party deps; install scripts/requirements.txt "
            "(pip install google-api-python-client google-auth)"
        ) from exc
    creds = _load_api_credentials(GA4_SCOPES, "GA4_CREDENTIALS")
    service = build("analyticsdata", "v1beta", credentials=creds)
    body = {
        "dateRanges": [{"startDate": start, "endDate": end}],
        "dimensions": [{"name": "pagePath"}],
        "metrics": [
            {"name": "sessions"},
            {"name": "totalUsers"},
            {"name": "keyEvents"},
        ],
    }
    response = (
        service.properties()
        .runReport(property=f"properties/{property_id}", body=body)
        .execute()
    )
    rows = []
    for row in response.get("rows", []):
        dims = row.get("dimensionValues", [])
        metrics = row.get("metricValues", [])
        rows.append(
            {
                "page": dims[0].get("value", "") if dims else "",
                "sessions": metrics[0].get("value", 0) if len(metrics) > 0 else 0,
                "users": metrics[1].get("value", 0) if len(metrics) > 1 else 0,
                "conversions": metrics[2].get("value", 0) if len(metrics) > 2 else 0,
            }
        )
    return rows


# ---------------------------------------------------------------------------
# wins / losses and priorities
# ---------------------------------------------------------------------------


def _period_deltas(
    current: List[Dict[str, Any]], prior: List[Dict[str, Any]], kind: str
) -> List[Tuple[str, float]]:
    """Click deltas between periods for a bucket list (pages or queries)."""
    cur = {row["key"]: row["clicks"] for row in current}
    prev = {row["key"]: row["clicks"] for row in prior}
    deltas = []
    for key in set(cur) | set(prev):
        deltas.append((f"{kind}: {key}", cur.get(key, 0.0) - prev.get(key, 0.0)))
    return deltas


def wins_losses(
    current: Dict[str, Any], prior: Dict[str, Any]
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """Compare page- and query-level clicks between periods -> wins/losses."""
    deltas: List[Tuple[str, float]] = []
    deltas += _period_deltas(current.get("top_pages", []), prior.get("top_pages", []), "page")
    deltas += _period_deltas(current.get("top_queries", []), prior.get("top_queries", []), "query")
    deltas.sort(key=lambda x: x[1], reverse=True)
    wins = [
        {"target": k, "delta_clicks": round(d, 1), "reason": "clicks up week-over-week"}
        for k, d in deltas[:WIN_LOSS_N]
        if d > 0
    ]
    losses = [
        {"target": k, "delta_clicks": round(d, 1), "reason": "clicks down week-over-week"}
        for k, d in reversed(deltas[-WIN_LOSS_N:])
        if d < 0
    ]
    return wins, losses


def load_optional_json(path: Optional[str]) -> Dict[str, Any]:
    if not path:
        return {}
    p = Path(path)
    if not p.exists():
        warn(f"optional file not found, skipping: {path}")
        return {}
    try:
        with open(p, encoding="utf-8") as fh:
            return json.load(fh)
    except json.JSONDecodeError as exc:
        warn(f"optional file is not valid JSON, skipping: {path} ({exc})")
        return {}


def build_priorities(
    gsc_current: Dict[str, Any],
    wins: List[Dict[str, Any]],
    losses: List[Dict[str, Any]],
    gap_data: Dict[str, Any],
    fix_data: Dict[str, Any],
) -> List[Dict[str, Any]]:
    """Build a concrete next-week priority list."""
    priorities: List[Dict[str, Any]] = []

    # 1) CTR opportunities: high impressions, low CTR, position 5-15 (pages + queries)
    candidates = []
    for kind, bucket in (("page", gsc_current.get("top_pages", [])), ("query", gsc_current.get("top_queries", []))):
        for row in bucket:
            pos = row["position"]
            ctr = (row["clicks"] / row["impressions"]) if row["impressions"] else 0.0
            if 5 <= pos <= 15 and row["impressions"] >= 500 and ctr < 0.02:
                candidates.append((kind, row["key"], pos, row["impressions"], ctr))
    for kind, key, pos, imp, ctr in candidates:
        label = key if kind == "query" else f"{key} (page)"
        priorities.append(
            {
                "priority": len(priorities) + 1,
                "action": f"Improve title/meta for {label} (CTR opportunity)",
                "target": label,
                "rationale": (
                    f"position {pos}, {imp:.0f} impressions, CTR {ctr:.3%} — "
                    f"a title/description rewrite can lift clicks"
                ),
                "source": "gsc",
            }
        )

    # 2) loss recovery: pages that lost clicks week-over-week
    for loss in losses[:3]:
        priorities.append(
            {
                "priority": len(priorities) + 1,
                "action": f"Refresh content on {loss['target']} (lost clicks)",
                "target": loss["target"],
                "rationale": f"lost {abs(loss['delta_clicks']):.0f} clicks vs prior week",
                "source": "gsc",
            }
        )

    # 3) content-gap tie-ins: gap keywords seen in our queries with impressions
    gaps = gap_data.get("gaps", []) if isinstance(gap_data, dict) else []
    query_map = {q["key"]: q for q in gsc_current["top_queries"]}
    for gap in gaps[:5]:
        kw = gap.get("keyword", "")
        if kw in query_map:
            q = query_map[kw]
            if q["clicks"] < 5 and q["impressions"] >= 100:
                priorities.append(
                    {
                        "priority": len(priorities) + 1,
                        "action": f"Publish content targeting \"{kw}\"",
                        "target": kw,
                        "rationale": (
                            f"content-gap opportunity (est. value {gap.get('estimated_value')}); "
                            f"we already get {q['impressions']:.0f} impressions at "
                            f"position {q['position']}"
                        ),
                        "source": "content-gap",
                    }
                )

    # 4) seo-audit tie-ins: high-severity fixes on pages that have traffic
    fixes = fix_data.get("fixes", []) if isinstance(fix_data, dict) else []
    traffic_pages = {p["key"] for p in gsc_current["top_pages"]}
    for fix in fixes[:5]:
        severity = fix.get("severity", "")
        location = str(fix.get("location", ""))
        if severity in ("critical", "high") and location in traffic_pages:
            priorities.append(
                {
                    "priority": len(priorities) + 1,
                    "action": f"Fix SEO issue on {location}: {fix.get('issue')}",
                    "target": location,
                    "rationale": f"seo-audit {severity}: {fix.get('fix', '')}",
                    "source": "seo-audit",
                }
            )

    priorities.sort(key=lambda p: p["priority"])
    for idx, item in enumerate(priorities, 1):
        item["priority"] = idx
    return priorities[:10]


# ---------------------------------------------------------------------------
# Markdown rendering
# ---------------------------------------------------------------------------


def _fmt_pct(value: Optional[float]) -> str:
    if value is None:
        return "n/a"
    sign = "+" if value > 0 else ""
    return f"{sign}{value}%"


def render_markdown(report: Dict[str, Any]) -> str:
    lines: List[str] = []
    period = report["period"]
    prior = report["prior_period"]
    gsc = report["gsc"]
    ga4 = report["ga4"]

    lines.append(f"# Weekly Growth Report / 周度增长报告")
    lines.append("")
    lines.append(
        f"Period / 报告周期: {period['start']} → {period['end']} "
        f"(vs {prior['start']} → {prior['end']})"
    )
    lines.append("")

    lines.append("## 1. Traffic Trends / 流量趋势")
    lines.append("")
    lines.append("| Metric / 指标 | This Week / 本周 | vs Prior / 环比 |")
    lines.append("|---|---|---|")
    lines.append(
        f"| GSC Clicks / 点击 | {gsc['totals']['clicks']:.0f} | "
        f"{_fmt_pct(gsc['delta'].get('clicks_pct'))} |"
    )
    lines.append(
        f"| GSC Impressions / 展示 | {gsc['totals']['impressions']:.0f} | "
        f"{_fmt_pct(gsc['delta'].get('impressions_pct'))} |"
    )
    lines.append(
        f"| GA4 Sessions / 会话 | {ga4['totals']['sessions']:.0f} | "
        f"{_fmt_pct(ga4['delta'].get('sessions_pct'))} |"
    )
    lines.append(
        f"| GA4 Users / 用户 | {ga4['totals']['users']:.0f} | "
        f"{_fmt_pct(ga4['delta'].get('users_pct'))} |"
    )
    lines.append(
        f"| GA4 Conversions / 转化 | {ga4['totals']['conversions']:.0f} | "
        f"{_fmt_pct(ga4['delta'].get('conversions_pct'))} |"
    )
    lines.append("")

    lines.append("## 2. Top Pages / 热门页面")
    lines.append("")
    lines.append("| Page / 页面 | Clicks / 点击 | Impressions / 展示 | Position / 排名 |")
    lines.append("|---|---|---|---|")
    for p in gsc["top_pages"]:
        lines.append(
            f"| {p['key']} | {p['clicks']:.0f} | {p['impressions']:.0f} | {p['position']} |"
        )
    lines.append("")

    lines.append("## 3. Top Keywords / 热门关键词")
    lines.append("")
    lines.append("| Query / 关键词 | Clicks / 点击 | Impressions / 展示 | Position / 排名 |")
    lines.append("|---|---|---|---|")
    for q in gsc["top_queries"]:
        lines.append(
            f"| {q['key']} | {q['clicks']:.0f} | {q['impressions']:.0f} | {q['position']} |"
        )
    lines.append("")

    lines.append("## 4. Wins & Losses / 赢与输（vs prior period）")
    lines.append("")
    lines.append("### Wins / 赢")
    lines.append("")
    for w in gsc["wins"]:
        lines.append(f"- {w['target']} — +{w['delta_clicks']:.0f} clicks")
    lines.append("")
    lines.append("### Losses / 输")
    lines.append("")
    for loss in gsc["losses"]:
        lines.append(f"- {loss['target']} — {loss['delta_clicks']:.0f} clicks")
    lines.append("")

    lines.append("## 5. Next-Week Priorities / 下周优先级")
    lines.append("")
    for item in report["priorities"]:
        lines.append(
            f"{item['priority']}. **{item['action']}** "
            f"[{item['source']}] — {item['rationale']}"
        )
    lines.append("")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------


def parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="gsc_ga4_report.py",
        description=(
            "Pull GSC + GA4 data and produce a weekly growth report "
            "(JSON to stdout, Markdown to --output)."
        ),
    )
    parser.add_argument("--gsc-csv", help="GSC export CSV (query/page/clicks/impressions/ctr/position)")
    parser.add_argument("--ga4-csv", help="GA4 export CSV (page/sessions/users/conversions)")
    parser.add_argument(
        "--gsc-prior-csv",
        help="GSC export CSV for the prior period (default: reuse --gsc-csv)",
    )
    parser.add_argument(
        "--ga4-prior-csv",
        help="GA4 export CSV for the prior period (default: reuse --ga4-csv)",
    )
    parser.add_argument(
        "--fetch",
        choices=["gsc", "ga4", "all"],
        help="fetch data via Google APIs instead of CSV (requires third-party deps)",
    )
    parser.add_argument("--site", help="GSC site URL for API mode (e.g. sc-domain:example.com)")
    parser.add_argument("--property", help="GA4 property id for API mode")
    parser.add_argument("--start", required=True, help="report start date YYYY-MM-DD")
    parser.add_argument("--end", required=True, help="report end date YYYY-MM-DD")
    parser.add_argument("--prior-start", help="prior period start (default: auto)")
    parser.add_argument("--prior-end", help="prior period end (default: auto)")
    parser.add_argument("--gap-file", help="outputs/content-gap/gap-opportunities.json")
    parser.add_argument("--fix-file", help="outputs/seo-audit/fix-plan.json")
    parser.add_argument("--output", default=DEFAULT_OUTPUT, help=f"Markdown output path (default: {DEFAULT_OUTPUT})")
    parser.add_argument("--output-json", help="optional JSON output path")
    return parser.parse_args(argv)


def load_source_data(
    args: argparse.Namespace,
    start: str,
    end: str,
    *,
    prior: bool = False,
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """Return (gsc_rows, ga4_rows) for one period.

    In CSV mode, `prior=True` switches to the *-prior-csv inputs; when those
    are absent, the current-period files are reused (deltas will be zero).
    """
    gsc_rows: List[Dict[str, Any]] = []
    ga4_rows: List[Dict[str, Any]] = []

    gsc_csv = args.gsc_prior_csv if prior else args.gsc_csv
    ga4_csv = args.ga4_prior_csv if prior else args.ga4_csv
    if prior and not gsc_csv and not ga4_csv:
        warn(
            "prior-period CSVs not provided (--gsc-prior-csv/--ga4-prior-csv); "
            "reusing current files, week-over-week deltas will be zero"
        )
        gsc_csv = args.gsc_csv
        ga4_csv = args.ga4_csv
    elif prior:
        gsc_csv = gsc_csv or args.gsc_csv
        ga4_csv = ga4_csv or args.ga4_csv

    fetch_mode = args.fetch if not prior else None
    if fetch_mode in ("gsc", "all"):
        site = args.site or os.environ.get("GSC_SITE")
        if not site:
            raise SystemExit("--fetch gsc requires --site or GSC_SITE env var")
        gsc_rows = fetch_gsc_api(site, start, end)
    elif gsc_csv:
        gsc_rows = parse_gsc_rows(read_rows(gsc_csv))

    if fetch_mode in ("ga4", "all"):
        prop = args.property or os.environ.get("GA4_PROPERTY_ID")
        if not prop:
            raise SystemExit("--fetch ga4 requires --property or GA4_PROPERTY_ID env var")
        ga4_rows = fetch_ga4_api(str(prop), start, end)
    elif ga4_csv:
        ga4_rows = parse_ga4_rows(read_rows(ga4_csv))

    if not gsc_rows:
        warn("no GSC data loaded — GSC section will be empty")
    if not ga4_rows:
        warn("no GA4 data loaded — GA4 section will be empty")
    return gsc_rows, ga4_rows


def main(argv: Optional[List[str]] = None) -> int:
    args = parse_args(argv)

    start = parse_date(args.start)
    end = parse_date(args.end)
    if end < start:
        raise SystemExit("--end must not be before --start")

    if args.prior_start and args.prior_end:
        prior_start = parse_date(args.prior_start)
        prior_end = parse_date(args.prior_end)
    else:
        length = (end - start).days + 1
        prior_end = start - timedelta(days=1)
        prior_start = prior_end - timedelta(days=length - 1)

    gsc_rows, ga4_rows = load_source_data(args, args.start, args.end)
    prior_gsc_rows, prior_ga4_rows = load_source_data(
        args, prior_start.isoformat(), prior_end.isoformat(), prior=True
    )

    gsc_current = summarize_gsc(gsc_rows)
    gsc_prior = summarize_gsc(prior_gsc_rows)
    ga4_current = summarize_ga4(ga4_rows)
    ga4_prior = summarize_ga4(prior_ga4_rows)

    wins, losses = wins_losses(gsc_current, gsc_prior)

    gap_data = load_optional_json(args.gap_file)
    fix_data = load_optional_json(args.fix_file)
    priorities = build_priorities(gsc_current, wins, losses, gap_data, fix_data)

    report: Dict[str, Any] = {
        "skill": "weekly-growth-report",
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "period": {"start": start.isoformat(), "end": end.isoformat()},
        "prior_period": {"start": prior_start.isoformat(), "end": prior_end.isoformat()},
        "gsc": {
            "totals": gsc_current["totals"],
            "delta": {
                "clicks_pct": pct(gsc_current["totals"]["clicks"], gsc_prior["totals"]["clicks"]),
                "impressions_pct": pct(gsc_current["totals"]["impressions"], gsc_prior["totals"]["impressions"]),
            },
            "top_pages": gsc_current["top_pages"],
            "top_queries": gsc_current["top_queries"],
            "wins": wins,
            "losses": losses,
        },
        "ga4": {
            "totals": ga4_current["totals"],
            "delta": {
                "sessions_pct": pct(ga4_current["totals"]["sessions"], ga4_prior["totals"]["sessions"]),
                "users_pct": pct(ga4_current["totals"]["users"], ga4_prior["totals"]["users"]),
                "conversions_pct": pct(ga4_current["totals"]["conversions"], ga4_prior["totals"]["conversions"]),
            },
            "top_pages": ga4_current["top_pages"],
        },
        "priorities": priorities,
    }

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(render_markdown(report), encoding="utf-8")

    if args.output_json:
        json_path = Path(args.output_json)
        json_path.parent.mkdir(parents=True, exist_ok=True)
        json_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")

    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
