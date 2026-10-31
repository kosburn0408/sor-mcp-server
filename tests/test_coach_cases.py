"""Regression cases from literacy coach reviews (scripts/coach_review.py).

Each case is a word the coach classified differently from the engine. Cases
recorded against a custom scope only run when SOR_SCOPE_PATH matches. Cases
marked xfail stay visible until the engine is fixed; remove the marker when
the case passes.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

from src.engine.decoder import analyze_word
from src.engine.scope_sequence import resolve_scope

CASES = json.loads((Path(__file__).parent / "fixtures" / "coach_cases.json").read_text() or "[]")


def _applies(case: dict) -> bool:
    src = case.get("scope_source", "default")
    return src == os.environ.get("SOR_SCOPE_PATH", "default")


@pytest.mark.parametrize("case", CASES or [None], ids=[f"{c['word']}-{c['grade']}-{c['unit']}" for c in CASES] or ["none"])
def test_coach_case(case: dict | None) -> None:
    if case is None:
        pytest.skip("No coach review cases recorded yet")
    if not _applies(case):
        pytest.skip(f"Case recorded against scope {case.get('scope_source')}")
    if case.get("xfail"):
        pytest.xfail(case.get("notes") or "known disagreement")
    scope = resolve_scope(case["grade"], case["unit"])
    got = analyze_word(case["word"], scope["taught_gpcs"], scope["heart_words"])["status"]
    assert got == case["expected_status"], case.get("notes", "")
