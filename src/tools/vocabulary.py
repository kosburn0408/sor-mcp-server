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


TIER1_MIN_ZIPF = 4.6   # very common words (e.g. "cat" 4.8, "quickly" 5.0)
TIER3_MAX_ZIPF = 3.2   # rare words, usually technical (e.g. "phoneme" 2.4, "magma" 3.2)

FREQUENCY_NOTE = (
    "Tiers are estimated from word frequency (wordfreq Zipf scale), the project's small tier "
    "corpus, and an academic word list. Frequency cannot tell an everyday word like 'frog' from "
    "an academic word like 'reluctant' when both are uncommon, so Tier 2 words are candidates for "
    "a teacher to review, ordered from most to least common (most useful first)."
)


def _basic_words() -> set[str]:
    from src.resources.word_lists import DOLCH_LISTS, FRY_LISTS, HIGH_FREQUENCY_WORDS

    words: set[str] = set()
    for group in (DOLCH_LISTS, FRY_LISTS, HIGH_FREQUENCY_WORDS):
        for lst in group.values():
            words.update(w.lower() for w in lst)
    return words


def _corpus() -> dict[str, dict[str, Any]]:
    out: dict[str, dict[str, Any]] = {}
    try:
        from db.database import get_connection

        rows = get_connection().execute("SELECT word, tier, frequency, grade FROM vocabulary_corpus").fetchall()
        for r in rows:
            out.setdefault(r[0].lower(), {"tier": r[1], "grade_level": "K" if r[3] == 0 else str(r[3])})
    except Exception:
        pass
    return out


def _zipf(word: str) -> float | None:
    try:
        from wordfreq import zipf_frequency
    except ImportError:
        return None
    return zipf_frequency(word, "en")


def estimate_tier(word: str, corpus: dict[str, dict[str, Any]] | None = None,
                  basic: set[str] | None = None) -> dict[str, Any]:
    """Estimate a word's Beck tier. Returns tier (1/2/3 or None), source and zipf."""
    w = word.lower()
    corpus = _corpus() if corpus is None else corpus
    basic = _basic_words() if basic is None else basic
    z = _zipf(w)
    zr = round(z, 2) if z is not None else None
    if w in corpus:
        return {"tier": corpus[w]["tier"], "source": "tier corpus", "zipf": zr}
    for base, variants in TIER_2_PATTERNS.items():
        if w == base or w in variants:
            return {"tier": 2, "source": "academic word list", "zipf": zr}
    if w in basic:
        return {"tier": 1, "source": "high-frequency word list", "zipf": zr}
    if z is None:
        return {"tier": None, "source": "unavailable (wordfreq not installed)", "zipf": None}
    if z == 0:
        return {"tier": None, "source": "not in frequency data", "zipf": 0.0}
    if z >= TIER1_MIN_ZIPF:
        return {"tier": 1, "source": "frequency", "zipf": zr}
    if z < TIER3_MAX_ZIPF:
        return {"tier": 3, "source": "frequency", "zipf": zr}
    return {"tier": 2, "source": "frequency", "zipf": zr}


def seen_lower(text: str) -> set[str]:
    """Words that appear in lowercase somewhere in the text."""
    return {t for t in re.findall(r"[a-z]+(?:'[a-z]+)?", text) if t[0].islower()}


def classify_text(text: str, domain: str | None = None) -> dict[str, Any]:
    """Sort a passage's words into Beck, McKeown & Kucan's three tiers (estimated).

    Proper nouns (capitalized words that don't start a sentence) are listed
    separately as names. See FREQUENCY_NOTE for the method and its limits.
    """
    if not text or not text.strip():
        return {"error": "No text provided for classification", "total_words": 0}

    tokens = list(re.finditer(r"[A-Za-z]+(?:'[A-Za-z]+)?", text))
    if not tokens:
        return {"error": "No recognizable words found", "total_words": 0}

    names: Counter = Counter()
    words: list[str] = []
    for m in tokens:
        tok = m.group(0)
        before = text[:m.start()].rstrip()
        sentence_start = not before or before[-1] in ".!?\"\u201c"
        if tok[0].isupper() and tok != "I" and not sentence_start:
            names[tok] += 1
        elif tok[0].isupper() and sentence_start and tok.lower() not in seen_lower(text) \
                and (_zipf(tok.lower()) or 0) < TIER3_MAX_ZIPF:
            # Rare capitalized word at a sentence start: probably a name.
            names[tok] += 1
        else:
            words.append(tok.lower())

    total_words = len(tokens)
    word_counts = Counter(words)
    corpus, basic = _corpus(), _basic_words()

    buckets: dict[str, list[dict[str, Any]]] = {"tier_1": [], "tier_2": [], "tier_3": [], "unclassified": []}
    for word, count in word_counts.items():
        est = estimate_tier(word, corpus, basic)
        item = {"word": word, "count": count, "zipf": est["zipf"], "source": est["source"]}
        key = f"tier_{est['tier']}" if est["tier"] else "unclassified"
        buckets[key].append(item)

    for key in buckets:
        buckets[key].sort(key=lambda i: (-(i["zipf"] or 0), i["word"]))

    counts = {k: sum(i["count"] for i in v) for k, v in buckets.items()}
    counts["names"] = sum(names.values())

    if buckets["tier_2"]:
        top = ", ".join(i["word"] for i in buckets["tier_2"][:6])
        rec = (
            f"Review the {len(buckets['tier_2'])} Tier 2 candidates (most useful first: {top}). "
            "Pre-teach the ones that are useful across many texts; skip everyday words students already know."
        )
    else:
        rec = "No Tier 2 candidates found; check Tier 3 words for any that need a quick definition."

    return {
        "total_words": total_words,
        "unique_words": len(word_counts),
        "domain": domain or "general",
        "tier_counts": {k: counts[k] for k in ("tier_1", "tier_2", "tier_3", "unclassified", "names")},
        "tier_summary": {
            k: {"count": counts[k], "pct": round(counts[k] / total_words * 100, 1)}
            for k in ("tier_1", "tier_2", "tier_3", "unclassified", "names")
        },
        "tier_1_words": buckets["tier_1"],
        "tier_2_words": buckets["tier_2"],
        "tier_3_words": buckets["tier_3"],
        "unclassified_words": buckets["unclassified"],
        "names": [{"word": n, "count": c} for n, c in names.most_common()],
        "method": FREQUENCY_NOTE,
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
        est = estimate_tier(word_clean)
        result.update({"tier": est["tier"], "found": False, "tier_source": est["source"], "zipf": est["zipf"]})

    result.update(_decodability_info(word_clean, grade))
    return result
