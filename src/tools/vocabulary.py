"""Vocabulary tier classification tool.

Classifies words into Beck, McKeown & Kucan's (2013) three-tier framework:
  Tier 1: Basic, high-frequency conversational words.
  Tier 2: High-utility academic words across domain areas.
  Tier 3: Domain-specific, low-frequency words.
"""

from __future__ import annotations

import re
from collections import Counter
from typing import Any

TIER_2_PATTERNS: dict[str, list[str]] = {
    "analyze": ["analyze", "analysis", "analyst", "analytic", "analytical"],
    "approach": ["approach", "approachable", "approaching"],
    "assess": ["assess", "assessment", "assessing", "assessed"],
    "assume": ["assume", "assumed", "assuming", "assumption"],
    "concept": ["concept", "conception", "concepts", "conceptual"],
    "context": ["context", "contexts", "contextual"],
    "create": ["create", "created", "creating", "creation", "creative"],
    "data": ["data", "database", "dataset"],
    "define": ["define", "defined", "defines", "defining", "definition"],
    "evidence": ["evidence", "evident", "evidently"],
    "identify": ["identify", "identified", "identification"],
    "indicate": ["indicate", "indicated", "indication"],
    "interpret": ["interpret", "interpretation", "interpreted"],
    "method": ["method", "methodical", "methods"],
    "process": ["process", "processed", "processes", "processing"],
    "require": ["require", "required", "requirement"],
    "research": ["research", "researched", "researcher"],
    "structure": ["structure", "structured", "structures"],
    "theory": ["theory", "theoretical", "theories"],
    "vary": ["vary", "varied", "varies", "variety", "various"],
}


def classify_text(text: str, domain: str | None = None) -> dict[str, Any]:
    """Classify all words in a text passage into Tier 1, Tier 2, and Tier 3.

    Args:
        text: Passage text.
        domain: Content area ('science', 'math', 'social_studies', 'ela').

    Returns:
        Dict with tier counts, percentages, and lists of words by tier.
    """
    if not text or not text.strip():
        return {"error": "No text provided for classification", "total_words": 0}

    raw_words = re.findall(r"[a-zA-Z]+(?:'[a-zA-Z]+)?", text.lower())
    if not raw_words:
        return {"error": "No recognizable words found", "total_words": 0}

    total_words = len(raw_words)
    word_counts = Counter(raw_words)

    db_words: dict[str, dict[str, Any]] = {}
    try:
        from db.database import get_connection
        conn = get_connection()
        rows = conn.execute(
            "SELECT word, tier, frequency, grade FROM vocabulary_corpus"
        ).fetchall()
        for r in rows:
            db_words[r[0].lower()] = {
                "word": r[0],
                "tier": r[1],
                "frequency": r[2],
                "grade_level": "K" if r[3] == 0 else str(r[3]),
            }
    except Exception:
        pass

    tier1: list[dict[str, Any]] = []
    tier2: list[dict[str, Any]] = []
    tier3: list[dict[str, Any]] = []

    for word, count in word_counts.most_common():
        if word in db_words:
            entry = db_words[word]
            item = {"word": word, "count": count, "grade_level": entry["grade_level"]}
            if entry["tier"] == 1:
                tier1.append(item)
            elif entry["tier"] == 2:
                tier2.append(item)
            else:
                tier3.append(item)
        else:
            is_t2 = False
            for base, variants in TIER_2_PATTERNS.items():
                if word in variants or word == base:
                    tier2.append({"word": word, "count": count, "grade_level": "3-5"})
                    is_t2 = True
                    break
            if not is_t2:
                if len(word) <= 4 or count > 2:
                    tier1.append({"word": word, "count": count, "grade_level": "K-2"})
                else:
                    tier3.append({"word": word, "count": count, "grade_level": "3-5"})

    t1_count = sum(w["count"] for w in tier1)
    t2_count = sum(w["count"] for w in tier2)
    t3_count = sum(w["count"] for w in tier3)

    rec = (
        f"Focus direct instruction on the {len(tier2)} Tier 2 words identified. "
        "Tier 2 words provide the highest instructional leverage across domains."
    )

    return {
        "total_words": total_words,
        "unique_words": len(word_counts),
        "domain": domain or "general",
        "tier_counts": {
            "tier_1": t1_count,
            "tier_2": t2_count,
            "tier_3": t3_count,
        },
        "tier_summary": {
            "tier_1": {"count": t1_count, "pct": round(t1_count / total_words * 100, 1)},
            "tier_2": {"count": t2_count, "pct": round(t2_count / total_words * 100, 1)},
            "tier_3": {"count": t3_count, "pct": round(t3_count / total_words * 100, 1)},
        },
        "tier_1_words": tier1,
        "tier_2_words": tier2,
        "tier_3_words": tier3,
        "recommendation": rec,
        "instructional_recommendation": rec,
    }


def classify_vocabulary(text: str, domain: str | None = None) -> dict[str, Any]:
    """Alias for classify_text."""
    return classify_text(text=text, domain=domain)


def _decodability_info(word: str, grade: str | None) -> dict[str, Any]:
    """Decodability from the scope-aware engine (same logic as verify_decodable_text)."""
    from src.engine.decoder import analyze_word
    from src.engine.gpc import ALL_GPC_IDS
    from src.engine.scope_sequence import GRADE_ORDER, load_sequence, normalize_grade, resolve_scope

    info: dict[str, Any] = {}
    overall = analyze_word(word, ALL_GPC_IDS)
    info["decoding_status"] = (
        "decodable_with_catalogued_patterns" if overall["status"] == "decodable" else overall["status"]
    )
    info["breakdown"] = overall["breakdown"]

    first = None
    seq = load_sequence()
    for g in GRADE_ORDER:
        for u in range(1, len(seq.get(g, [])) + 1):
            scope = resolve_scope(g, u)
            if analyze_word(word, scope["taught_gpcs"])["status"] == "decodable":
                first = {"grade": g, "unit": u, "unit_title": scope["unit_title"]}
                break
        if first:
            break
    info["first_decodable_at"] = first

    g = normalize_grade(grade) if grade else None
    if g:
        end_scope = resolve_scope(g, 99)
        r = analyze_word(word, end_scope["taught_gpcs"], end_scope["heart_words"])
        info["decodable"] = r["status"] == "decodable"
        info["status_by_end_of_grade"] = r["status"]
        info["missing_patterns"] = r["missing_patterns"]
    else:
        info["decodable"] = None
        info["note"] = "Pass grade to check decodability against that grade's scope; see first_decodable_at."
    return info


def match_word(word: str, grade: str | None = None) -> dict[str, Any]:
    """Look up a single word: vocabulary tier plus scope-aware decodability.

    Decodability comes from the same engine as verify_decodable_text, judged
    against the (default or SOR_SCOPE_PATH) scope by the end of ``grade``.
    """
    word_clean = word.strip().lower()
    result: dict[str, Any] = {"word": word_clean}
    tier_found = False
    try:
        from db.database import get_connection
        conn = get_connection()
        query = "SELECT word, tier, frequency, grade FROM vocabulary_corpus WHERE LOWER(word) = ? ORDER BY grade LIMIT 1"
        row = conn.execute(query, [word_clean]).fetchone()
        if row:
            result.update({
                "tier": row[1],
                "frequency": row[2],
                "grade_level": "K" if row[3] == 0 else str(row[3]),
                "found": True,
            })
            tier_found = True
    except Exception:
        pass

    if not tier_found:
        for base, variants in TIER_2_PATTERNS.items():
            if word_clean in variants or word_clean == base:
                result.update({"tier": 2, "found": True, "note_tier": "Derived from academic word list"})
                tier_found = True
                break
    if not tier_found:
        result.update({
            "tier": None,
            "found": False,
            "note_tier": "Not in the vocabulary corpus; tier not determined.",
        })

    result.update(_decodability_info(word_clean, grade))
    return result
