"""Tests for the Simple View screening profile."""

from __future__ import annotations

import pytest

from src.tools.diagnostics import evaluate_simple_view
from src.tools.remediation import DEFICIT_TO_REMEDIATION, REMEDIATION_TABLE


def test_profiles_use_screening_labels_not_diagnoses() -> None:
    cases = {
        (0.8, 0.8): "typical",
        (0.4, 0.8): "decoding_weak",
        (0.8, 0.4): "language_comprehension_weak",
        (0.4, 0.4): "dual_weak",
    }
    for (d, lc), expected in cases.items():
        out = evaluate_simple_view(d, lc, "1st")
        assert out["diagnostic"]["reading_profile"] == expected
        assert "not a diagnosis" in out["diagnostic"]["caveat"]
        assert "dyslexia" not in out["diagnostic"]["reading_profile"]


def test_threshold_is_configurable() -> None:
    assert evaluate_simple_view(0.7, 0.9, threshold=0.8)["diagnostic"]["reading_profile"] == "decoding_weak"
    assert evaluate_simple_view(0.7, 0.9, threshold=0.6)["diagnostic"]["reading_profile"] == "typical"
    assert "error_code" in evaluate_simple_view(0.5, 0.5, threshold=0.0)


def test_dual_weak_advice_builds_language_in_parallel() -> None:
    steps = evaluate_simple_view(0.3, 0.3)["next_steps"]
    assert "same time" in steps
    assert "wait" in steps


def test_every_suggested_deficit_code_has_a_card() -> None:
    for d in (0.1, 0.4, 0.55):
        out = evaluate_simple_view(d, 0.9)
        assert out["diagnostic"]["unavailable_codes"] == []
        assert len(out["remediations"]) == len(out["diagnostic"]["deficit_codes"])


def test_all_mapped_remediation_codes_resolve() -> None:
    for target in DEFICIT_TO_REMEDIATION.values():
        assert target in REMEDIATION_TABLE


def test_invalid_scores_are_rejected() -> None:
    assert evaluate_simple_view(1.5, 0.5)["error_code"] == "ERR_INVALID_SCORE_RANGE"
