"""MCP Tool: get_phonics_scope — fetch phonics scope and sequence.

Bridges to GET /api/v1/phonics/scope on sor.edtechlabs.dev with local fallback.
"""

from __future__ import annotations

from typing import Any

from src.client.sor_client import SoRClient
from src.config import Settings
from src.errors import (
    SoRAPIErrorCode,
    format_api_error,
)

GRADE_ORDER = ["K", "1", "2", "3"]


def _local_scope(grade_level: str, unit: str) -> dict[str, Any]:
    """Build the scope from the same cumulative model the decodability checker uses.

    Showing one scope and checking against another confuses teachers, so this is
    derived from ``scope_engine`` and nothing else.
    """
    from src.tools.scope_engine import parse_unit, taught_scope

    modeled = grade_level if grade_level in GRADE_ORDER else "3"
    unit_n = parse_unit(unit) or 1
    current = taught_scope(modeled, unit_n)
    previous = taught_scope(modeled, unit_n - 1) if unit_n > 1 else {"graphemes": set(), "rules": set()}
    if unit_n == 1 and modeled != "K":
        previous = taught_scope(GRADE_ORDER[GRADE_ORDER.index(modeled) - 1], None)

    def _order(items: set[str]) -> list[str]:
        return sorted(items, key=lambda g: (len(g), g))

    new_graphemes = _order(current["graphemes"] - previous["graphemes"])
    new_rules = sorted(current["rules"] - previous["rules"])
    return {
        "target_phonemes": [f"/{g}/" for g in new_graphemes],
        "target_graphemes": new_graphemes,
        "taught_graphemes": _order(current["graphemes"]),
        "taught_rules": sorted(current["rules"]),
        "heart_words": [{"word": w} for w in sorted(current["heart_words"])],
        "unit_objectives": [
            ("New this unit: " + ", ".join(new_graphemes + new_rules)) if (new_graphemes or new_rules) else "No new graphemes this unit; consolidate earlier patterns with fluency practice"
        ],
        "prerequisite_skills": [name for name in current["groups"][:-1]][-3:],
        "note": (
            "Grades 4-5 are not modeled; showing the Grade 3 scope." if grade_level in {"4", "5"} else
            "Default sequence is a generic example. Replace it with your program's scope and sequence."
        ),
    }


async def get_phonics_scope(
    grade_level: str,
    unit: str = "1",
    client: SoRClient | None = None,
    settings: Settings | None = None,
) -> dict[str, Any]:
    """Fetch the phonics scope and sequence for a given grade and unit."""
    valid_grades = {"K", "1", "2", "3", "4", "5"}
    if grade_level not in valid_grades:
        return format_api_error(
            SoRAPIErrorCode.ERR_INVALID_GRADE_BAND,
            grade=grade_level,
        )

    if client is not None:
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
                "cached": True,
            }
        except Exception:
            pass  # Fall through to local fallback

    scope_data = _local_scope(grade_level, unit)
    return {
        "status": "ok",
        "grade_level": grade_level,
        "unit": unit,
        "target_phonemes": scope_data["target_phonemes"],
        "target_graphemes": scope_data["target_graphemes"],
        "taught_graphemes": scope_data["taught_graphemes"],
        "taught_rules": scope_data["taught_rules"],
        "heart_words": scope_data["heart_words"],
        "unit_objectives": scope_data["unit_objectives"],
        "prerequisite_skills": scope_data["prerequisite_skills"],
        "note": scope_data["note"],
        "source": "local_scope_engine",
        "cached": True,
    }
