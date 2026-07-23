"""Tests for the dynamic meta-tool router (query_sor_curriculum).

Validates routing decisions, grade validation, error codes, and
compact curriculum result format.
"""

from __future__ import annotations

import pytest

from src.core.errors import SoRErrorCode, format_error
from src.core.router import query_sor_curriculum


class TestRouterRouting:
    """Test that the router dispatches to correct internal handlers."""

    def test_phonology_strand_returns_scope(self) -> None:
        """Phonology strand should return scope with phonemes and concepts."""
        result = query_sor_curriculum(grade_level="K", strand="phonology")
        assert result["strand"] == "phonology"
        assert result["grade"] == "K"
        assert "concepts" in result
        assert "phonemes" in result
        assert len(result["concepts"]) > 0
        assert result["tool_routed_to"] == "scope_sequence_lookup"

    def test_phonology_with_phoneme_lookup(self) -> None:
        """Phoneme parameter should add remediation code."""
        result = query_sor_curriculum(
            grade_level="1", strand="phonology", target_phoneme="/a/"
        )
        assert result["remediation_code"] == "cvc_short_a"
        assert result["tool_routed_to"] == "phoneme_remediation_lookup"

    def test_phonology_with_syllable_type(self) -> None:
        """Syllable type should enrich concepts."""
        result = query_sor_curriculum(
            grade_level="1", strand="phonology", syllable_type="closed"
        )
        assert "closed" in str(result["concepts"])
        assert result["tool_routed_to"] == "syllable_type_scope"

    def test_morphology_strand(self) -> None:
        """Morphology strand should return morphology concepts."""
        result = query_sor_curriculum(grade_level="2", strand="morphology")
        assert result["strand"] == "morphology"
        assert len(result["concepts"]) > 0

    def test_standards_lookup_enriches_results(self) -> None:
        """Standard state parameter should add matched standards."""
        result = query_sor_curriculum(
            grade_level="1", strand="phonology", standard_state="CCSS"
        )
        assert "matched_standards" in result
        assert result["tool_routed_to"] == "standards_scope_lookup"


class TestRouterValidation:
    """Test that the router rejects invalid inputs with proper error codes."""

    def test_invalid_grade_rejected(self) -> None:
        """Invalid grade should return ERR_INVALID_GRADE_BAND."""
        result = query_sor_curriculum(grade_level="7", strand="phonology")
        assert result["error_code"] == SoRErrorCode.ERR_INVALID_GRADE_BAND

    def test_invalid_strand_rejected(self) -> None:
        """Invalid strand should return proper error."""
        result = query_sor_curriculum(grade_level="1", strand="garbage")
        assert result["error_code"] == SoRErrorCode.ERR_INVALID_INPUT

    def test_valid_grades_accepted(self) -> None:
        """All valid grades K-5 should work."""
        for grade in ["K", "1", "2", "3", "4", "5"]:
            result = query_sor_curriculum(grade_level=grade, strand="phonology")
            assert result["grade"] == grade
            assert "error_code" not in result

    def test_invalid_syllable_type_rejected(self) -> None:
        """Invalid syllable type should return ERR_INVALID_SYLLABLE_TYPE."""
        result = query_sor_curriculum(
            grade_level="1", strand="phonology", syllable_type="not_a_type"
        )
        assert result["error_code"] == SoRErrorCode.ERR_INVALID_SYLLABLE_TYPE


class TestRouterOutputShape:
    """Test that output has the expected compact shape."""

    def test_output_keys_present(self) -> None:
        """All expected keys should be in the output."""
        result = query_sor_curriculum(grade_level="K", strand="phonology")
        required_keys = {
            "strand", "grade", "concepts", "prerequisites",
            "next_steps", "matched_standards", "remediation_code", "tool_routed_to",
        }
        assert required_keys.issubset(result.keys())

    def test_output_is_compact(self) -> None:
        """Output should be lean enough for system prompt context."""
        result = query_sor_curriculum(grade_level="K", strand="phonology")
        # Should not have verbose nested structures
        assert "concepts" in result
        assert isinstance(result["concepts"], list)

    def test_all_grades_have_scope_data(self) -> None:
        """Every grade K-5 should return non-empty concepts."""
        for grade in ["K", "1", "2", "3", "4", "5"]:
            result = query_sor_curriculum(grade_level=grade, strand="phonology")
            assert len(result["concepts"]) > 0, f"Grade {grade} has no concepts"


class TestErrorCodeFormat:
    """Test that error codes produce consumable responses."""

    def test_format_error_produces_dict(self) -> None:
        """format_error should return a dict with code and message."""
        err = format_error(SoRErrorCode.ERR_INVALID_GRADE_BAND, detail="bad_grade")
        assert "error_code" in err
        assert "error_message" in err
        assert err["error_code"] == SoRErrorCode.ERR_INVALID_GRADE_BAND

    def test_all_error_codes_have_messages(self) -> None:
        """Every SoRErrorCode should have a message in ERROR_MESSAGES."""
        from src.core.errors import ERROR_MESSAGES
        for code in SoRErrorCode:
            assert code in ERROR_MESSAGES, f"Missing message for {code}"
