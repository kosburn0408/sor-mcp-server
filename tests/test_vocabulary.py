"""Tests for frequency-based vocabulary tier estimates."""

from __future__ import annotations

from src.tools.vocabulary import classify_text, estimate_tier


def _words(result: dict, key: str) -> list[str]:
    return [w["word"] for w in result[key]]


def test_common_academic_words_are_tier2_candidates() -> None:
    r = classify_text("The fox ran quickly across the enormous meadow to investigate the experiment.")
    t2 = _words(r, "tier_2_words")
    assert "enormous" in t2 and "investigate" in t2
    assert "quickly" in _words(r, "tier_1_words") and "across" in _words(r, "tier_1_words")
    # Length no longer decides the tier.
    assert "quickly" not in _words(r, "tier_3_words")


def test_rare_technical_words_are_tier3() -> None:
    r = classify_text("Each phoneme maps to a grapheme.")
    assert {"phoneme", "grapheme"} <= set(_words(r, "tier_3_words"))


def test_names_are_not_classified() -> None:
    r = classify_text("The dog ran to Keisha and Mateo.")
    assert {"Keisha", "Mateo"} <= {n["word"] for n in r["names"]}


def test_tier2_ordered_most_common_first() -> None:
    r = classify_text("Reluctant and enormous and peculiar.")
    zs = [w["zipf"] for w in r["tier_2_words"]]
    assert zs == sorted(zs, reverse=True)


def test_corpus_and_lists_override_frequency() -> None:
    assert estimate_tier("describe")["source"] == "tier corpus"
    assert estimate_tier("said")["tier"] == 1


def test_rare_capitalized_sentence_start_treated_as_name() -> None:
    r = classify_text("The fox ran. Keisha was reluctant.")
    assert "Keisha" in {n["word"] for n in r["names"]}
    assert "keisha" not in [w["word"] for w in r["tier_3_words"]]
