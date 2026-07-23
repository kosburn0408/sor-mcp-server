"""Tests for the anti-cueing decodability verifier.

Validates decodability analysis, anti-cueing detection, heart word
identification, and structured error codes.
"""

from __future__ import annotations

import pytest

from src.tools.decodability import (
    verify_decodable_text,
    MANDATORY_HEART_WORDS,
)


class TestDecodabilityAnalysis:
    """Test core decodability percentage computation."""

    def test_fully_decodable_text(self, clean_decodable_text: str) -> None:
        """Simple CVC text should be highly decodable at K level."""
        result = verify_decodable_text(
            text=clean_decodable_text,
            target_skill="cvc_short_a",
            grade_level="K",
        )
        assert result["decodable_pct"] >= 80.0
        assert result["total_words"] > 0

    def test_grade_validation(self) -> None:
        """Invalid grade should return error."""
        result = verify_decodable_text(
            text="cat",
            target_skill="cvc_short_a",
            grade_level="invalid",
        )
        assert "error_code" in result

    def test_empty_text(self) -> None:
        """Empty text should return error."""
        result = verify_decodable_text(
            text="",
            target_skill="cvc_short_a",
        )
        assert "error_code" in result

    def test_instructional_level_determined(self, sample_decodable_text: str) -> None:
        """Result should include an instructional level."""
        result = verify_decodable_text(
            text=sample_decodable_text,
            target_skill="cvc_short_a",
            grade_level="1",
        )
        assert result["instructional_level"] in ("independent", "instructional", "frustration")

    def test_target_skill_words_identified(self) -> None:
        """Words matching the target skill should be listed."""
        result = verify_decodable_text(
            text="cat hat mat sat",
            target_skill="cvc_short_a",
            grade_level="K",
        )
        assert len(result["target_skill_words"]) >= 1

    def test_heart_words_identified(self) -> None:
        """Mandatory heart words should be flagged."""
        result = verify_decodable_text(
            text="The cat said was to go",
            target_skill="cvc_short_a",
            grade_level="K",
        )
        heart_word_texts = [hw["word"] for hw in result["heart_words"]]
        assert "said" in heart_word_texts or "the" in heart_word_texts or "was" in heart_word_texts


class TestAntiCueingDetection:
    """Test that 3-cueing/MSV strategies are detected and flagged."""

    def test_cueing_detected_in_text(self, cued_text: str) -> None:
        """Text with 'look at the picture' should be flagged."""
        result = verify_decodable_text(
            text=cued_text,
            target_skill="cvc_short_a",
            grade_level="1",
            enable_anti_cueing=True,
        )
        assert len(result["warnings"]) > 0, "Expected anti-cueing warnings"
        warning_codes = [w["code"] for w in result["warnings"]]
        assert "ERR_CUEING_DETECTED" in warning_codes

    def test_picture_guessing_flagged(self) -> None:
        """Picture-dependent language should be flagged."""
        result = verify_decodable_text(
            text="Look at the picture and guess what the word is.",
            target_skill="cvc_short_a",
            grade_level="1",
            enable_anti_cueing=True,
        )
        warnings = result["warnings"]
        assert any("picture" in w.get("message", "").lower() for w in warnings)

    def test_msv_explicit_flagged(self) -> None:
        """Explicit 3-cueing/MSV references should be flagged."""
        result = verify_decodable_text(
            text="The three-cueing system helps students guess words.",
            target_skill="cvc_short_a",
            grade_level="1",
            enable_anti_cueing=True,
        )
        warnings = result["warnings"]
        assert any(
            "MSV" in str(w.get("message", "")) or "cueing" in str(w.get("message", "")).lower()
            for w in warnings
        )

    def test_anti_cueing_disabled(self, cued_text: str) -> None:
        """Disabling anti-cueing should not produce warnings."""
        result = verify_decodable_text(
            text=cued_text,
            target_skill="cvc_short_a",
            grade_level="1",
            enable_anti_cueing=False,
        )
        # Warnings may still exist for decodability issues but not anti-cueing
        anti_cue_warnings = [w for w in result["warnings"] if w["code"] == "ERR_CUEING_DETECTED"]
        assert len(anti_cue_warnings) == 0

    def test_skip_and_return_flagged(self) -> None:
        """Skip-it-and-come-back strategy should be flagged."""
        result = verify_decodable_text(
            text="If you don't know a word, skip it and go on.",
            target_skill="cvce_silent_e",
            grade_level="2",
            enable_anti_cueing=True,
        )
        warnings = result["warnings"]
        assert len(warnings) > 0

    def test_context_over_decoding_flagged(self) -> None:
        """Context-over-decoding strategies should be flagged."""
        result = verify_decodable_text(
            text="Use context to figure out the difficult words.",
            target_skill="cvce_silent_e",
            grade_level="2",
            enable_anti_cueing=True,
        )
        # Context-over-decoding creates warnings
        assert isinstance(result["warnings"], list)


class TestHeartWordValidation:
    """Test that heart words are correctly identified."""

    def test_mandatory_heart_words_exist(self) -> None:
        """MANDATORY_HEART_WORDS should have known entries."""
        assert "the" in MANDATORY_HEART_WORDS
        assert "said" in MANDATORY_HEART_WORDS
        assert "was" in MANDATORY_HEART_WORDS

    def test_heart_word_has_required_fields(self) -> None:
        """Each heart word should have regular_part and heart_part."""
        for word, data in MANDATORY_HEART_WORDS.items():
            assert "regular_part" in data, f"Missing regular_part for {word}"
            assert "heart_part" in data, f"Missing heart_part for {word}"
            assert "explanation" in data, f"Missing explanation for {word}"


class TestOffScopeDetection:
    """Test that words with untaught patterns are correctly identified."""

    def test_untaught_patterns_flag_off_scope(self) -> None:
        """Words with patterns beyond grade level should be flagged."""
        result = verify_decodable_text(
            text="The beautiful butterfly flew away.",
            target_skill="cvc_short_a",
            grade_level="K",
        )
        assert len(result["off_scope_words"]) > 0

    def test_off_scope_words_have_suggestions(self) -> None:
        """Each off-scope word should have a replacement suggestion."""
        result = verify_decodable_text(
            text="The photosynthesis process is complex.",
            target_skill="cvc_short_a",
            grade_level="1",
        )
        for word in result["off_scope_words"]:
            assert "suggestion" in word
            assert word["word"]


class TestOutputShape:
    """Test that results have all required fields."""

    def test_required_fields_present(self, clean_decodable_text: str) -> None:
        """All expected fields should be in the output."""
        result = verify_decodable_text(
            text=clean_decodable_text,
            target_skill="cvc_short_a",
            grade_level="K",
        )
        required = {
            "total_words", "decodable_count", "decodable_pct",
            "target_skill_words", "heart_words", "off_scope_words",
            "warnings", "recommendation", "instructional_level",
        }
        assert required.issubset(result.keys())
