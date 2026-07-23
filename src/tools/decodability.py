"""MCP Tool: verify_decodable_text — API-based decodability verification.

Bridges to POST /api/v1/decodability/verify on sor.edtechlabs.dev.
"""

from __future__ import annotations

from typing import Any

from src.client.sor_client import SoRClient
from src.config import Settings
from src.errors import (
    SoRAPIErrorCode,
    format_api_error,
)
from src.schemas.api import DecodabilityResult


async def verify_decodable_text(
    text: str,
    grade_level: str,
    unit: str = "1",
    client: SoRClient | None = None,
    settings: Settings | None = None,
) -> dict[str, Any]:
    """Verify text decodability against the phonics scope for a grade/unit.

    Checks every word against the cumulative phonics scope, identifies heart
    words, flags off-scope patterns, detects 3-cueing/MSV strategies, and
    suggests decodable substitutions.

    Args:
        text: The text passage to verify (max 5000 chars).
        grade_level: Grade level (K, 1, 2, 3, 4, 5).
        unit: Curriculum unit for scope reference (default: '1').
        client: Optional pre-configured SoRClient.
        settings: Optional Settings.

    Returns:
        Dict with decodable_pct, total_words, off_scope_words, heart_words,
        substitutions, cueing_flags, and instructional_level.
    """
    # Validate grade
    valid_grades = {"K", "1", "2", "3", "4", "5"}
    if grade_level not in valid_grades:
        return format_api_error(
            SoRAPIErrorCode.ERR_INVALID_GRADE_BAND,
            grade=grade_level,
        )

    if not text or not text.strip():
        return format_api_error(
            SoRAPIErrorCode.ERR_INVALID_INPUT,
            detail="text is empty",
        )

    if len(text) > 5000:
        return format_api_error(
            SoRAPIErrorCode.ERR_INVALID_INPUT,
            detail=f"text exceeds 5000 character limit ({len(text)} chars)",
        )

    if client is None:
        client = SoRClient(settings or Settings())

    try:
        result = await client.verify_decodable_text(text, grade_level, unit)

        # Determine instructional level
        if result.decodable_pct >= 95:
            level = "independent"
        elif result.decodable_pct >= 90:
            level = "instructional"
        else:
            level = "frustration"

        # Check for anti-cueing
        warnings: list[dict[str, str]] = []
        if result.cueing_flags:
            for flag in result.cueing_flags:
                warnings.append({
                    "severity": "error",
                    "code": SoRAPIErrorCode.ERR_CUEING_DETECTED.value,
                    "message": f"Cueing detected: {flag}",
                })

        return {
            "status": "ok",
            "decodable_pct": result.decodable_pct,
            "total_words": result.total_words,
            "off_scope_words": result.off_scope_words,
            "heart_words": result.heart_words,
            "substitutions": result.substitutions,
            "cueing_flags": result.cueing_flags,
            "warnings": warnings,
            "instructional_level": level,
            "recommendation": _get_recommendation(level, result.decodable_pct),
            "grade_level": grade_level,
            "unit": unit,
            "source": "sor.edtechlabs.dev",
        }
    except Exception as exc:
        return format_api_error(
            SoRAPIErrorCode.ERR_UPSTREAM_REGISTRY_UNAVAILABLE,
            detail=str(exc),
        )


def _get_recommendation(level: str, pct: float) -> str:
    """Instructional recommendation based on decodability percentage."""
    if level == "independent":
        return (
            f"{pct:.0f}% decodable — suitable for independent reading practice. "
            "Pre-teach heart words before reading."
        )
    elif level == "instructional":
        return (
            f"{pct:.0f}% decodable — suitable for guided reading with teacher support. "
            "Review off-scope words and pre-teach patterns."
        )
    else:
        return (
            f"{pct:.0f}% decodable — frustration level. "
            "Revise text to use only mastered patterns, or use as teacher-read text only."
        )
