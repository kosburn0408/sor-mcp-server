"""Decodable text analysis tool.

Checks what percentage of words in a text are decodable at a given grade
level based on phonics patterns taught at each stage.

Theoretical basis: National Reading Panel — systematic phonics instruction
is most effective when students practice with decodable text matched to
their current phonics knowledge. Scarborough's Rope — the decoding strand
must be developed through practice with text that matches the reader's
orthographic mapping stage.

Phonics scope and sequence adapted from:
- WWC Foundational Skills Practice Guide (Foorman et al., 2016)
- University of Oregon DIBELS phonics sequence
"""

import re
from typing import Any


# Phonics patterns by grade level (cumulative — each grade includes prior patterns)
PHONICS_PATTERNS: dict[str, dict[str, str | list[str]]] = {
    "K": {
        "label": "Kindergarten",
        "patterns": [
            r"^[a-z]$",                                 # single letters (C)
            r"^[aeiou]$",                               # short vowels (V)
            r"^[bcdfghjklmnpqrstvwxyz][aeiou]$",        # CV
            r"^[aeiou][bcdfghjklmnpqrstvwxyz]$",        # VC
            r"^[bcdfghjklmnpqrstvwxyz][aeiou][bcdfghjklmnpqrstvwxyz]$",  # CVC
        ],
    },
    "1": {
        "label": "Grade 1",
        "patterns": [
            # Inherits all K patterns plus:
            r"^[bcdfghjklmnpqrstvwxyz]+[aeiou][bcdfghjklmnpqrstvwxyz]+$",  # CCVC, CVCC
            r"^[bcdfghjklmnpqrstvwxyz][aeiou][bcdfghjklmnpqrstvwxyz]e$",    # CVCe (silent e)
            r"^(sh|ch|th|wh|ph|ck|ng|qu)",                                  # digraphs
            r"(sh|ch|th|wh|ph|ck|ng)$",
            r"^(bl|cl|fl|gl|pl|sl|br|cr|dr|fr|gr|pr|tr|sc|sk|sm|sn|sp|st|sw)",  # blends
            r"(mp|nd|nt|nk|st|sk|ft|lt|lp|lk|pt|ct|xt)$",                   # ending blends
        ],
    },
    "2": {
        "label": "Grade 2",
        "patterns": [
            # Inherits all K-1 patterns plus:
            r"(ai|ay|ee|ea|oa|oe|ue|ui|oo|ou|ow|oi|oy|au|aw)",              # vowel teams
            r"^(wr|kn|gn|mb)",                                               # silent letters
            r"^(spr|str|scr|spl|shr|thr)",                                   # 3-letter blends
            r"(ing|ed|er|est|ly|ful|less|ness|ment)",                        # common suffixes
            r"^(un|re|pre|mis|dis)",                                         # common prefixes
        ],
    },
    "3": {
        "label": "Grade 3+",
        "patterns": [
            # Inherits all K-2 patterns plus multisyllabic:
            r"(tion|sion|ture|cious|tious)",                                  # advanced patterns
            r"^(sub|inter|super|trans|anti|semi|mid)",                        # advanced prefixes
            r"(able|ible|ance|ence|ify|ize|ous|al|ic|ive)",                   # advanced suffixes
        ],
    },
}

# Common sight/heart words by grade (need to be taught as whole words, not fully decodable at that level)
SIGHT_WORDS: dict[str, set[str]] = {
    "K": {"the", "a", "I", "to", "is", "my", "go", "me", "like", "on",
           "in", "so", "we", "it", "and", "up", "at", "see", "he", "do",
           "you", "an", "can", "no", "am", "said", "was", "are", "have", "has"},
    "1": {"of", "his", "had", "him", "her", "some", "as", "then", "could",
          "when", "were", "them", "ask", "over", "just", "from", "any",
          "how", "know", "put", "every", "old", "by", "after", "think",
          "let", "going", "walk", "again", "may", "stop", "fly", "round",
          "give", "once", "open", "live", "thank"},
    "2": {"always", "around", "because", "been", "before", "best", "both",
          "buy", "call", "cold", "does", "don't", "fast", "first", "five",
          "found", "gave", "goes", "green", "made", "many", "off", "pull",
          "read", "right", "sing", "sit", "sleep", "tell", "their", "these",
          "those", "upon", "us", "use", "very", "wash", "which", "why",
          "wish", "work", "would", "write", "your"},
    "3": {"about", "better", "bring", "carry", "clean", "cut", "done", "draw",
          "drink", "eight", "fall", "far", "full", "got", "grow", "hold",
          "hot", "hurt", "keep", "kind", "laugh", "light", "long", "much",
          "myself", "never", "only", "own", "pick", "seven", "shall", "show",
          "six", "small", "start", "ten", "today", "together", "try", "warm"},
}


def check_decodability(text: str, grade: str) -> dict[str, Any]:
    """Check what percentage of words in text are decodable at a given grade level.

    Args:
        text: The text to analyze.
        grade: Grade level as string ('K', '1', '2', '3'). Grade 3 serves as ceiling.

    Returns:
        Dictionary with decodability percentage, word-level breakdown, and
        instructional recommendations.
    """
    if not text or not text.strip():
        return {"error": "No text provided for analysis", "decodability_pct": None}

    grade = grade.upper().strip()
    if grade not in PHONICS_PATTERNS:
        return {
            "error": f"Invalid grade '{grade}'. Use K, 1, 2, or 3.",
            "decodability_pct": None,
        }

    # Normalize words
    raw_words = re.findall(r"[a-zA-Z]+(?:'[a-zA-Z]+)?", text.lower())
    if not raw_words:
        return {"error": "No recognizable words found", "decodability_pct": None}

    # Get cumulative patterns up to this grade
    grade_order = ["K", "1", "2", "3"]
    max_index = grade_order.index(grade)
    all_patterns: list[str] = []
    for g in grade_order[:max_index + 1]:
        all_patterns.extend(PHONICS_PATTERNS[g]["patterns"])  # type: ignore[arg-type]

    # Get all sight words up to this grade
    all_sight_words: set[str] = set()
    for g in grade_order[:max_index + 1]:
        all_sight_words |= SIGHT_WORDS.get(g, set())

    # Analyze each word
    word_analysis: list[dict[str, Any]] = []
    decodable_count = 0

    for word in raw_words:
        # Skip very short words (single letters like 'a', 'I')
        if len(word) == 1:
            decodable = True
            reason = "single letter"
        elif word in all_sight_words:
            decodable = True
            reason = "sight/heart word"
        elif word in COMMON_SIGHT_WORDS_ALL:
            decodable = True
            reason = "high-frequency word"
        else:
            # Check against phonics patterns
            decodable = any(re.search(pattern, word) for pattern in all_patterns)
            reason = "matches phonics pattern" if decodable else "beyond current phonics level"

        word_analysis.append({
            "word": word,
            "decodable": decodable,
            "reason": reason,
        })
        if decodable:
            decodable_count += 1

    total = len(raw_words)
    decodability_pct = round(decodable_count / total * 100, 1) if total > 0 else 0.0

    # Get non-decodable words for instruction
    non_decodable = [w for w in word_analysis if not w["decodable"]]

    # Instructional recommendation
    recommendation = _get_recommendation(decodability_pct, grade)

    return {
        "grade": grade,
        "grade_label": PHONICS_PATTERNS[grade]["label"],
        "total_words": total,
        "decodable_words": decodable_count,
        "decodability_percentage": decodability_pct,
        "non_decodable_count": len(non_decodable),
        "non_decodable_words": [w["word"] for w in non_decodable[:20]],
        "non_decodable_truncated": len(non_decodable) > 20,
        "word_analysis_sample": word_analysis[:30],
        "recommendation": recommendation,
        "phonics_patterns_used": len(all_patterns),
        "framework_note": (
            "National Reading Panel — systematic phonics instruction with "
            "decodable text practice yields effect size d=0.41. Scarborough's "
            "Rope — decoding strand strengthened through connected text reading "
            "at the reader's instructional level."
        ),
    }


def _get_recommendation(pct: float, grade: str) -> str:
    """Generate instructional recommendation based on decodability percentage."""
    if pct >= 90:
        return (
            f"Independent reading level for {PHONICS_PATTERNS[grade]['label']}. "
            "This text is highly decodable — students can read it independently "
            "with >90% accuracy. Suitable for independent practice."
        )
    elif pct >= 75:
        return (
            f"Instructional reading level for {PHONICS_PATTERNS[grade]['label']}. "
            "This text is appropriate for guided reading with teacher support. "
            "Pre-teach non-decodable words before reading."
        )
    elif pct >= 50:
        return (
            f"Frustration-level for independent reading in {PHONICS_PATTERNS[grade]['label']}. "
            "Use only with significant scaffolding: pre-teach vocabulary, "
            "paired reading, or teacher read-aloud with discussion. "
            "Consider a simpler text for independent practice."
        )
    else:
        return (
            f"Not suitable for independent reading at {PHONICS_PATTERNS[grade]['label']} level. "
            "Use as a read-aloud only. Text contains many words beyond current "
            "phonics and sight-word knowledge."
        )


# Common high-frequency words from Fry/Dolch lists not covered by sight words
COMMON_SIGHT_WORDS_ALL: set[str] = {
    "a", "i", "the", "and", "to", "in", "is", "you", "that", "it",
    "he", "was", "for", "on", "are", "as", "with", "his", "they",
}


if __name__ == "__main__":
    import json
    sample = "The cat sat on the mat. She looked at the beautiful butterfly."
    result = check_decodability(sample, "K")
    print(json.dumps(result, indent=2))
