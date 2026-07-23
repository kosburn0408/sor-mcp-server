"""Structured MCP error codes for the Science of Reading MCP server.

Provides consistent error identification without exposing stack traces.
All error codes are prefixed with ERR_ for easy client-side matching.
"""

from __future__ import annotations

from enum import Enum
from typing import Any


class SoRErrorCode(str, Enum):
    """Categorized error codes for literacy domain operations."""

    # ── Scope / Grade Validation ───────────────────────────────────────
    ERR_OFF_SCOPE_PHONEME = "ERR_OFF_SCOPE_PHONEME"
    ERR_INVALID_GRADE_BAND = "ERR_INVALID_GRADE_BAND"
    ERR_INVALID_SYLLABLE_TYPE = "ERR_INVALID_SYLLABLE_TYPE"

    # ── Decodability / Anti-Cueing ─────────────────────────────────────
    ERR_CUEING_DETECTED = "ERR_CUEING_DETECTED"
    ERR_HEART_WORD_AS_DECODABLE = "ERR_HEART_WORD_AS_DECODABLE"
    ERR_UNTAUGHT_PATTERN = "ERR_UNTAUGHT_PATTERN"

    # ── Remediation / Diagnostics ──────────────────────────────────────
    ERR_UNKNOWN_DEFICIT_CODE = "ERR_UNKNOWN_DEFICIT_CODE"
    ERR_INVALID_SCORE_RANGE = "ERR_INVALID_SCORE_RANGE"
    ERR_UNSUPPORTED_SKILL = "ERR_UNSUPPORTED_SKILL"

    # ── Standards / Frameworks ─────────────────────────────────────────
    ERR_UNKNOWN_STANDARD_SET = "ERR_UNKNOWN_STANDARD_SET"
    ERR_UNKNOWN_FRAMEWORK = "ERR_UNKNOWN_FRAMEWORK"

    # ── General ────────────────────────────────────────────────────────
    ERR_INVALID_INPUT = "ERR_INVALID_INPUT"
    ERR_DATABASE = "ERR_DATABASE"


# Human-readable messages for each error code
ERROR_MESSAGES: dict[SoRErrorCode, str] = {
    SoRErrorCode.ERR_OFF_SCOPE_PHONEME: (
        "The target phoneme '{detail}' is not in the scope sequence for grade '{grade}'. "
        "Consult the curriculum scope and sequence for grade-appropriate phonemes."
    ),
    SoRErrorCode.ERR_INVALID_GRADE_BAND: (
        "Grade '{grade}' is outside the supported K-5 range. "
        "This server supports Kindergarten through Grade 5."
    ),
    SoRErrorCode.ERR_INVALID_SYLLABLE_TYPE: (
        "Unknown syllable type '{detail}'. "
        "Valid types: closed, open, VCe, r-controlled, vowel team, C+le."
    ),
    SoRErrorCode.ERR_CUEING_DETECTED: (
        "Three-cueing / MSV strategy detected in the provided text or instructions. "
        "Science of Reading best practice prohibits guessing from context, picture cues, "
        "or sentence structure. Students must decode phoneme-by-phoneme. "
        "Remove: {detail}"
    ),
    SoRErrorCode.ERR_HEART_WORD_AS_DECODABLE: (
        "Word '{detail}' is incorrectly marked as fully decodable. "
        "This word contains phoneme-grapheme correspondences not yet taught "
        "and should be presented as a Heart Word with the irregular part explicitly noted."
    ),
    SoRErrorCode.ERR_UNTAUGHT_PATTERN: (
        "The text contains phonics pattern '{detail}' which has not been taught "
        "according to the provided scope and sequence. Text should be constrained "
        "to mastered patterns only."
    ),
    SoRErrorCode.ERR_UNKNOWN_DEFICIT_CODE: (
        "Unknown deficit code '{detail}'. Run list_remediations to see valid codes."
    ),
    SoRErrorCode.ERR_INVALID_SCORE_RANGE: (
        "Score '{detail}' is outside the valid range of 0.0-1.0."
    ),
    SoRErrorCode.ERR_UNSUPPORTED_SKILL: (
        "The requested skill '{detail}' is not supported. "
        "Check the remediation table for supported skills."
    ),
    SoRErrorCode.ERR_UNKNOWN_STANDARD_SET: (
        "Unknown standard set '{detail}'. Supported: CCSS, TEXAS, FLORIDA, NY, GEORGIA."
    ),
    SoRErrorCode.ERR_UNKNOWN_FRAMEWORK: (
        "Unknown framework '{detail}'. Supported: Simple View, Scarborough's Rope, "
        "Five Pillars, Four-Part Processor, WWC Foundational Skills."
    ),
    SoRErrorCode.ERR_INVALID_INPUT: (
        "Invalid input: {detail}"
    ),
    SoRErrorCode.ERR_DATABASE: (
        "Database operation failed: {detail}"
    ),
}


def format_error(code: SoRErrorCode, detail: str = "", **kwargs: str) -> dict[str, Any]:
    """Format a structured error response with an error code and human message.

    Args:
        code: The SoRErrorCode to use.
        detail: Primary detail string (formatted into the message).
        **kwargs: Additional keyword parameters for message formatting
                  (e.g., grade='K').

    Returns:
        Dictionary with error_code, error_message, and optional hints.
    """
    from collections import defaultdict

    template = ERROR_MESSAGES.get(code, "Unknown error: {detail}")

    # Use defaultdict so missing template variables fall back to empty string
    # instead of raising KeyError (e.g., when caller doesn't pass 'grade')
    safe_kwargs: defaultdict[str, str] = defaultdict(str, detail=detail, **kwargs)

    # Use format_map with the defaultdict for safe formatting
    class _SafeFormatter(defaultdict[str, str]):
        def __missing__(self, key: str) -> str:
            return ""

    msg = template.format_map(_SafeFormatter(detail=detail, **kwargs))
    return {
        "error_code": code.value,
        "error_message": msg,
        "hint": _get_hint(code),
    }


def _get_hint(code: SoRErrorCode) -> str:
    """Return a helpful resolution hint for each error code."""
    hints: dict[SoRErrorCode, str] = {
        SoRErrorCode.ERR_OFF_SCOPE_PHONEME: (
            "Use query_sor_curriculum to find the scope sequence for this grade."
        ),
        SoRErrorCode.ERR_INVALID_GRADE_BAND: "Use grade K, 1, 2, 3, 4, or 5.",
        SoRErrorCode.ERR_INVALID_SYLLABLE_TYPE: "Use one of: closed, open, VCe, r-controlled, vowel_team, c_le.",
        SoRErrorCode.ERR_CUEING_DETECTED: "Replace with explicit decoding instruction.",
        SoRErrorCode.ERR_HEART_WORD_AS_DECODABLE: "Tag the irregular part explicitly.",
        SoRErrorCode.ERR_UNTAUGHT_PATTERN: "Remove the pattern or pre-teach it before using this text.",
        SoRErrorCode.ERR_UNKNOWN_DEFICIT_CODE: "Call list_remediations for valid codes.",
        SoRErrorCode.ERR_INVALID_SCORE_RANGE: "Scores must be between 0.0 and 1.0.",
        SoRErrorCode.ERR_UNSUPPORTED_SKILL: "Check available remediations with list_remediations.",
        SoRErrorCode.ERR_UNKNOWN_STANDARD_SET: "Try CCSS, TEXAS, FLORIDA, NY, or GEORGIA.",
        SoRErrorCode.ERR_UNKNOWN_FRAMEWORK: "Use list_frameworks to see available frameworks.",
        SoRErrorCode.ERR_INVALID_INPUT: "Check the input format and try again.",
        SoRErrorCode.ERR_DATABASE: "Check that the DuckDB database is seeded and accessible.",
    }
    return hints.get(code, "Contact support if this persists.")
