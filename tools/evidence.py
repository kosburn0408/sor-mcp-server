"""Evidence-based research lookup tool.

Queries the embedded research database for WWC (What Works Clearinghouse),
BEE (Best Evidence Encyclopedia), and NRP (National Reading Panel) findings.

Theoretical basis: Evidence-based practice requires grounding instructional
decisions in rigorous research. This tool maps queries to the five pillars
of reading (NRP, 2000), the Simple View of Reading (Gough & Tunmer, 1986),
and Scarborough's Reading Rope (2001).
"""

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
    "foundational skills": ["phonemic_awareness", "phonics", "fluency"],
    "five pillars": ["phonemic_awareness", "phonics", "fluency", "vocabulary", "comprehension"],
}


def search_evidence(topic: str) -> dict[str, Any]:
    """Search the evidence database for research related to a topic.

    Maps natural language topics to framework pillars and returns matching
    research papers with effect sizes and findings.

    Args:
        topic: A natural language query (e.g., 'phonics', 'fluency',
               'simple view of reading', 'phonemic awareness').

    Returns:
        Dictionary with matching papers, framework context, and summary statistics.
    """
    if not topic or not topic.strip():
        return {"error": "No topic provided for search", "results": []}

    topic_lower = topic.lower().strip()

    # Determine which framework to search
    frameworks: list[str] = []
    for key, values in FRAMEWORK_MAP.items():
        if key in topic_lower:
            frameworks.extend(values)
            break

    if not frameworks:
        # Fall back to full-text search across all fields
        frameworks = []

    from db.database import get_connection
    conn = get_connection()

    if frameworks:
        placeholders = ",".join(["?"] * len(frameworks))
        query = f"""
            SELECT id, title, authors, year, framework, finding, effect_size, source, url
            FROM research_papers
            WHERE framework IN ({placeholders})
            ORDER BY effect_size DESC
        """
        rows = conn.execute(query, frameworks).fetchall()
    else:
        query = """
            SELECT id, title, authors, year, framework, finding, effect_size, source, url
            FROM research_papers
            WHERE LOWER(title) LIKE ? OR LOWER(finding) LIKE ?
            ORDER BY effect_size DESC
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
        })

    # Compute summary stats
    if papers:
        effect_sizes = [p["effect_size"] for p in papers if p["effect_size"] is not None]
        avg_effect = round(sum(effect_sizes) / len(effect_sizes), 2) if effect_sizes else None
    else:
        avg_effect = None

    # Get relevant frameworks for context
    framework_contexts = _get_framework_context(frameworks)

    return {
        "topic": topic,
        "matched_pillars": frameworks if frameworks else ["full_text_search"],
        "total_papers": len(papers),
        "average_effect_size": avg_effect,
        "papers": papers,
        "framework_context": framework_contexts,
        "interpretation": _interpret_effect_size(avg_effect) if avg_effect is not None else None,
    }


def _get_framework_context(frameworks: list[str]) -> list[dict[str, str]]:
    """Get theoretical framework descriptions for context."""
    from db.database import get_connection
    conn = get_connection()

    context = []
    # Always include core frameworks for reference
    core = ["Simple View of Reading", "Scarborough's Reading Rope", "National Reading Panel Report"]
    if frameworks:
        for fw_name in core:
            row = conn.execute(
                "SELECT name, description FROM theoretical_frameworks WHERE name = ?",
                [fw_name],
            ).fetchone()
            if row:
                context.append({"name": row[0], "description": row[1]})

    return context


def _interpret_effect_size(d: float) -> str:
    """Interpret Cohen's d effect size for educational research."""
    if d < 0:
        return "Negative effect — intervention was harmful or counterproductive."
    elif d < 0.20:
        return f"Small effect (d={d}) — statistically significant but may have limited practical impact. Consider cost-benefit."
    elif d < 0.50:
        return f"Moderate effect (d={d}) — likely to produce meaningful improvement. WWC threshold for 'effective' is typically d≥0.25."
    elif d < 0.80:
        return f"Large effect (d={d}) — strong evidence of effectiveness. This level of impact is educationally meaningful."
    else:
        return f"Very large effect (d={d}) — exceptional impact. Verify study quality and replicability."


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
    """List evidence-based reading assessments.

    Args:
        tool_type: Optional filter by assessment type
                   ('screener', 'diagnostic', 'progress_monitoring', 'outcome').

    Returns:
        Dictionary with assessment details.
    """
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

    # Group by type
    by_type: dict[str, int] = {}
    for a in assessments:
        by_type[a["type"]] = by_type.get(a["type"], 0) + 1

    return {
        "total": len(assessments),
        "by_type": by_type,
        "assessments": assessments,
        "assessment_framework_note": (
            "Effective reading instruction uses a Multi-Tiered System of Supports "
            "(MTSS/RTI) framework: universal screening → diagnostic assessment → "
            "progress monitoring → outcome evaluation. WWC recommends using "
            "screening data to identify at-risk students and progress monitoring "
            "to evaluate intervention effectiveness."
        ),
    }


def align_standards(text_description: str, state: str = "CCSS", grade: str | None = None) -> dict[str, Any]:
    """Find standards that align with a text or skill description.

    Args:
        text_description: Natural language description of the text or skill.
        state: State standards code ('CCSS', 'TEXAS', 'FLORIDA', 'NY').
        grade: Optional grade filter ('K' through '5').

    Returns:
        Matching standards with framework alignment.
    """
    if not text_description or not text_description.strip():
        return {"error": "No description provided", "matches": []}

    from db.database import get_connection
    conn = get_connection()

    # Try to map the description to a framework pillar
    desc_lower = text_description.lower()
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
        params = [state] + matched_frameworks
    else:
        query = """
            SELECT state, grade, code, description, framework
            FROM standards
            WHERE state = ? AND LOWER(description) LIKE ?
        """
        # Extract keywords for search
        keywords = " ".join(re.findall(r"[a-zA-Z]{4,}", desc_lower))
        params = [state, f"%{keywords[:50]}%"]

    if grade:
        query += " AND grade = ?"
        params.append(grade)

    rows = conn.execute(query, params).fetchall()

    if not rows:
        # Broader search — return all standards for the state+grade
        fallback_query = "SELECT state, grade, code, description, framework FROM standards WHERE state = ?"
        fallback_params = [state]
        if grade:
            fallback_query += " AND grade = ?"
            fallback_params.append(grade)
        rows = conn.execute(fallback_query + " LIMIT 20", fallback_params).fetchall()

    matches = []
    for row in rows:
        matches.append({
            "state": row[0],
            "grade": row[1],
            "code": row[2],
            "description": row[3],
            "framework": row[4],
        })

    return {
        "description": text_description,
        "state": state,
        "grade_filter": grade,
        "total_matches": len(matches),
        "matches": matches,
        "framework_note": (
            "Standards alignment supports the Simple View of Reading by ensuring "
            "instruction addresses both word recognition and language comprehension "
            "strands. Scarborough's Rope: each standard maps to one or more "
            "interconnected reading strands."
        ),
    }


if __name__ == "__main__":
    import json, re
    result = search_evidence("phonics instruction")
    print(json.dumps(result, indent=2))
