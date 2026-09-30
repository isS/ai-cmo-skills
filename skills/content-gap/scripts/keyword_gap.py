#!/usr/bin/env python3
"""keyword_gap.py — Find content/keyword gaps between our site and competitors.

Compares our keyword list against one or more competitor keyword lists and
outputs keywords the competitors have but we lack, ranked by estimated value.
Each gap is flagged with its source(s) and a suggested content angle.

Inputs: JSON keyword-list files or GSC CSV exports (see SKILL.md for schemas).
Output: ranked gap opportunities as JSON on stdout (optionally also to a file).

Requirements: Python 3.10+ standard library only — no third-party deps.
Secrets: none required (pure local file comparison). If a future version calls
an external keyword API, credentials MUST be read from environment variables
(e.g. KEYWORD_API_TOKEN) and never hardcoded.
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

DEFAULT_TOP = 50

KEYWORD_KEYS = ("keyword", "query", "term")
VOLUME_KEYS = ("volume", "search_volume", "vol")
DIFFICULTY_KEYS = ("difficulty", "kd", "difficulty_score")


def normalize(keyword: Any) -> str:
    """Normalize a keyword for exact matching (lowercase, collapse whitespace).

    Prevents false positives: variants such as "AI CMO  Tool" and "ai cmo tool"
    are treated as the same already-covered term.
    """
    if keyword is None:
        return ""
    return " ".join(str(keyword).strip().lower().split())


def pick_number(row: Dict[str, Any], keys: Iterable[str]) -> float:
    """Return the first numeric value among `keys`, else 0.0."""
    for key in keys:
        value = row.get(key)
        if value is None:
            continue
        try:
            return float(value)
        except (TypeError, ValueError):
            continue
    return 0.0


def load_keyword_file(path: str) -> Tuple[str, Dict[str, Dict[str, Any]]]:
    """Load keyword records from a JSON or CSV file.

    Returns (source_name, {normalized_keyword: record}).
    """
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"keyword file not found: {path}")
    if p.suffix.lower() == ".csv":
        return _load_csv(p)
    if p.suffix.lower() == ".json":
        return _load_json(p)
    raise ValueError(f"unsupported file type (use .json or .csv): {path}")


def _load_json(p: Path) -> Tuple[str, Dict[str, Dict[str, Any]]]:
    with open(p, encoding="utf-8") as fh:
        data = json.load(fh)

    if isinstance(data, list):
        meta, items = {}, data
    elif isinstance(data, dict):
        meta = data
        items = data.get("keywords") or data.get("queries") or []
    else:
        raise ValueError(f"unexpected JSON structure in {p}")

    source = str(meta.get("site") or meta.get("competitor") or meta.get("name") or p.stem)
    records: Dict[str, Dict[str, Any]] = {}

    for item in items:
        if isinstance(item, str):
            item = {"keyword": item}
        if not isinstance(item, dict):
            continue
        key = next((item[k] for k in KEYWORD_KEYS if item.get(k)), None)
        norm = normalize(key)
        if not norm:
            continue
        records[norm] = {
            "keyword": str(key),
            "volume": pick_number(item, VOLUME_KEYS),
            "difficulty": pick_number(item, DIFFICULTY_KEYS),
            "clicks": pick_number(item, ("clicks",)),
            "impressions": pick_number(item, ("impressions",)),
            "position": pick_number(item, ("position", "pos")),
        }
    return source, records


def _load_csv(p: Path) -> Tuple[str, Dict[str, Dict[str, Any]]]:
    # utf-8-sig tolerates the BOM that GSC exports usually include.
    with open(p, encoding="utf-8-sig", newline="") as fh:
        reader = csv.DictReader(fh)
        records: Dict[str, Dict[str, Any]] = {}
        for row in reader:
            key = row.get("query") or row.get("keyword") or row.get("term")
            norm = normalize(key)
            if not norm:
                continue
            records[norm] = {
                "keyword": str(key),
                "volume": 0.0,  # GSC exports carry no volume; value comes from clicks/impressions
                "difficulty": 0.0,
                "clicks": pick_number(row, ("clicks",)),
                "impressions": pick_number(row, ("impressions",)),
                "position": pick_number(row, ("position", "pos")),
            }
    return p.stem, records


def estimate_value(record: Dict[str, Any]) -> float:
    """Score a gap keyword by estimated value (higher = more worthwhile).

    volume * (1 - difficulty/100) + clicks * 10 + impressions * 0.05
    """
    volume = record.get("volume") or 0.0
    difficulty = min(max(record.get("difficulty") or 0.0, 0.0), 100.0)
    clicks = record.get("clicks") or 0.0
    impressions = record.get("impressions") or 0.0
    return round(volume * (1.0 - difficulty / 100.0) + clicks * 10.0 + impressions * 0.05, 2)


def suggest_angle(keyword: str, record: Dict[str, Any]) -> str:
    """Suggest a content angle for a gap keyword via simple heuristics."""
    kw = str(keyword).strip().lower()
    volume = record.get("volume") or 0.0
    note = f" (est. volume {volume:g})" if volume else ""

    if " vs " in kw or kw.endswith(" vs"):
        return f'Comparison page targeting "{keyword}"{note}'
    if kw.startswith(("how to", "how do", "how can")):
        return f'How-to guide targeting "{keyword}"{note}'
    if kw.startswith(("what", "why", "which", "when", "where", "who", "is ", "are ", "can ", "does ")):
        return f'FAQ / answer post targeting "{keyword}"{note}'
    if "best" in kw or "top " in kw:
        return f'Listicle / roundup targeting "{keyword}"{note}'
    if "review" in kw:
        return f'Review post targeting "{keyword}"{note}'
    if any(t in kw for t in ("pricing", "price", "cost")):
        return f'Pricing page targeting "{keyword}"{note}'
    if any(t in kw for t in ("template", "checklist", "example")):
        return f'Template / resource post targeting "{keyword}"{note}'
    if any(t in kw for t in ("tutorial", "guide", "setup")):
        return f'Step-by-step tutorial targeting "{keyword}"{note}'
    return f'Pillar blog post targeting "{keyword}"{note}'


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="keyword_gap.py",
        description=(
            "Find content/keyword gaps between our site and competitors. "
            "Outputs gap keywords (competitor has, we lack) sorted by estimated value."
        ),
    )
    parser.add_argument("our_file", help="our keyword list (JSON) or GSC export (CSV)")
    parser.add_argument(
        "competitor_files",
        nargs="+",
        help="one or more competitor keyword files (JSON or CSV)",
    )
    parser.add_argument(
        "-o",
        "--output",
        help="write results to this JSON file (default: stdout only)",
    )
    parser.add_argument(
        "-n",
        "--top",
        type=int,
        default=DEFAULT_TOP,
        help=f"limit to top N gaps, 0 = unlimited (default: {DEFAULT_TOP})",
    )
    parser.add_argument(
        "--min-volume",
        type=float,
        default=0.0,
        help="only include gaps with search volume >= N (default: 0)",
    )
    return parser


def main(argv: Optional[List[str]] = None) -> int:
    args = build_arg_parser().parse_args(argv)

    try:
        our_source, our_records = load_keyword_file(args.our_file)
        gaps: Dict[str, Dict[str, Any]] = {}
        competitor_files: List[Dict[str, str]] = []

        for comp_file in args.competitor_files:
            comp_source, comp_records = load_keyword_file(comp_file)
            competitor_files.append({"file": comp_file, "source": comp_source})
            for norm, record in comp_records.items():
                if norm in our_records:
                    continue  # already covered — avoids false positives
                entry = gaps.setdefault(
                    norm,
                    {
                        "keyword": record["keyword"],
                        "volume": 0.0,
                        "difficulty": 0.0,
                        "clicks": 0.0,
                        "impressions": 0.0,
                        "sources": [],
                    },
                )
                entry["volume"] = max(entry["volume"], record.get("volume") or 0.0)
                entry["difficulty"] = max(entry["difficulty"], record.get("difficulty") or 0.0)
                entry["clicks"] = max(entry["clicks"], record.get("clicks") or 0.0)
                entry["impressions"] = max(entry["impressions"], record.get("impressions") or 0.0)
                if comp_source not in entry["sources"]:
                    entry["sources"].append(comp_source)

        results = []
        for entry in gaps.values():
            if entry["volume"] < args.min_volume:
                continue
            entry["estimated_value"] = estimate_value(entry)
            results.append(entry)

        results.sort(key=lambda e: (-e["estimated_value"], -e["volume"], e["keyword"]))

        if args.top and args.top > 0:
            results = results[: args.top]

        output = {
            "skill": "content-gap",
            "our_source": our_source,
            "our_keywords_analyzed": len(our_records),
            "competitor_files": competitor_files,
            "gap_count": len(results),
            "gaps": [
                {
                    "keyword": e["keyword"],
                    "volume": e["volume"],
                    "difficulty": e["difficulty"],
                    "estimated_value": e["estimated_value"],
                    "sources": e["sources"],
                    "suggested_angle": suggest_angle(e["keyword"], e),
                }
                for e in results
            ],
        }

        payload = json.dumps(output, ensure_ascii=False, indent=2)

        if args.output:
            out_path = Path(args.output)
            out_path.parent.mkdir(parents=True, exist_ok=True)
            out_path.write_text(payload + "\n", encoding="utf-8")

        print(payload)
        return 0
    except Exception as exc:  # top-level guard: stdout must always be valid JSON
        print(json.dumps({"skill": "content-gap", "error": str(exc)}, ensure_ascii=False, indent=2))
        print(f"keyword_gap.py: error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
