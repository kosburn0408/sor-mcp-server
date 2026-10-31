"""Decodable text verifier tool.

Checks a passage against the phonics patterns taught through a given grade and
unit. Each word's spelling is aligned to its dictionary pronunciation using
only taught grapheme-phoneme correspondences (see ``src/engine/decoder.py``),
so the result says which words are decodable, which are taught heart words,
and exactly which untaught patterns block the rest.

The same text is scanned for three-cueing prompting language
(``src/engine/cueing.py``).

All analysis runs locally and deterministically; no LLM is involved.
"""

from __future__ import annotations

from typing import Any, Iterable

from src.client.sor_client import SoRClient
from src.config import Settings
from src.engine.cueing import detect_cueing
from src.engine.decoder import analyze_text
from src.engine.scope_sequence import normalize_grade, resolve_scope
from src.errors import SoRAPIErrorCode, format_api_error

MAX_CHARS = 5000


def check_decodability(
    text: str,
    grade_level: str = "1",
    unit: str | int = 1,
    target_pct: float = 90.0,
    min_decodable_pct: float | None = None,
    taught_gpcs: Iterable[str] | None = None,
    taught_heart_words: Iterable[str] | None = None,
    target_skill: str | None = None,  # retained for backward compatibility; unused
) -> dict[str, Any]:
    """Check text decodability against the cumulative scope for grade/unit.

    ``taught_gpcs`` / ``taught_heart_words`` override the scope & sequence when a
    district wants to check against its own program directly.
    """
    if not text or not text.strip():
        return format_api_error(SoRAPIErrorCode.ERR_INVALID_INPUT, detail="text is empty")
    if len(text) > MAX_CHARS:
        return format_api_error(
            SoRAPIErrorCode.ERR_INVALID_INPUT,
            detail=f"text exceeds {MAX_CHARS} character limit ({len(text)} chars)",
        )

    grade = normalize_grade(grade_level)
    if grade is None:
        return format_api_error(SoRAPIErrorCode.ERR_INVALID_GRADE_BAND, grade=grade_level)

    scope = resolve_scope(grade, unit)
    gpcs = list(taught_gpcs) if taught_gpcs is not None else scope["taught_gpcs"]
    hearts = list(taught_heart_words) if taught_heart_words is not None else scope["heart_words"]

    result = analyze_text(text, gpcs, hearts, target_pct=target_pct, min_decodable_pct=min_decodable_pct)
    if result["total_words"] == 0:
        return format_api_error(SoRAPIErrorCode.ERR_INVALID_INPUT, detail="no words found")

    cueing = detect_cueing(text)
    off_scope = sorted(
        set(result["not_yet_decodable_words"]) | set(result["irregular_words"]) | set(result["not_in_dictionary_words"])
    )

    return {
        "status": "ok",
        "text": text,
        "grade_level": grade,
        "unit": scope["unit"],
        "unit_title": scope["unit_title"],
        "scope_source": scope["source"] if taught_gpcs is None else "caller_supplied",
        **result,
        "off_scope_words": off_scope,
        "cueing_flags": cueing,
        "anti_cueing_passed": not cueing,
        "recommendation": _recommendation(result, cueing),
        "method": (
            "Each word's spelling is aligned to its CMU Pronouncing Dictionary pronunciation "
            "using only grapheme-phoneme correspondences taught through this unit."
        ),
        "source": "local_scope_engine",
    }


def _recommendation(result: dict[str, Any], cueing: list[dict[str, Any]]) -> str:
    parts: list[str] = []
    pct, target = result["accessible_pct"], result["target_pct"]
    ok = "meets" if pct >= target else "below"
    parts.append(f"{pct:.0f}% of words are decodable or taught heart words ({ok} the {target:.0f}% target).")
    min_dec = result.get("min_decodable_pct")
    if min_dec is not None:
        dec = result["decodable_pct"]
        ok = "meets" if dec >= min_dec else "below"
        parts.append(f"{dec:.0f}% are decodable from taught patterns alone ({ok} the {min_dec:.0f}% minimum).")
    if result["missing_patterns"]:
        top = sorted(result["missing_patterns"].items(), key=lambda kv: -len(kv[1]))[:3]
        parts.append(
            "Untaught patterns: "
            + "; ".join(f"{label} ({', '.join(words[:4])})" for label, words in top)
            + ". Replace these words or teach the pattern first."
        )
    if result["irregular_words"]:
        parts.append(
            "Irregular words not yet taught as heart words: "
            + ", ".join(result["irregular_words"][:8])
            + ". Pre-teach them as heart words or replace them."
        )
    if result["not_in_dictionary_words"]:
        parts.append("Check by hand (not in the pronunciation dictionary): " + ", ".join(result["not_in_dictionary_words"][:8]) + ".")
    if cueing:
        parts.append(f"{len(cueing)} three-cueing prompt(s) found; see cueing_flags for decoding-focused replacements.")
    return " ".join(parts)


async def verify_decodable_text(
    text: str,
    grade_level: str,
    unit: str = "1",
    target_pct: float = 90.0,
    min_decodable_pct: float | None = None,
    taught_gpcs: list[str] | None = None,
    taught_heart_words: list[str] | None = None,
    client: SoRClient | None = None,  # kept for interface compatibility; analysis is local
    settings: Settings | None = None,
) -> dict[str, Any]:
    """MCP entry point: verify decodability (local, deterministic)."""
    return check_decodability(
        text,
        grade_level,
        unit=unit,
        target_pct=target_pct,
        min_decodable_pct=min_decodable_pct,
        taught_gpcs=taught_gpcs,
        taught_heart_words=taught_heart_words,
    )
