"""Evidence-based research & standards tools.

Grounds reading instruction decisions in WWC, BEE, and NRP empirical research
embedded in DuckDB, with optional upstream API fallbacks.
"""

from __future__ import annotations

import re
import urllib.parse
from typing import Any

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
    "foundational skills": ["phonemic_awareness", "phonics", "fluency", "foundational_skills"],
    "active view": ["simple_view"],
    "orton": ["phonics"],
    "multisensory": ["phonics"],
    "five pillars": ["phonemic_awareness", "phonics", "fluency", "vocabulary", "comprehension"],
}

STATE_ALIASES: dict[str, str] = {
    "GEORGIA": "GA", "GA": "GA",
    "CALIFORNIA": "CA", "CA": "CA",
    "TEXAS": "TX", "TX": "TX",
    "FLORIDA": "FL", "FL": "FL",
    "NEW YORK": "NY", "NY": "NY", "NEW_YORK": "NY",
    "NORTH CAROLINA": "NC", "NC": "NC",
    "OHIO": "OH", "OH": "OH",
    "PENNSYLVANIA": "PA", "PA": "PA",
    "VIRGINIA": "VA", "VA": "VA",
    "ILLINOIS": "IL", "IL": "IL",
    "COMMON CORE": "CCSS", "CCSS": "CCSS",
}


def search_evidence(topic: str) -> dict[str, Any]:
    """Search the evidence database for research related to a topic."""
    if not topic or not topic.strip():
        return {"error": "No topic provided for search", "results": []}

    topic_lower = topic.lower().strip()

    frameworks: list[str] = []
    for key, values in FRAMEWORK_MAP.items():
        if key in topic_lower:
            frameworks.extend(values)
            break

    from db.database import get_connection
    conn = get_connection()

    if frameworks:
        placeholders = ",".join(["?"] * len(frameworks))
        query = f"""
            SELECT id, title, authors, year, framework, finding, effect_size, source, url,
                   verification, notes
            FROM research_papers
            WHERE framework IN ({placeholders})
            ORDER BY effect_size DESC NULLS LAST, year DESC
        """
        rows = conn.execute(query, frameworks).fetchall()
    else:
        query = """
            SELECT id, title, authors, year, framework, finding, effect_size, source, url,
                   verification, notes
            FROM research_papers
            WHERE LOWER(title) LIKE ? OR LOWER(finding) LIKE ?
            ORDER BY effect_size DESC NULLS LAST, year DESC
        """
        search_term = f"%{topic_lower}%"
        rows = conn.execute(query, [search_term, search_term]).fetchall()

    papers = []
    for row in rows:
        papers.append({
            "id": row[0],
            "title": row[1],
            "authors": row[2],
            "year": row[3],
            "framework": row[4],
            "finding": row[5],
            "effect_size": row[6],
            "source": row[7],
            "url": row[8],
            "verification": row[9],
            "notes": row[10],
        })

    # Only average effect sizes that were checked against their source.
    effect_sizes = [
        p["effect_size"] for p in papers
        if p["effect_size"] is not None and p["verification"] == "verified"
    ]
    avg_effect = round(sum(effect_sizes) / len(effect_sizes), 2) if effect_sizes else None

    framework_contexts = _get_framework_context(frameworks)

    return {
        "topic": topic,
        "matched_pillars": frameworks if frameworks else ["full_text_search"],
        "total_papers": len(papers),
        "average_effect_size": avg_effect,
        "effect_sizes_averaged": len(effect_sizes),
        "evidence_policy": (
            "Effect sizes are stored only when checked against the source. Entries with no "
            "effect size (for example WWC practice guides, which report evidence levels) are "
            "still listed. Effect sizes from different designs are not directly comparable."
        ),
        "papers": papers,
        "framework_context": framework_contexts,
        "interpretation": _interpret_effect_size(avg_effect) if avg_effect is not None else None,
    }


def _get_framework_context(frameworks: list[str]) -> list[dict[str, str]]:
    """Get theoretical framework descriptions for context."""
    from db.database import get_connection
    conn = get_connection()

    context = []
    core = ["Simple View of Reading", "Scarborough's Reading Rope", "National Reading Panel Report"]
    for fw_name in core:
        try:
            row = conn.execute(
                "SELECT name, description FROM theoretical_frameworks WHERE name = ?",
                [fw_name],
            ).fetchone()
            if row:
                context.append({"name": row[0], "description": row[1]})
        except Exception:
            pass

    return context


def _interpret_effect_size(d: float) -> str:
    """Describe a standardized mean difference using Cohen's conventional benchmarks."""
    if d < 0:
        return "Negative effect: the comparison condition did better."
    if d < 0.20:
        return f"Negligible effect (d = {d})."
    if d < 0.50:
        return f"Small effect (d = {d}). Small effects can still matter at scale in education."
    if d < 0.80:
        return f"Moderate effect (d = {d})."
    return f"Large effect (d = {d}). Treat very large effects with caution; they often come from narrow, researcher-made measures."


def list_frameworks() -> dict[str, Any]:
    """List all theoretical frameworks in the database."""
    from db.database import get_connection
    conn = get_connection()

    rows = conn.execute(
        "SELECT name, authors, year, description, components, url "
        "FROM theoretical_frameworks ORDER BY year"
    ).fetchall()

    frameworks = []
    for row in rows:
        frameworks.append({
            "name": row[0],
            "authors": row[1],
            "year": row[2],
            "description": row[3],
            "components": row[4].split(", ") if row[4] else [],
            "url": row[5],
        })

    return {
        "total_frameworks": len(frameworks),
        "frameworks": frameworks,
        "five_pillars": [
            {"pillar": "Phonemic Awareness", "description": "Ability to hear, identify, and manipulate individual sounds in spoken words."},
            {"pillar": "Phonics", "description": "Relationship between letters (graphemes) and sounds (phonemes) in written language."},
            {"pillar": "Fluency", "description": "Ability to read text accurately, quickly, and with proper expression."},
            {"pillar": "Vocabulary", "description": "Knowledge of word meanings needed for comprehension."},
            {"pillar": "Comprehension", "description": "Ability to understand, remember, and communicate meaning from text."},
        ],
    }


def list_assessments(tool_type: str | None = None) -> dict[str, Any]:
    """List evidence-based reading assessments."""
    from db.database import get_connection
    conn = get_connection()

    if tool_type:
        rows = conn.execute(
            "SELECT id, name, type, grade_range, skills_assessed, administration, url "
            "FROM assessments WHERE type = ? ORDER BY name",
            [tool_type],
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT id, name, type, grade_range, skills_assessed, administration, url "
            "FROM assessments ORDER BY type, name"
        ).fetchall()

    assessments = []
    for row in rows:
        assessments.append({
            "id": row[0],
            "name": row[1],
            "type": row[2],
            "grade_range": row[3],
            "skills_assessed": row[4],
            "administration": row[5],
            "url": row[6],
        })

    by_type: dict[str, int] = {}
    for a in assessments:
        by_type[a["type"]] = by_type.get(a["type"], 0) + 1

    return {
        "total": len(assessments),
        "by_type": by_type,
        "assessments": assessments,
        "assessment_framework_note": (
            "Effective reading instruction uses an MTSS framework: "
            "universal screening → diagnostic assessment → progress monitoring → outcome evaluation."
        ),
    }


def align_standards(description: str, state: str = "GA", grade: str | None = None) -> dict[str, Any]:
    """Find academic standards aligned to a text or skill description via Standards Satchel (CASE® Exchange)."""
    if not description or not description.strip():
        return {"error": "No description provided", "matches": []}

    state_input = str(state).strip().upper()
    state_code = STATE_ALIASES.get(state_input, state_input)

    live_status = "not_attempted"
    if state_code == "GA":
        live_result, live_status = _georgia_live_matches(description, grade)
        if live_result is not None:
            return live_result

    from db.database import get_connection
    conn = get_connection()

    desc_lower = description.lower()
    matched_frameworks = []
    for key, values in FRAMEWORK_MAP.items():
        if key in desc_lower:
            matched_frameworks.extend(values)

    if matched_frameworks:
        placeholders = ",".join(["?"] * len(matched_frameworks))
        query = f"""
            SELECT state, grade, code, description, framework
            FROM standards
            WHERE state = ? AND framework IN ({placeholders})
        """
        params: list[Any] = [state_code] + matched_frameworks
    else:
        query = """
            SELECT state, grade, code, description, framework
            FROM standards
            WHERE state = ? AND LOWER(description) LIKE ?
        """
        keywords = " ".join(re.findall(r"[a-zA-Z]{4,}", desc_lower))
        params = [state_code, f"%{keywords[:50]}%"]

    if grade:
        query += " AND grade = ?"
        params.append(grade)

    rows = conn.execute(query, params).fetchall()

    is_crosswalk = False
    if not rows:
        fallback_query = "SELECT state, grade, code, description, framework FROM standards WHERE state = 'CCSS'"
        fallback_params: list[Any] = []
        if grade:
            fallback_query += " AND grade = ?"
            fallback_params.append(grade)
        rows = conn.execute(fallback_query + " LIMIT 20", fallback_params).fetchall()
        is_crosswalk = True

    matches = []
    for row in rows:
        code = row[2]
        encoded_code = urllib.parse.quote(code)
        matches.append({
            "state": state_code if is_crosswalk else row[0],
            "grade": row[1],
            "code": code,
            "description": row[3],
            "framework": row[4],
            "provider": "Common Good Learning Tools",
            "portal": "Standards Satchel",
            "url": f"https://rosetta.commongoodlt.com/#/search?q={encoded_code}",
            "exchange": "Satchel Rosetta Exchange (CASE® Format)",
            "is_crosswalk": is_crosswalk,
        })

    return {
        "description": description,
        "state": state_code,
        "grade_filter": grade,
        "source": "seeded_table",
        "live_case_status": live_status,
        "note": (
            "These come from a small seeded table that uses older Georgia code formats (ELAGSE...), "
            "not from the state's live CASE server. Check codes against Georgia's current ELA standards."
            if state_code == "GA" else
            "These come from a small seeded table, not a live CASE server."
        ),
        "satchel_rosetta_integration": {
            "portal": "Standards Satchel",
            "provider": "Common Good Learning Tools",
            "url": "https://rosetta.commongoodlt.com/",
            "format": "CASE® (Competencies & Academic Standards Exchange)",
            "case_api_base": "https://rosetta.commongoodlt.com/ims/case/v1p1/",
            "google_classroom_export": True,
        },
        "total_matches": len(matches),
        "matches": matches,
    }


def _georgia_live_matches(description: str, grade: str | None) -> tuple[dict[str, Any] | None, str]:
    """Search Georgia's current ELA standards on the state's CASE server.

    Returns (result, status). result is None when the live lookup is off, fails or finds
    nothing, in which case the caller falls back to the seeded table and reports status.
    """
    from src.client import georgia_case

    if not georgia_case.live_enabled():
        return None, "disabled"
    try:
        package = georgia_case.load_package()
    except georgia_case.GeorgiaCaseError as exc:
        return None, f"unavailable: {exc}"
    found = georgia_case.search_standards(package, description, grade)
    if not found:
        return None, "no_match_in_current_ela_standards"

    strand_names = {"F": "foundational_skills", "R": "reading", "W": "writing", "L": "language", "S": "speaking_listening"}
    matches = []
    for item in found:
        uri = item.get("uri") or f"{georgia_case._base_url()}/ims/case/v1p1/CFItems/{item.get('identifier')}"
        matches.append({
            "state": "GA",
            "grade": item["grade"],
            "code": item["code"],
            "description": item["statement"],
            "framework": strand_names.get(item["strand"], item["strand"].lower()),
            "item_type": item["item_type"],
            "identifier": item["identifier"],
            "case_item_uri": uri,
            "url": uri,
            "provider": "Georgia Department of Education",
            "portal": "Georgia CASE server",
            "is_crosswalk": False,
        })
    return {
        "description": description,
        "state": "GA",
        "grade_filter": grade,
        "source": "georgia_case_live" if package.get("fetched_from") == "live" else "georgia_case_disk_cache",
        "live_case_status": "ok",
        "standards_package": {
            "title": package["title"],
            "case_version": package["version"],
            "last_change": package["last_change"],
            "uri": package["package_uri"],
        },
        "note": (
            "Matched by keywords against Georgia's published ELA standards; confirm the best fit "
            "against the standard's full text before citing it."
        ),
        "total_matches": len(matches),
        "matches": matches,
    }, "ok"
