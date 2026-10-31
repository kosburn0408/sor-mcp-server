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

from src.engine.gpc import gpc_label
from src.engine.scope_sequence import describe_scope, normalize_grade, resolve_scope


def _graphemes_for(gpc_ids: list[str]) -> list[str]:
    from src.engine.gpc import CATALOG, SPECIAL_GPCS

    out: list[str] = []
    for gid in gpc_ids:
        if gid.startswith("vce_"):
            out.append(f"{gid[-1]}_e")
        elif gid in SPECIAL_GPCS:
            out.append(gid.replace("_", " "))
        else:
            out.extend(g.grapheme for g in CATALOG if g.id == gid)
    return list(dict.fromkeys(out))


async def get_phonics_scope(
    grade_level: str,
    unit: str = "1",
    client: SoRClient | None = None,  # kept for interface compatibility; scope is local
    settings: Settings | None = None,
) -> dict[str, Any]:
    """Return the cumulative phonics scope through a grade and unit.

    Uses the default illustrative sequence, or the district sequence in
    ``SOR_SCOPE_PATH``. See ``src/engine/scope_sequence.py``.
    """
    grade = normalize_grade(grade_level)
    if grade is None:
        return format_api_error(SoRAPIErrorCode.ERR_INVALID_GRADE_BAND, grade=grade_level)

    scope = describe_scope(resolve_scope(grade, unit))
    return {
        "status": "ok",
        "grade_level": grade,
        "unit": str(scope["unit"]),
        "unit_title": scope["unit_title"],
        "new_patterns": scope["new_patterns"],
        "target_phonemes": [gpc_label(g) for g in scope["new_gpcs"]],
        "taught_graphemes": _graphemes_for(scope["taught_gpcs"]),
        "taught_gpc_ids": scope["taught_gpcs"],
        "heart_words": [{"word": w, "note": scope["heart_word_notes"].get(w, "")} for w in scope["heart_words"]],
        "new_heart_words": scope["new_heart_words"],
        "unit_objectives": [f"Decode words with: {', '.join(scope['new_patterns'])}"] if scope["new_patterns"] else [],
        "prerequisite_skills": scope["taught_patterns"][: max(0, len(scope["taught_patterns"]) - len(scope["new_patterns"]))][-6:],
        "source": scope["source"],
        "note": (
            "Default sequence is illustrative, not a specific published program. "
            "Set SOR_SCOPE_PATH to your district's adopted scope & sequence."
        ),
        "cached": True,
    }
