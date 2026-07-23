"""MCP Tool: get_phonics_scope — fetch phonics scope and sequence.

Bridges to GET /api/v1/phonics/scope on sor.edtechlabs.dev.
"""

from __future__ import annotations

from typing import Any

from src.client.sor_client import SoRClient
from src.config import Settings
from src.errors import (
    SoRAPIErrorCode,
    format_api_error,
)
from src.schemas.api import PhonicsScope


async def get_phonics_scope(
    grade_level: str,
    unit: str = "1",
    client: SoRClient | None = None,
    settings: Settings | None = None,
) -> dict[str, Any]:
    """Fetch the phonics scope and sequence for a given grade and unit.

    Returns target phonemes, taught graphemes, heart words, and unit
    objectives from the Science of Reading API. Results are cached for
    the configured TTL (default: 5 minutes).

    Args:
        grade_level: Grade level (K, 1, 2, 3, 4, 5).
        unit: Curriculum unit number (default: '1').
        client: Optional pre-configured SoRClient (created if not provided).
        settings: Optional Settings (loaded from env if not provided).

    Returns:
        Dict with grade_level, unit, target_phonemes, taught_graphemes,
        heart_words, unit_objectives, and prerequisite_skills.
    """
    # Validate grade
    valid_grades = {"K", "1", "2", "3", "4", "5"}
    if grade_level not in valid_grades:
        return format_api_error(
            SoRAPIErrorCode.ERR_INVALID_GRADE_BAND,
            grade=grade_level,
        )

    if client is None:
        client = SoRClient(settings or Settings())

    try:
        scope = await client.get_phonics_scope(grade_level, unit)
        return {
            "status": "ok",
            "grade_level": scope.grade_level,
            "unit": scope.unit,
            "target_phonemes": scope.target_phonemes,
            "taught_graphemes": scope.taught_graphemes,
            "heart_words": scope.heart_words,
            "unit_objectives": scope.unit_objectives,
            "prerequisite_skills": scope.prerequisite_skills,
            "source": "sor.edtechlabs.dev",
            "cached": True,  # always cached when returned
        }
    except Exception as exc:
        return format_api_error(
            SoRAPIErrorCode.ERR_UPSTREAM_REGISTRY_UNAVAILABLE,
            detail=str(exc),
        )
