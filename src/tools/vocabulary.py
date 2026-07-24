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
            "SELECT word, tier, frequency_per_million, decodable, grade_level FROM vocabulary_corpus"
        ).fetchall()
        for r in rows:
            db_words[r[0].lower()] = {
                "word": r[0],
                "tier": r[1],
                "frequency": r[2],
                "decodable": bool(r[3]),
                "grade_level": r[4],
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

    return {
        "total_words": total_words,
        "unique_words": len(word_counts),
        "domain": domain or "general",
        "tier_summary": {
            "tier_1": {"count": t1_count, "pct": round(t1_count / total_words * 100, 1)},
            "tier_2": {"count": t2_count, "pct": round(t2_count / total_words * 100, 1)},
            "tier_3": {"count": t3_count, "pct": round(t3_count / total_words * 100, 1)},
        },
        "tier_1_words": tier1,
        "tier_2_words": tier2,
        "tier_3_words": tier3,
        "instructional_recommendation": (
            f"Focus direct instruction on the {len(tier2)} Tier 2 words identified. "
            "Tier 2 words provide the highest instructional leverage across domains."
        ),
    }


def classify_vocabulary(text: str, domain: str | None = None) -> dict[str, Any]:
    """Alias for classify_text."""
    return classify_text(text=text, domain=domain)


def match_word(word: str, grade: str | None = None) -> dict[str, Any]:
    """Look up a single word in the vocabulary corpus.

    Args:
        word: Word to search.
        grade: Optional grade filter.

    Returns:
        Dict with tier, decodability, frequency, and grade level.
    """
    word_clean = word.strip().lower()
    try:
        from db.database import get_connection
        conn = get_connection()
        query = "SELECT word, tier, frequency_per_million, decodable, grade_level FROM vocabulary_corpus WHERE LOWER(word) = ?"
        row = conn.execute(query, [word_clean]).fetchone()
        if row:
            return {
                "word": row[0],
                "tier": row[1],
                "frequency_per_million": row[2],
                "decodable": bool(row[3]),
                "grade_level": row[4],
                "found": True,
            }
    except Exception:
        pass

    for base, variants in TIER_2_PATTERNS.items():
        if word_clean in variants or word_clean == base:
            return {
                "word": word_clean,
                "tier": 2,
                "frequency_per_million": 100.0,
                "decodable": True,
                "grade_level": grade or "3-5",
                "found": True,
                "note": "Derived from academic word list",
            }

    return {
        "word": word_clean,
        "tier": 1 if len(word_clean) <= 4 else 3,
        "frequency_per_million": 10.0,
        "decodable": True,
        "grade_level": grade or "K-3",
        "found": False,
        "note": "Heuristic tier classification",
    }
