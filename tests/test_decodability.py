"""Tests for the anti-cueing decodability verifier.

Validates decodability analysis, anti-cueing detection, heart word
identification, and structured error codes.
"""

from __future__ import annotations

import pytest

from src.tools.decodability import (
    verify_decodable_text,
    check_decodability,
    MANDATORY_HEART_WORDS,
)


class TestDecodabilityAnalysis:
    """Test core decodability percentage computation."""

    def test_fully_decodable_text(self, clean_decodable_text: str) -> None:
        """Simple CVC text should be highly decodable at K level."""
        result = check_decodability(
            text=clean_decodable_text,
            grade_level="K",
        )
        assert result["decodable_pct"] >= 70.0
        assert result["total_words"] > 0

    def test_grade_validation(self) -> None:
        """Invalid grade should return error."""
        result = check_decodability(
            text="cat",
            grade_level="invalid",
        )
        assert "error_code" in result

    def test_empty_text(self) -> None:
        """Empty text should return error."""
        result = check_decodability(
            text="",
            grade_level="1",
        )
        assert "error_code" in result

    def test_instructional_level_determined(self, sample_decodable_text: str) -> None:
        """Result should include an instructional level."""
        result = check_decodability(
            text=sample_decodable_text,
            grade_level="1",
        )
        assert result["instructional_level"] in ("independent", "instructional", "frustration")

    def test_heart_words_identified(self) -> None:
        """Mandatory heart words should be flagged."""
        result = check_decodability(
            text="The cat said was to go",
            grade_level="K",
        )
        assert len(result["heart_words"]) >= 1


class TestHeartWordValidation:
    """Test that heart words are correctly identified."""

    def test_mandatory_heart_words_exist(self) -> None:
        """MANDATORY_HEART_WORDS should have known entries."""
        assert "the" in MANDATORY_HEART_WORDS
        assert "said" in MANDATORY_HEART_WORDS
        assert "was" in MANDATORY_HEART_WORDS


class TestOffScopeDetection:
    """Test that words with untaught patterns are correctly identified."""

    def test_untaught_patterns_flag_off_scope(self) -> None:
        """Words with patterns beyond grade level should be flagged."""
        result = check_decodability(
            text="The beautiful butterfly flew away.",
            grade_level="K",
        )
        assert len(result["off_scope_words"]) > 0


class TestOutputShape:
    """Test that results have all required fields."""

    def test_required_fields_present(self, clean_decodable_text: str) -> None:
        """All expected fields should be in the output."""
        result = check_decodability(
            text=clean_decodable_text,
            grade_level="K",
        )
        required = {
            "total_words", "decodable_count", "decodable_pct",
            "heart_words", "off_scope_words",
            "instructional_level",
        }
        assert required.issubset(result.keys())
