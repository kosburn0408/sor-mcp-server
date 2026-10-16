"""Tests for the cumulative grapheme scope engine and the decodability checker built on it."""

from __future__ import annotations

import pytest

from src.tools.decodability import MANDATORY_HEART_WORDS, check_decodability
from src.tools.scope_engine import analyze_word, scope_for


def status(word: str, grade: str, unit: int | None = None) -> str:
    return analyze_word(word, scope_for(grade, unit))["status"]


@pytest.mark.parametrize("word", ["night", "knight", "through", "thought", "ocean", "about"])
def test_irregular_or_untaught_spellings_are_off_scope_in_grade_1(word: str) -> None:
    assert status(word, "1") == "off_scope"


def test_igh_and_kn_become_decodable_once_taught() -> None:
    assert status("night", "2") == "decodable"
    assert status("knight", "2") == "decodable"


@pytest.mark.parametrize("word", ["cat", "chat", "ship", "cake", "jumped", "jumping", "hopping", "boxes"])
def test_regular_grade_1_words_are_decodable(word: str) -> None:
    assert status(word, "1") == "decodable"


def test_unit_gating_limits_graphemes_taught_so_far() -> None:
    # Kindergarten unit 1 teaches only s a t p i n, so "cat" needs a letter not yet taught.
    assert status("sat", "K", 1) == "decodable"
    assert status("cat", "K", 1) == "off_scope"
    assert status("cat", "K") == "decodable"


def test_vowel_teams_need_to_be_taught() -> None:
    assert status("rain", "1") == "off_scope"
    assert status("rain", "2") == "decodable"


def test_multisyllable_words_wait_for_the_pattern() -> None:
    assert status("rabbit", "1") == "off_scope"
    assert status("rabbit", "2") == "decodable"


def test_compounds_require_known_halves() -> None:
    assert status("sunset", "1") == "decodable"
    assert status("through", "1") == "off_scope"


def test_regular_words_are_not_heart_words() -> None:
    for word in ("on", "can", "then", "him", "just", "let"):
        assert word not in MANDATORY_HEART_WORDS
    for word in ("the", "said", "was"):
        assert word in MANDATORY_HEART_WORDS


def test_heart_words_are_reported_separately() -> None:
    result = check_decodability("The cat said it was fun.", "K")
    assert "said" in result["heart_words"]
    assert result["regular_decodable_pct"] < result["decodable_pct"]


def test_grade_1_text_with_untaught_words_is_not_independent() -> None:
    result = check_decodability("Through the night the knight thought about the ocean.", "1")
    assert result["instructional_level"] == "frustration"
    assert any(f["type"] == "high_guessing_risk" for f in result["cueing_flags"])


def test_guessing_prompts_and_predictable_frames_are_flagged() -> None:
    text = "Look at the picture and guess the word. I see a dog. I see a cat. I see a hen."
    flags = {f["type"] for f in check_decodability(text, "K")["cueing_flags"]}
    assert "guessing_prompt" in flags
    assert "repeated_sentence_frame" in flags


def test_substitutions_are_only_offered_when_decodable_at_that_scope() -> None:
    kindergarten = check_decodability("The huge dog saw a beautiful hen.", "K")
    # "big" is a taught CVC word, so it is a valid swap for "huge".
    assert kindergarten["substitutions"].get("huge") == ["big"]
    # "fine" needs the CVCe pattern, which kindergarten has not taught, so it is not suggested.
    assert "beautiful" in kindergarten["off_scope_words"]
    assert "beautiful" not in kindergarten["substitutions"]


def test_spelling_based_engine_documents_its_blind_spot() -> None:
    result = check_decodability("The cat sat.", "K")
    assert any("pronunciation" in item.lower() for item in result["limitations"])


def test_grade_4_and_5_are_marked_as_not_modeled() -> None:
    result = check_decodability("The quick brown fox jumps.", "4")
    assert result["warnings"]


def test_word_analysis_is_returned_per_unique_word() -> None:
    result = check_decodability("cat cat dog", "K")
    assert [w["word"] for w in result["word_analysis"]] == ["cat", "dog"]
