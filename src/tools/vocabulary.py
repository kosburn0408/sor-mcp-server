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


def _grade_label(grade: int | None) -> str:
    """Render the corpus grade integer (K=0) as a label."""
    if grade is None:
        return "unknown"
    return "K" if int(grade) == 0 else str(int(grade))


def _grade_to_int(grade: str | None) -> int | None:
    """Parse 'K', '2', '2nd' into the corpus grade integer (K=0)."""
    if grade is None:
        return None
    g = str(grade).strip().upper()
    if g in ("K", "KINDERGARTEN"):
        return 0
    digits = "".join(ch for ch in g if ch.isdigit())
    return int(digits) if digits else None


def _load_corpus() -> dict[str, list[dict[str, Any]]]:
    """Load the vocabulary corpus keyed by word (one entry per grade)."""
    corpus: dict[str, list[dict[str, Any]]] = {}
    try:
        from db.database import get_connection
        conn = get_connection()
        rows = conn.execute(
            "SELECT word, tier, frequency, decodable, grade "
            "FROM vocabulary_corpus ORDER BY grade"
        ).fetchall()
    except Exception:
        # Corpus unavailable: callers fall back to labelled heuristics.
        return corpus
    for word, tier, frequency, decodable, grade in rows:
        corpus.setdefault(word.lower(), []).append({
            "word": word,
            "tier": int(tier),
            "frequency_index": frequency,
            "decodable": bool(decodable),
            "grade": grade,
        })
    return corpus


def _pick_entry(entries: list[dict[str, Any]], grade: int | None) -> dict[str, Any]:
    """Prefer the entry for the requested grade, else the earliest grade."""
    if grade is not None:
        for e in entries:
            if e["grade"] == grade:
                return e
    return entries[0]


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

    corpus = _load_corpus()

    tier1: list[dict[str, Any]] = []
    tier2: list[dict[str, Any]] = []
    tier3: list[dict[str, Any]] = []

    for word, count in word_counts.most_common():
        if word in corpus:
            entry = _pick_entry(corpus[word], None)
            item = {
                "word": word,
                "count": count,
                "grade_level": _grade_label(entry["grade"]),
                "basis": "corpus",
            }
            target = {1: tier1, 2: tier2}.get(entry["tier"], tier3)
            target.append(item)
            continue

        # Not in the curated corpus: label the result as a heuristic so teachers
        # know it needs professional review (Beck's tiers are about utility, not length).
        is_t2 = any(word == base or word in variants for base, variants in TIER_2_PATTERNS.items())
        if is_t2:
            tier2.append({"word": word, "count": count, "grade_level": "3-5", "basis": "heuristic"})
        elif len(word) <= 4 or count > 2:
            tier1.append({"word": word, "count": count, "grade_level": "K-2", "basis": "heuristic"})
        else:
            tier3.append({"word": word, "count": count, "grade_level": "3-5", "basis": "heuristic"})

    heuristic_n = sum(
        1 for group in (tier1, tier2, tier3) for w in group if w["basis"] == "heuristic"
    )

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
        "heuristic_word_count": heuristic_n,
        "classification_note": (
            "Words marked basis='heuristic' are not in the curated corpus; their tier is a "
            "rough guess and should be reviewed by a teacher before instruction."
        ),
    }


def classify_vocabulary(text: str, domain: str | None = None) -> dict[str, Any]:
    """Alias for classify_text."""
    return classify_text(text=text, domain=domain)


def match_word(word: str, grade: str | None = None) -> dict[str, Any]:
    """Look up a single word in the vocabulary corpus."""
    word_clean = word.strip().lower()
    corpus = _load_corpus()
    entries = corpus.get(word_clean)
    if entries:
        entry = _pick_entry(entries, _grade_to_int(grade))
        return {
            "word": entry["word"],
            "tier": entry["tier"],
            "frequency_index": entry["frequency_index"],
            "decodable": entry["decodable"],
            "grade_level": _grade_label(entry["grade"]),
            "found": True,
            "basis": "corpus",
        }

    for base, variants in TIER_2_PATTERNS.items():
        if word_clean in variants or word_clean == base:
            return {
                "word": word_clean,
                "tier": 2,
                "frequency_index": None,
                "decodable": None,
                "grade_level": grade or "3-5",
                "found": False,
                "basis": "heuristic",
                "note": "Derived from the academic word list; not in the curated corpus.",
            }

    return {
        "word": word_clean,
        "tier": None,
        "frequency_index": None,
        "decodable": None,
        "grade_level": grade or "unknown",
        "found": False,
        "basis": "none",
        "note": "Not in the curated corpus. No tier assigned; review before instruction.",
    }
