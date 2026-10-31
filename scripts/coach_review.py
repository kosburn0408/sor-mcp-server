#!/usr/bin/env python3
"""Literacy coach review: check the decodability engine against an expert.

Step 1 - make a review sheet from real passages:

    python3 scripts/coach_review.py prepare passages.csv -o review.csv

  passages.csv columns: passage_id,grade,unit,text
  review.csv has one row per distinct word per passage, with the tool's
  verdict and empty columns for the coach.

Step 2 - the coach opens review.csv in Google Sheets or Excel and, for each
word, fills in:

  coach_agrees   Y or N
  coach_status   when N: decodable, heart_word, not_yet_decodable or irregular
  coach_notes    optional (e.g. "taught as heart word in lesson 22")

Step 3 - turn the coach's answers into a report and regression tests:

    python3 scripts/coach_review.py ingest review.csv --cases tests/fixtures/coach_cases.json

  Prints agreement rates by status and appends every disagreement to the
  cases file. tests/test_coach_cases.py then checks each case against the
  engine, so fixes can be verified and nothing regresses.

Set SOR_SCOPE_PATH to the district's scope & sequence before both steps, so
the review is against the program the coach actually teaches.
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.tools.decodability import check_decodability  # noqa: E402

STATUSES = ("decodable", "heart_word", "not_yet_decodable", "irregular", "not_in_dictionary")
REVIEW_COLUMNS = [
    "passage_id", "grade", "unit", "word", "tool_status", "tool_breakdown", "tool_missing_patterns",
    "coach_agrees", "coach_status", "coach_notes",
]


def prepare(passages: Path, out: Path) -> int:
    rows_out = 0
    with passages.open(newline="", encoding="utf-8-sig") as f, out.open("w", newline="", encoding="utf-8") as g:
        reader = csv.DictReader(f)
        missing = {"passage_id", "grade", "unit", "text"} - set(reader.fieldnames or [])
        if missing:
            raise ValueError(f"passages CSV is missing columns: {', '.join(sorted(missing))}")
        writer = csv.DictWriter(g, fieldnames=REVIEW_COLUMNS)
        writer.writeheader()
        for row in reader:
            result = check_decodability(row["text"], row["grade"], unit=row["unit"])
            if result.get("error_code"):
                raise ValueError(f"Passage {row['passage_id']}: {result.get('error_message', result['error_code'])}")
            for w in result["words"]:
                writer.writerow({
                    "passage_id": row["passage_id"],
                    "grade": result["grade_level"],
                    "unit": result["unit"],
                    "word": w["word"].lower(),
                    "tool_status": w["status"],
                    "tool_breakdown": w["breakdown"],
                    "tool_missing_patterns": "; ".join(w["missing_patterns"]),
                    "coach_agrees": "",
                    "coach_status": "",
                    "coach_notes": "",
                })
                rows_out += 1
    return rows_out


def ingest(review: Path, cases_path: Path) -> dict:
    with review.open(newline="", encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f))
    reviewed = [r for r in rows if r.get("coach_agrees", "").strip()]
    by_status: dict[str, Counter] = {}
    new_cases: list[dict] = []
    problems: list[str] = []

    for r in reviewed:
        agrees = r["coach_agrees"].strip().upper().startswith("Y")
        by_status.setdefault(r["tool_status"], Counter())["agree" if agrees else "disagree"] += 1
        if agrees:
            continue
        expected = r.get("coach_status", "").strip().lower()
        if expected not in STATUSES:
            problems.append(f"{r['passage_id']}/{r['word']}: coach_status '{expected}' is not one of {', '.join(STATUSES)}")
            continue
        new_cases.append({
            "word": r["word"],
            "grade": r["grade"],
            "unit": int(r["unit"]),
            "expected_status": expected,
            "tool_status_at_review": r["tool_status"],
            "notes": r.get("coach_notes", "").strip(),
            "scope_source": os.environ.get("SOR_SCOPE_PATH", "default"),
        })

    existing: list[dict] = []
    if cases_path.exists():
        existing = json.loads(cases_path.read_text() or "[]")
    seen = {(c["word"], c["grade"], c["unit"], c.get("scope_source")) for c in existing}
    added = [c for c in new_cases if (c["word"], c["grade"], c["unit"], c["scope_source"]) not in seen]
    cases_path.parent.mkdir(parents=True, exist_ok=True)
    cases_path.write_text(json.dumps(existing + added, indent=2) + "\n")

    total = sum(sum(c.values()) for c in by_status.values())
    agree = sum(c["agree"] for c in by_status.values())
    return {
        "rows": len(rows),
        "reviewed": total,
        "agreement_pct": round(100 * agree / total, 1) if total else None,
        "by_tool_status": {
            s: {"agree": c["agree"], "disagree": c["disagree"],
                "agreement_pct": round(100 * c["agree"] / (c["agree"] + c["disagree"]), 1)}
            for s, c in sorted(by_status.items())
        },
        "cases_added": len(added),
        "problems": problems,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("prepare", help="Make a review sheet from passages")
    p.add_argument("passages", type=Path)
    p.add_argument("-o", "--output", type=Path, required=True)
    i = sub.add_parser("ingest", help="Summarize a completed review and record disagreements as test cases")
    i.add_argument("review", type=Path)
    i.add_argument("--cases", type=Path, default=Path("tests/fixtures/coach_cases.json"))
    args = ap.parse_args()

    try:
        if args.cmd == "prepare":
            n = prepare(args.passages, args.output)
            print(f"Wrote {n} words to review in {args.output}")
        else:
            report = ingest(args.review, args.cases)
            print(json.dumps(report, indent=2))
    except ValueError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
