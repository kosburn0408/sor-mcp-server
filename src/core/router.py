"""Dynamic meta-tool router for the Science of Reading MCP server.

Implements query_sor_curriculum — a single entry point that routes to
appropriate internal tools based on the query shape. Keeps system prompt
context lean by returning only essential curriculum data.

Route map:
    strand=phonology + target_phoneme → scope sequence + remediation lookup
    strand=phonology + syllable_type → scope sequence with syllable rules
    strand=morphology → morphology scope sequence
    strand=vocabulary → vocabulary tier + evidence lookup
    strand=fluency → fluency scope
    strand=comprehension → comprehension scope
    standard_state set → standards alignment + scope
"""

from __future__ import annotations

from typing import Any

from src.core.errors import SoRErrorCode, format_error
from src.schemas.curriculum import (
    CurriculumQuery,
    CurriculumResult,
    GradeLevel,
    Strand,
    SyllableType,
)
from src.tools.diagnostics import get_scope_sequence


def query_sor_curriculum(
    grade_level: str,
    strand: str | None = None,
    target_phoneme: str | None = None,
    syllable_type: str | None = None,
    standard_state: str | None = None,
) -> dict[str, Any]:
    """Dynamic meta-tool: route to appropriate internal tool and return compact curriculum data.

    This is the single entry point for curriculum queries — it resolves the best
    internal handler based on which parameters are populated and returns a lean
    JSON payload suitable for system prompt context.

    Args:
        grade_level: Target grade level (K-5).
        strand: Literacy strand (phonology, morphology, vocabulary, fluency, comprehension).
        target_phoneme: Optional specific phoneme to look up.
        syllable_type: Optional syllable type for explicit instruction.
        standard_state: Optional state standards code.

    Returns:
        Compact JSON: {strand, grade, concepts[], prerequisites[], next_steps[]}.
    """
    # ── Validate grade level ──────────────────────────────────────────
    valid_grades = {"K", "1", "2", "3", "4", "5"}
    if grade_level not in valid_grades:
        return format_error(
            SoRErrorCode.ERR_INVALID_GRADE_BAND,
            detail=grade_level,
        )

    # ── Validate strand ───────────────────────────────────────────────
    valid_strands = {"phonology", "morphology", "vocabulary", "fluency", "comprehension"}
    resolved_strand = strand or "phonology"
    if resolved_strand not in valid_strands:
        return format_error(
            SoRErrorCode.ERR_INVALID_INPUT,
            detail=f"Unknown strand '{strand}'. Valid: {', '.join(sorted(valid_strands))}",
        )

    # ── Validate syllable type ────────────────────────────────────────
    valid_syllable_types = {"closed", "open", "VCe", "r_controlled", "vowel_team", "c_le"}
    if syllable_type and syllable_type not in valid_syllable_types:
        return format_error(
            SoRErrorCode.ERR_INVALID_SYLLABLE_TYPE,
            detail=syllable_type,
        )

    # ── Route to internal handler ─────────────────────────────────────
    tool_routed = "scope_sequence_lookup"
    scope = get_scope_sequence(grade_level, resolved_strand)

    # If phonology + phoneme, add remediation lookup
    remediation_code: str | None = None
    if resolved_strand == "phonology" and target_phoneme:
        tool_routed = "phoneme_remediation_lookup"
        remediation_code = _phoneme_to_remediation(target_phoneme)

    # If phonology + syllable type, enrich with syllable rules
    if resolved_strand == "phonology" and syllable_type:
        tool_routed = "syllable_type_scope"
        from src.resources.frameworks import SYLLABLE_DIVISION_RULES
        syllable_rule = SYLLABLE_DIVISION_RULES.get(syllable_type, "")
        if syllable_rule:
            scope["concepts"] = list(scope.get("concepts", [])) + [f"Syllable type: {syllable_type} — {syllable_rule}"]

    # If state standards requested, add standards
    matched_standards: list[str] = []
    if standard_state:
        tool_routed = "standards_scope_lookup"
        matched_standards = _lookup_standards(grade_level, resolved_strand, standard_state)

    return {
        "strand": resolved_strand,
        "grade": grade_level,
        "concepts": scope.get("concepts", []),
        "phonemes": scope.get("phonemes", []),
        "syllable_types": scope.get("syllable_types", []),
        "prerequisites": scope.get("prerequisites", []),
        "next_steps": scope.get("next_steps", []),
        "matched_standards": matched_standards,
        "remediation_code": remediation_code,
        "tool_routed_to": tool_routed,
    }


# ── Internal Routing Helpers ────────────────────────────────────────────────


def _phoneme_to_remediation(phoneme: str) -> str | None:
    """Map a target phoneme to a remediation deficit code."""
    phoneme_lower = phoneme.lower().strip()
    mapping: dict[str, str] = {
        "/a/": "cvc_short_a",
        "short a": "cvc_short_a",
        "/e/": "cvc_mixed",
        "short e": "cvc_mixed",
        "/i/": "cvc_mixed",
        "short i": "cvc_mixed",
        "/o/": "cvc_mixed",
        "short o": "cvc_mixed",
        "/u/": "cvc_mixed",
        "short u": "cvc_mixed",
        "/ā/": "cvce_silent_e",
        "long a": "cvce_silent_e",
        "/ē/": "cvce_silent_e",
        "long e": "cvce_silent_e",
        "/ī/": "cvce_silent_e",
        "long i": "cvce_silent_e",
        "/ō/": "cvce_silent_e",
        "long o": "cvce_silent_e",
        "/sh/": "consonant_digraphs",
        "/ch/": "consonant_digraphs",
        "/th/": "consonant_digraphs",
        "/ar/": "r_controlled",
        "/or/": "r_controlled",
        "/er/": "r_controlled",
        "blends": "consonant_blends",
        "silent e": "cvce_silent_e",
    }
    return mapping.get(phoneme_lower)


def _lookup_standards(grade: str, strand: str, state: str) -> list[str]:
    """Look up matching standards codes for a grade/strand/state combo."""
    from db.database import get_connection

    pillar_map = {
        "phonology": ["phonemic_awareness", "phonics"],
        "morphology": ["phonics"],
        "vocabulary": ["vocabulary"],
        "fluency": ["fluency"],
        "comprehension": ["comprehension"],
    }
    pillars = pillar_map.get(strand, ["phonics"])

    conn = get_connection()
    placeholders = ",".join(["?"] * len(pillars))
    query = f"""
        SELECT code FROM standards
        WHERE UPPER(state) = ? AND grade = ? AND framework IN ({placeholders})
        LIMIT 5
    """
    params = [state.upper(), grade] + pillars
    rows = conn.execute(query, params).fetchall()
    return [row[0] for row in rows]
