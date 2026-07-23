"""MCP Tool: lookup_competency — CASE standards competency lookup.

Bridges to GET /api/v1/standards/competency on sor.edtechlabs.dev.
"""

from __future__ import annotations

from typing import Any

from src.client.sor_client import SoRClient
from src.config import Settings
from src.errors import (
    SoRAPIErrorCode,
    format_api_error,
)
from src.schemas.api import StandardMatch


async def lookup_competency(
    skill: str,
    state: str = "GA",
    client: SoRClient | None = None,
    settings: Settings | None = None,
) -> dict[str, Any]:
    """Look up academic standards (CASE/state) for a phonics skill.

    Maps a skill like 'consonant_blends' or 'silent_e' to matching state
    and CASE framework standards. Results are cached for the configured TTL.

    Args:
        skill: Phonics skill (e.g., 'consonant_blends', 'silent_e', 'digraphs').
        state: State abbreviation (GA, CCSS, TX, FL, NY). Default: 'GA'.
        client: Optional pre-configured SoRClient.
        settings: Optional Settings.

    Returns:
        Dict with 'matches' array containing CASE GUIDs, state codes, grade,
        and descriptions.
    """
    if not skill or not skill.strip():
        return format_api_error(
            SoRAPIErrorCode.ERR_INVALID_INPUT,
            detail="skill is required",
        )

    valid_states = {"GA", "CCSS", "TX", "FL", "NY"}
    if state not in valid_states:
        return format_api_error(
            SoRAPIErrorCode.ERR_INVALID_INPUT,
            detail=f"unknown state '{state}'. Supported: {sorted(valid_states)}",
        )

    if client is None:
        client = SoRClient(settings or Settings())

    try:
        matches = await client.lookup_competency(skill, state)
        return {
            "status": "ok",
            "skill": skill,
            "state": state,
            "total_matches": len(matches),
            "matches": [
                {
                    "case_guid": m.case_guid,
                    "state_code": m.state_code,
                    "grade": m.grade,
                    "description": m.description,
                    "strand": m.strand,
                }
                for m in matches
            ],
            "source": "sor.edtechlabs.dev",
            "cached": True,
        }
    except Exception as exc:
        return format_api_error(
            SoRAPIErrorCode.ERR_UPSTREAM_REGISTRY_UNAVAILABLE,
            detail=str(exc),
        )


# ── Legacy CASE alignment (DuckDB-backed, kept for backward compat) ────

import re as _re  # noqa: E402


def align_standards_case(
    text_description: str,
    state: str = "CCSS",
    grade: str | None = None,
    output_format: str = "summary",
) -> dict[str, Any]:
    """Align a text or skill description with CASE standards (DuckDB-backed).

    Legacy function kept for backward compatibility with existing tools.
    Use lookup_competency for the new API-based approach.

    Args:
        text_description: Natural language description of the text or skill.
        state: State standards code (CCSS, TEXAS, FLORIDA, NY, GEORGIA).
        grade: Optional grade-level filter (K-5).
        output_format: 'summary' or 'case_jsonld'.

    Returns:
        StandardsAlignmentResult with matches and optional CASE bundle.
    """
    from src.core.errors import SoRErrorCode as _CoreCode, format_error as _fmt
    from src.schemas.standards import (
        CaseAssociation,
        CaseAssociationType,
        CaseCFItem,
        CaseStandardsBundle,
    )

    FRAMEWORK_MAP: dict[str, list[str]] = {
        "phonemic awareness": ["phonemic_awareness"],
        "phonemic": ["phonemic_awareness"],
        "phonics": ["phonics"],
        "decoding": ["phonics"],
        "fluency": ["fluency"],
        "vocabulary": ["vocabulary"],
        "comprehension": ["comprehension"],
        "simple view": ["simple_view"],
        "simple view of reading": ["simple_view"],
        "scarborough": ["rope"],
        "rope": ["rope"],
        "reading rope": ["rope"],
        "foundational skills": ["phonemic_awareness", "phonics", "fluency"],
        "five pillars": ["phonemic_awareness", "phonics", "fluency", "vocabulary", "comprehension"],
    }

    SUPPORTED_STATES: set[str] = {"CCSS", "TEXAS", "FLORIDA", "NY", "GEORGIA"}

    if not text_description or not text_description.strip():
        return {"error": "No description provided", "error_code": "ERR_INVALID_INPUT"}

    state_upper = state.upper().strip()
    if state_upper not in SUPPORTED_STATES:
        return _fmt(
            _CoreCode.ERR_UNKNOWN_STANDARD_SET,
            detail=state,
        )

    desc_lower = text_description.lower()
    matched_frameworks: list[str] = []
    for key, values in FRAMEWORK_MAP.items():
        if key in desc_lower:
            matched_frameworks.extend(values)
            break

    try:
        from db.database import get_connection
        conn = get_connection()

        if matched_frameworks:
            placeholders = ",".join(["?"] * len(matched_frameworks))
            query = f"""
                SELECT state, grade, code, description, framework
                FROM standards
                WHERE UPPER(state) = ? AND framework IN ({placeholders})
            """
            params: list[str] = [state_upper] + matched_frameworks
        else:
            query = """
                SELECT state, grade, code, description, framework
                FROM standards
                WHERE UPPER(state) = ? AND LOWER(description) LIKE ?
            """
            keywords = " ".join(_re.findall(r"[a-zA-Z]{4,}", desc_lower))
            params = [state_upper, f"%{keywords[:50]}%"]

        if grade:
            query += " AND grade = ?"
            params.append(grade)

        rows = conn.execute(query, params).fetchall()

        if not rows:
            fallback_query = (
                "SELECT state, grade, code, description, framework "
                "FROM standards WHERE UPPER(state) = ?"
            )
            fallback_params = [state_upper]
            if grade:
                fallback_query += " AND grade = ?"
                fallback_params.append(grade)
            rows = conn.execute(fallback_query + " LIMIT 20", fallback_params).fetchall()
    except Exception:
        rows = []

    matches: list[dict[str, Any]] = []
    cf_items: list[CaseCFItem] = []
    associations: list[CaseAssociation] = []

    for i, row in enumerate(rows):
        state_code, grade_val, std_code, desc, framework = row[0], row[1], row[2], row[3], row[4]
        match_entry = {
            "state": state_code,
            "grade": grade_val,
            "code": std_code,
            "description": desc,
            "framework": framework,
        }
        matches.append(match_entry)

        cf_items.append(CaseCFItem(
            identifier=f"https://sor-mcp/case/items/{state_code.lower()}-{std_code.replace('.', '-').lower()}",
            uri=f"urn:case:{state_code.lower()}:{grade_val}:{std_code}",
            full_statement=desc,
            human_coding_scheme=std_code,
            grade=grade_val,
            subject="ELA",
            pillar=framework,
            strand="Reading Foundational" if framework in ("phonemic_awareness", "phonics", "fluency") else "Language",
        ))

        if i > 0 and row[1] == rows[i - 1][1]:
            prev = cf_items[-2]
            curr = cf_items[-1]
            associations.append(CaseAssociation(
                origin_node_uri=curr.uri,
                destination_node_uri=prev.uri,
                association_type=CaseAssociationType.IS_RELATED_TO,
            ))

    bundle: dict[str, Any] | None = None
    if output_format == "case_jsonld":
        bundle = CaseStandardsBundle(
            title=f"SoR Standards Alignment — {state_upper}",
            description=f"Science of Reading standards from {state_upper} aligned to '{text_description[:80]}'",
            cf_items=cf_items,
            cf_associations=associations,
        ).model_dump()

    return {
        "request_grade": grade,
        "request_state": state_upper,
        "total_matches": len(matches),
        "matches": matches,
        "case_bundle": bundle,
        "framework_note": (
            "Standards alignment supports the Simple View of Reading by ensuring "
            "instruction addresses both word recognition and language comprehension "
            "strands. Scarborough's Rope: each standard maps to one or more "
            "interconnected reading strands."
        ),
    }
