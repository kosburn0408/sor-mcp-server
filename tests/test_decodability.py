"""Tests for the scope-aware decodability engine and anti-cueing detector.

Includes regression cases that the previous regex-based checker scored as
100% decodable even though they are far beyond the grade's phonics scope.
"""

from __future__ import annotations

import pytest

from src.engine.cueing import detect_cueing
from src.engine.decoder import analyze_word
from src.engine.gpc import ALL_GPC_IDS
from src.engine.scope_sequence import resolve_scope
from src.tools.decodability import check_decodability, verify_decodable_text


def taught(grade: str, unit: int) -> list[str]:
    return resolve_scope(grade, unit)["taught_gpcs"]


class TestRegressionsFromRegexChecker:
    """Passages the old checker wrongly passed as 100% decodable."""

    def test_grade2_irregular_words_flagged(self) -> None:
        r = check_decodability("Tomorrow the beautiful knight laughed loudly.", "2", unit=8)
        assert r["accessible_pct"] < 100
        assert "beautiful" in r["off_scope_words"]
        assert "laughed" in r["off_scope_words"]

    def test_grade3_technical_words_flagged(self) -> None:
        r = check_decodability("Chlorophyll photosynthesis encyclopedia", "3", unit=2)
        assert "chlorophyll" in r["irregular_words"]
        assert not r["meets_target"]

    def test_nonsense_word_not_accepted(self) -> None:
        r = check_decodability("Shnorkelbit sat.", "1", unit=10)
        assert "shnorkelbit" in r["not_in_dictionary_words"]

    def test_unit_changes_result(self) -> None:
        early = check_decodability("The dog sat on a log.", "K", unit=3)
        later = check_decodability("The dog sat on a log.", "K", unit=4)
        assert "log" in early["not_yet_decodable_words"]
        assert "log" not in later["off_scope_words"]


class TestWordAlignment:
    @pytest.mark.parametrize("word", ["cat", "ship", "duck", "bell", "think", "sing", "quit"])
    def test_kindergarten_patterns_decodable_by_end_of_k(self, word: str) -> None:
        assert analyze_word(word, taught("K", 10))["status"] == "decodable"

    @pytest.mark.parametrize("word", ["cake", "bike", "hope", "cute", "these"])
    def test_silent_e(self, word: str) -> None:
        assert analyze_word(word, taught("K", 10))["status"] == "not_yet_decodable"
        assert analyze_word(word, taught("1", 3))["status"] == "decodable"

    def test_silent_e_with_ed_needs_suffix_unit(self) -> None:
        assert analyze_word("baked", taught("1", 3))["missing_gpc_ids"] == ["suffix_ed"]
        assert analyze_word("baked", taught("1", 6))["status"] == "decodable"

    def test_missing_pattern_is_named(self) -> None:
        r = analyze_word("night", taught("1", 10))
        assert r["status"] == "not_yet_decodable"
        assert any("igh" in p for p in r["missing_patterns"])

    @pytest.mark.parametrize("word", ["said", "was", "of", "the", "because"])
    def test_irregular_words_not_decodable(self, word: str) -> None:
        assert analyze_word(word, ALL_GPC_IDS)["status"] in ("irregular", "not_yet_decodable")

    def test_taught_heart_word(self) -> None:
        r = analyze_word("said", taught("K", 3), heart_words=["said"])
        assert r["status"] == "heart_word"

    def test_decodable_words_not_counted_as_heart_words(self) -> None:
        # The old list treated plainly decodable words like 'and', 'it', 'can' as heart words.
        for w in ["and", "it", "can", "up", "him", "just"]:
            assert analyze_word(w, taught("K", 10))["status"] == "decodable", w

    def test_breakdown_is_sound_by_sound(self) -> None:
        assert analyze_word("chat", ALL_GPC_IDS)["breakdown"] == "ch - a - t → /ch/ /ă/ /t/"
        assert analyze_word("shop", ALL_GPC_IDS)["breakdown"].endswith("/sh/ /ŏ/ /p/")


class TestScope:
    def test_scope_is_cumulative(self) -> None:
        k = set(taught("K", 10))
        g1 = set(taught("1", 2))
        assert k < g1
        assert "vce_a" in g1 and "vce_a" not in k

    def test_custom_gpcs_override(self) -> None:
        r = check_decodability("cat sat", "1", unit=10, taught_gpcs=["c", "s", "t"], taught_heart_words=[])
        assert r["decodable_pct"] == 0
        assert r["scope_source"] == "caller_supplied"


class TestCueingDetection:
    def test_flags_msv_prompts(self) -> None:
        flags = detect_cueing("Look at the picture. What word would make sense here? Does it sound right?")
        rules = {f["rule"] for f in flags}
        assert {"picture", "makes_sense", "sounds_right"} <= rules
        assert all(f["suggested_prompt"] for f in flags)

    def test_story_text_not_flagged(self) -> None:
        assert detect_cueing("The cat sat on the mat. Pat had a big red hat.") == []

    def test_cueing_in_decodability_result(self) -> None:
        r = check_decodability("Skip it and come back. The cat sat.", "1", unit=1)
        assert r["cueing_flags"]
        assert r["anti_cueing_passed"] is False


class TestValidation:
    def test_invalid_grade(self) -> None:
        assert "error_code" in check_decodability("cat", "invalid")

    def test_empty_text(self) -> None:
        assert "error_code" in check_decodability("", "1")

    def test_too_long(self) -> None:
        assert "error_code" in check_decodability("cat " * 2000, "1")

    def test_required_fields(self) -> None:
        r = check_decodability("The cat sat on a mat.", "K", unit=4)
        required = {
            "total_words", "decodable_pct", "accessible_pct", "meets_target", "heart_words",
            "off_scope_words", "missing_patterns", "words", "cueing_flags", "recommendation",
        }
        assert required <= r.keys()


@pytest.mark.asyncio
async def test_verify_decodable_text_async() -> None:
    r = await verify_decodable_text("Pat has a cat.", "K", "4")
    assert r["status"] == "ok"
    assert r["meets_target"] is True
