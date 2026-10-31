#!/usr/bin/env python3
"""Build a SOR_SCOPE_PATH JSON file from a simple CSV.

Districts know their phonics program as a list of lessons or units. This
script lets a literacy lead type that list into a spreadsheet and turns it
into the JSON the decodability engine reads.

CSV columns (header required):

    grade,unit,title,patterns,heart_words
    K,1,"m, s, t, p, short a","m; s; t; p; a","the; a; I"
    1,2,"silent-e a_e, i_e","a_e; i_e","who"

- grade: K, 1, 2 or 3
- unit:  1, 2, 3 ... in teaching order within the grade (lessons can be grouped)
- patterns: semicolon-separated. Each entry may be a GPC id from
  src/engine/gpc.py (e.g. short_a, vce_a, vt_igh) or a spelling a teacher
  would write: a single vowel letter means its short sound; "a_e" means
  silent-e; "-ed", "-es" are suffixes; "open syllable", "schwa",
  "y as vowel", "doubled consonants" are also accepted.
- heart_words: semicolon-separated words taught as heart words in that unit.

Usage:
    python3 scripts/build_scope.py my_program.csv -o my_program_scope.json
    python3 scripts/build_scope.py --export-default -o template.csv
    SOR_SCOPE_PATH=my_program_scope.json python3 webapp.py
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.engine.gpc import ALL_GPC_IDS, CATALOG  # noqa: E402
from src.engine.scope_sequence import DEFAULT_SEQUENCE, GRADE_ORDER, normalize_grade  # noqa: E402

ALIASES: dict[str, str] = {
    "a": "short_a", "e": "short_e", "i": "short_i", "o": "short_o", "u": "short_u",
    "short a": "short_a", "short e": "short_e", "short i": "short_i", "short o": "short_o", "short u": "short_u",
    "a_e": "vce_a", "i_e": "vce_i", "o_e": "vce_o", "u_e": "vce_u", "e_e": "vce_e",
    "-ed": "suffix_ed", "ed": "suffix_ed", "-es": "suffix_es", "es": "suffix_es",
    "-s": "s", "s as z": "s_z", "s /z/": "s_z",
    "open syllable": "open_syllable", "open syllables": "open_syllable",
    "schwa": "schwa",
    "y as vowel": "y_vowel", "y as a vowel": "y_vowel", "vowel y": "y_vowel",
    "doubled consonants": "double_consonant", "double consonants": "double_consonant",
    "flss": "floss", "floss": "floss", "ff": "floss", "ll": "floss", "ss": "floss", "zz": "floss",
    "ea (short)": "ea_short", "short ea": "ea_short",
    "ou (oo)": "ou_oo", "ie (long e)": "ie_ee",
    "c (soft)": "soft_c", "soft c": "soft_c", "g (soft)": "soft_g", "soft g": "soft_g",
    "-le": "c_le", "consonant-le": "c_le", "le": "c_le",
    "-tion": "suffix_tion", "tion": "suffix_tion", "-sion": "suffix_tion", "sion": "suffix_tion",
    "-ture": "suffix_ture", "ture": "suffix_ture",
    "ve": "final_ve", "-ve": "final_ve", "se": "final_se",
}


def resolve_pattern(entry: str) -> tuple[list[str], str | None]:
    """Return (gpc_ids, warning) for one CSV pattern entry."""
    key = entry.strip().lower()
    if not key:
        return [], None
    if key in ALL_GPC_IDS:
        return [key], None
    if key in ALIASES:
        return [ALIASES[key]], None
    ids = list(dict.fromkeys(g.id for g in CATALOG if g.grapheme == key))
    if len(ids) == 1:
        return ids, None
    if len(ids) > 1:
        return [ids[0]], f"'{entry}' can mean {', '.join(ids)}; used {ids[0]}. Write the GPC id to choose another."
    raise ValueError(f"Unknown pattern '{entry}'. Use a GPC id from src/engine/gpc.py or a listed alias.")


def build(csv_path: Path) -> tuple[dict[str, list[dict]], list[str]]:
    sequence: dict[str, list[dict]] = {}
    warnings: list[str] = []
    with csv_path.open(newline="", encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f))
    required = {"grade", "unit", "title", "patterns", "heart_words"}
    if not rows or not required <= set(rows[0].keys()):
        raise ValueError(f"CSV must have columns: {', '.join(sorted(required))}")

    keyed: dict[str, list[tuple[int, dict]]] = {}
    for n, row in enumerate(rows, start=2):
        grade = normalize_grade(row["grade"])
        if grade is None:
            raise ValueError(f"Row {n}: grade '{row['grade']}' must be K, 1, 2 or 3")
        try:
            unit = int(str(row["unit"]).strip())
        except ValueError as exc:
            raise ValueError(f"Row {n}: unit '{row['unit']}' must be a number") from exc
        gpcs: list[str] = []
        for entry in str(row["patterns"]).split(";"):
            try:
                ids, warn = resolve_pattern(entry)
            except ValueError as exc:
                raise ValueError(f"Row {n}: {exc}") from exc
            gpcs.extend(ids)
            if warn:
                warnings.append(f"Row {n}: {warn}")
        hearts = [w.strip() for w in str(row["heart_words"]).split(";") if w.strip()]
        keyed.setdefault(grade, []).append((unit, {
            "title": row["title"].strip(),
            "gpcs": list(dict.fromkeys(gpcs)),
            "heart_words": hearts,
        }))

    for grade in GRADE_ORDER:
        units = sorted(keyed.get(grade, []), key=lambda t: t[0])
        numbers = [u for u, _ in units]
        if numbers and numbers != list(range(1, len(numbers) + 1)):
            warnings.append(f"Grade {grade}: units are {numbers}; they will be renumbered 1..{len(numbers)} in order.")
        if units:
            sequence[grade] = [u for _, u in units]

    taught: set[str] = set()
    for grade in GRADE_ORDER:
        for unit in sequence.get(grade, []):
            dup = taught & set(unit["gpcs"])
            if dup:
                warnings.append(f"Grade {grade} '{unit['title']}': already taught earlier: {', '.join(sorted(dup))}")
            taught |= set(unit["gpcs"])
    return sequence, warnings


def export_default(out: Path) -> None:
    with out.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["grade", "unit", "title", "patterns", "heart_words"])
        for grade in GRADE_ORDER:
            for i, unit in enumerate(DEFAULT_SEQUENCE.get(grade, []), start=1):
                w.writerow([grade, i, unit["title"], "; ".join(unit["gpcs"]), "; ".join(unit["heart_words"])])


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("csv", nargs="?", type=Path, help="Program scope & sequence CSV")
    ap.add_argument("-o", "--output", type=Path, required=True)
    ap.add_argument("--export-default", action="store_true", help="Write the default sequence as a CSV template")
    args = ap.parse_args()

    if args.export_default:
        export_default(args.output)
        print(f"Wrote template to {args.output}")
        return 0
    if not args.csv:
        ap.error("csv is required unless --export-default is used")
    try:
        sequence, warnings = build(args.csv)
    except ValueError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    args.output.write_text(json.dumps(sequence, indent=2) + "\n")
    for warn in warnings:
        print(f"Warning: {warn}", file=sys.stderr)
    total = sum(len(v) for v in sequence.values())
    print(f"Wrote {total} units across grades {', '.join(sequence)} to {args.output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
