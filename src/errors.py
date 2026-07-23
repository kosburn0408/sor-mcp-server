"""Structured MCP error codes — API-bridge extensions.

Extends src/core/errors.py with upstream-API-specific error codes for the
sor.edtechlabs.dev bridge. Re-exports all existing codes so tools can import
from a single location.
"""

from __future__ import annotations

from collections import defaultdict
from enum import Enum
from typing import Any


class SoRAPIErrorCode(str, Enum):
    """API-bridge error codes for sor.edtechlabs.dev integration."""

    # ── Upstream / Network ─────────────────────────────────────────────
    ERR_UPSTREAM_REGISTRY_UNAVAILABLE = "ERR_UPSTREAM_REGISTRY_UNAVAILABLE"
    ERR_API_AUTH = "ERR_API_AUTH"
    ERR_API_TIMEOUT = "ERR_API_TIMEOUT"

    # ── Scope / Unit Validation ────────────────────────────────────────
    ERR_INVALID_SCOPE_UNIT = "ERR_INVALID_SCOPE_UNIT"
    ERR_INVALID_GRADE_BAND = "ERR_INVALID_GRADE_BAND"
    ERR_OFF_SCOPE_PHONEME = "ERR_OFF_SCOPE_PHONEME"

    # ── Decodability / Anti-Cueing ─────────────────────────────────────
    ERR_CUEING_DETECTED = "ERR_CUEING_DETECTED"
    ERR_UNTAUGHT_PATTERN = "ERR_UNTAUGHT_PATTERN"

    # ── General ────────────────────────────────────────────────────────
    ERR_INVALID_INPUT = "ERR_INVALID_INPUT"
    ERR_CACHE_MISS = "ERR_CACHE_MISS"


# Human-readable messages
ERROR_MESSAGES: dict[SoRAPIErrorCode, str] = {
    SoRAPIErrorCode.ERR_UPSTREAM_REGISTRY_UNAVAILABLE: (
        "The SoR API at sor.edtechlabs.dev is currently unreachable. "
        "Detail: {detail}"
    ),
    SoRAPIErrorCode.ERR_API_AUTH: (
        "API authentication failed. Check SOR_API_KEY. Detail: {detail}"
    ),
    SoRAPIErrorCode.ERR_API_TIMEOUT: (
        "Request to sor.edtechlabs.dev timed out after {timeout}s. "
        "Consider increasing SOR_REQUEST_TIMEOUT."
    ),
    SoRAPIErrorCode.ERR_INVALID_SCOPE_UNIT: (
        "Unit '{unit}' not found for grade '{grade}'. "
        "Verify the unit exists in the scope and sequence."
    ),
    SoRAPIErrorCode.ERR_INVALID_GRADE_BAND: (
        "Grade '{grade}' is outside the supported range. "
        "Supported: K, 1, 2, 3, 4, 5."
    ),
    SoRAPIErrorCode.ERR_OFF_SCOPE_PHONEME: (
        "The target phoneme '{detail}' is not in the scope sequence for grade '{grade}'."
    ),
    SoRAPIErrorCode.ERR_CUEING_DETECTED: (
        "Three-cueing / MSV strategies detected: {detail}. "
        "Science of Reading best practice prohibits guessing from context. "
        "Students must decode phoneme-by-phoneme."
    ),
    SoRAPIErrorCode.ERR_UNTAUGHT_PATTERN: (
        "Text contains untaught phonics pattern '{detail}'. "
        "Constrain text to mastered patterns only."
    ),
    SoRAPIErrorCode.ERR_INVALID_INPUT: (
        "Invalid input: {detail}"
    ),
    SoRAPIErrorCode.ERR_CACHE_MISS: (
        "Cache miss for key: {detail}"
    ),
}


def format_api_error(
    code: SoRAPIErrorCode,
    detail: str = "",
    **kwargs: str,
) -> dict[str, Any]:
    """Format a structured API error response.

    Args:
        code: Error code enum value.
        detail: Primary detail for the message template.
        **kwargs: Additional template variables (e.g., grade='K', unit='3').

    Returns:
        Dict with error_code, error_message, hint keys.
    """
    template = ERROR_MESSAGES.get(code, "Unknown error: {detail}")

    class _SafeFormatter(defaultdict[str, str]):
        def __missing__(self, key: str) -> str:
            return ""

    msg = template.format_map(_SafeFormatter(detail=detail, **kwargs))
    return {
        "error_code": code.value,
        "error_message": msg,
        "hint": _get_api_hint(code),
    }


def _get_api_hint(code: SoRAPIErrorCode) -> str:
    hints: dict[SoRAPIErrorCode, str] = {
        SoRAPIErrorCode.ERR_UPSTREAM_REGISTRY_UNAVAILABLE: (
            "Verify sor.edtechlabs.dev is reachable and SOR_API_BASE_URL is correct."
        ),
        SoRAPIErrorCode.ERR_API_AUTH: (
            "Set SOR_API_KEY environment variable or .env file."
        ),
        SoRAPIErrorCode.ERR_API_TIMEOUT: (
            "Increase SOR_REQUEST_TIMEOUT or check network connectivity."
        ),
        SoRAPIErrorCode.ERR_INVALID_SCOPE_UNIT: (
            "Call get_phonics_scope to list available units for this grade."
        ),
        SoRAPIErrorCode.ERR_INVALID_GRADE_BAND: (
            "Supported grades: K, 1, 2, 3, 4, 5."
        ),
        SoRAPIErrorCode.ERR_OFF_SCOPE_PHONEME: (
            "Consult the phonics scope for grade-appropriate phonemes."
        ),
        SoRAPIErrorCode.ERR_CUEING_DETECTED: (
            "Replace cueing strategies with explicit decoding instruction."
        ),
        SoRAPIErrorCode.ERR_UNTAUGHT_PATTERN: (
            "Remove this pattern or pre-teach it before using the text."
        ),
        SoRAPIErrorCode.ERR_INVALID_INPUT: (
            "Check input format and try again."
        ),
        SoRAPIErrorCode.ERR_CACHE_MISS: (
            "Cache entry expired or not found. Data will be fetched on next request."
        ),
    }
    return hints.get(code, "Contact support if this error persists.")
