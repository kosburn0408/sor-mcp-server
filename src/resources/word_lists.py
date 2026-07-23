"""MCP Resource — Heart Words, Dolch, Fry, and High-Frequency Word Lists.

Provides grade-level word lists aligned to Science of Reading research:
  - Heart Words: Temporarily irregular words taught with explicit marking
  - Dolch Sight Words: Classic high-frequency word lists by grade
  - Fry Instant Words: Top 1000 words by frequency
  - High-Frequency Words: Combined list for instructional planning
"""

from __future__ import annotations

from typing import Any

# ── Heart Words by Grade (with irregular parts noted) ───────────────────────
#
# Heart Words are high-frequency words that contain temporarily irregular
# grapheme-phoneme correspondences. The "heart part" must be learned by heart
# until the student has mastered the relevant phonics pattern.

HEART_WORDS: dict[str, list[dict[str, str]]] = {
    "K": [
        {"word": "the", "regular": "th", "heart": "e says /ə/ (schwa), not short /e/"},
        {"word": "a", "regular": "", "heart": "Says /ə/ (schwa), not long /ā/"},
        {"word": "said", "regular": "s", "heart": "ai says /e/, not /ā/"},
        {"word": "was", "regular": "w", "heart": "a says /u/, not short /a/"},
        {"word": "you", "regular": "y", "heart": "ou says /ōō/, unexpected"},
        {"word": "of", "regular": "o", "heart": "f says /v/, unexpected"},
        {"word": "to", "regular": "t", "heart": "o says /ōō/, unexpected"},
        {"word": "do", "regular": "d", "heart": "o says /ōō/, unexpected"},
        {"word": "are", "regular": "", "heart": "are says /ar/ — silent e irregularity"},
    ],
    "1": [
        {"word": "have", "regular": "h", "heart": "Silent-e doesn't make a long — /a/ stays short"},
        {"word": "give", "regular": "g", "heart": "Silent-e doesn't make i long — /i/ stays short"},
        {"word": "come", "regular": "c", "heart": "o says /u/ + silent e — irregular"},
        {"word": "some", "regular": "s", "heart": "o says /u/ + silent e — irregular"},
        {"word": "what", "regular": "wh", "heart": "a says /u/ (schwa), not short /a/"},
        {"word": "once", "regular": "", "heart": "o says /w/ + ce says /s/ — highly irregular"},
        {"word": "any", "regular": "", "heart": "a says /e/, not short /a/"},
        {"word": "many", "regular": "m", "heart": "a says /e/, not short /a/"},
    ],
    "2": [
        {"word": "because", "regular": "b", "heart": "eau says /ē/ + se says /z/ — irregular"},
        {"word": "been", "regular": "b", "heart": "ee says /i/, not /ē/"},
        {"word": "both", "regular": "b", "heart": "o says /ō/ in closed syllable — irregular"},
        {"word": "does", "regular": "d", "heart": "oe says /u/, not /ō/"},
        {"word": "eye", "regular": "", "heart": "eye says /ī/ — unique pattern"},
        {"word": "friend", "regular": "fr", "heart": "ie says /e/, not /ē/"},
        {"word": "pretty", "regular": "pr", "heart": "e says /i/, not short /e/"},
        {"word": "their", "regular": "th", "heart": "eir says /air/ — irregular vowel team"},
    ],
}

# ── Dolch Word Lists ───────────────────────────────────────────────────────

DOLCH_LISTS: dict[str, list[str]] = {
    "pre_primer": [
        "a", "and", "away", "big", "blue", "can", "come", "down", "find",
        "for", "funny", "go", "help", "here", "i", "in", "is", "it",
        "jump", "little", "look", "make", "me", "my", "not", "one", "play",
        "red", "run", "said", "see", "the", "three", "to", "two", "up",
        "we", "where", "yellow", "you",
    ],
    "primer": [
        "all", "am", "are", "at", "ate", "be", "black", "brown", "but",
        "came", "did", "do", "eat", "four", "get", "good", "have", "he",
        "into", "like", "must", "new", "no", "now", "on", "our", "out",
        "please", "pretty", "ran", "ride", "saw", "say", "she", "so", "soon",
        "that", "there", "they", "this", "too", "under", "want", "was", "well",
        "went", "what", "white", "who", "will", "with", "yes",
    ],
    "grade_1": [
        "after", "again", "an", "any", "as", "ask", "by", "could", "every",
        "fly", "from", "give", "going", "had", "has", "her", "him", "his",
        "how", "just", "know", "let", "live", "may", "of", "old", "once",
        "open", "over", "put", "round", "some", "stop", "take", "thank",
        "them", "then", "think", "walk", "were", "when",
    ],
    "grade_2": [
        "always", "around", "because", "been", "before", "best", "both",
        "buy", "call", "cold", "does", "don't", "fast", "first", "five",
        "found", "gave", "goes", "green", "its", "made", "many", "off",
        "or", "pull", "read", "right", "sing", "sit", "sleep", "tell",
        "their", "these", "those", "upon", "us", "use", "very", "wash",
        "which", "why", "wish", "work", "would", "write", "your",
    ],
    "grade_3": [
        "about", "better", "bring", "carry", "clean", "cut", "done", "draw",
        "drink", "eight", "fall", "far", "full", "got", "grow", "hold",
        "hot", "hurt", "if", "keep", "kind", "laugh", "light", "long",
        "much", "myself", "never", "only", "own", "pick", "seven", "shall",
        "show", "six", "small", "start", "ten", "today", "together", "try",
        "warm",
    ],
}

# ── Fry Word Lists (Top 100) ───────────────────────────────────────────────

FRY_LISTS: dict[str, list[str]] = {
    "first_100": [
        "the", "of", "and", "a", "to", "in", "is", "you", "that", "it",
        "he", "was", "for", "on", "are", "as", "with", "his", "they", "i",
        "at", "be", "this", "have", "from", "or", "one", "had", "by", "word",
        "but", "not", "what", "all", "were", "we", "when", "your", "can", "said",
        "there", "use", "an", "each", "which", "she", "do", "how", "their", "if",
        "will", "up", "other", "about", "out", "many", "then", "them", "these", "so",
        "some", "her", "would", "make", "like", "him", "into", "time", "has", "look",
        "two", "more", "write", "go", "see", "number", "no", "way", "could", "people",
        "my", "than", "first", "water", "been", "called", "who", "am", "its", "now",
        "find", "long", "down", "day", "did", "get", "come", "made", "may", "part",
    ],
}

# ── Combined High-Frequency Words by Grade ──────────────────────────────────

HIGH_FREQUENCY_WORDS: dict[str, list[str]] = {
    "K": [
        "a", "and", "are", "at", "be", "can", "come", "do", "for", "go",
        "he", "here", "i", "in", "is", "it", "like", "look", "me", "my",
        "no", "of", "on", "play", "said", "see", "she", "so", "the", "to",
        "up", "was", "we", "were", "what", "with", "you",
    ],
    "1": [
        "after", "again", "all", "am", "an", "any", "as", "ask", "by", "could",
        "day", "did", "every", "find", "from", "give", "going", "had", "has",
        "have", "her", "him", "his", "how", "just", "know", "let", "live",
        "may", "now", "old", "once", "open", "over", "put", "round", "some",
        "stop", "take", "thank", "them", "then", "think", "walk", "when",
    ],
    "2": [
        "always", "around", "because", "been", "before", "best", "both",
        "buy", "call", "cold", "does", "don't", "fast", "first", "five",
        "found", "gave", "goes", "green", "its", "made", "many", "off",
        "pull", "read", "right", "sing", "sit", "sleep", "tell", "their",
        "these", "those", "upon", "us", "use", "very", "wash", "which",
        "why", "wish", "work", "would", "write", "your",
    ],
}


# ── Resource API ────────────────────────────────────────────────────────────


def get_word_list(list_type: str, grade: str | None = None) -> dict[str, Any]:
    """Retrieve a specific word list.

    Args:
        list_type: 'heart', 'dolch', 'fry', or 'high_frequency'.
        grade: Optional grade filter.

    Returns:
        Dictionary with word list data.
    """
    if list_type == "heart":
        if grade and grade in HEART_WORDS:
            return {"type": "heart_words", "grade": grade, "words": HEART_WORDS[grade], "count": len(HEART_WORDS[grade])}
        all_words: list[dict[str, str]] = []
        for words in HEART_WORDS.values():
            all_words.extend(words)
        return {"type": "heart_words", "grade": "all", "words": all_words, "count": len(all_words)}

    if list_type == "dolch":
        if grade and grade in DOLCH_LISTS:
            return {"type": "dolch", "level": grade, "words": DOLCH_LISTS[grade], "count": len(DOLCH_LISTS[grade])}
        return {"type": "dolch", "levels": list(DOLCH_LISTS.keys()), "total_words": sum(len(v) for v in DOLCH_LISTS.values())}

    if list_type == "fry":
        return {"type": "fry", "lists": list(FRY_LISTS.keys()), "total_words": sum(len(v) for v in FRY_LISTS.values())}

    if list_type == "high_frequency":
        if grade and grade in HIGH_FREQUENCY_WORDS:
            return {"type": "high_frequency", "grade": grade, "words": HIGH_FREQUENCY_WORDS[grade], "count": len(HIGH_FREQUENCY_WORDS[grade])}
        return {"type": "high_frequency", "grades": list(HIGH_FREQUENCY_WORDS.keys()), "total_words": sum(len(v) for v in HIGH_FREQUENCY_WORDS.values())}

    return {"error": f"Unknown list type '{list_type}'. Use: heart, dolch, fry, high_frequency."}


def list_word_lists() -> dict[str, Any]:
    """Return available word lists with descriptions."""
    return {
        "available_lists": {
            "heart": {
                "description": "Heart Words — temporarily irregular words taught with explicit marking of irregular parts",
                "grades": list(HEART_WORDS.keys()),
                "total_words": sum(len(v) for v in HEART_WORDS.values()),
            },
            "dolch": {
                "description": "Dolch Sight Words — classic high-frequency word lists (pre-primer through grade 3)",
                "levels": list(DOLCH_LISTS.keys()),
                "total_words": sum(len(v) for v in DOLCH_LISTS.values()),
            },
            "fry": {
                "description": "Fry Instant Words — top words by frequency in English text",
                "lists": list(FRY_LISTS.keys()),
                "total_words": sum(len(v) for v in FRY_LISTS.values()),
            },
            "high_frequency": {
                "description": "Combined high-frequency words by grade level (K-2)",
                "grades": list(HIGH_FREQUENCY_WORDS.keys()),
                "total_words": sum(len(v) for v in HIGH_FREQUENCY_WORDS.values()),
            },
        }
    }
