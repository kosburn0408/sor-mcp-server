"""Lexile text complexity analysis tool.

Computes approximate Lexile measures using sentence length and word frequency
metrics. Lexile framework (MetaMetrics) ranges from 0L (beginning reader) to
2000L+. This tool uses a simplified model based on:

- Mean Sentence Length (MSL): longer sentences → higher Lexile
- Mean Log Word Frequency (MLWF): less common words → higher Lexile
- Word count and unique word ratio for additional context

Theoretical basis: Simple View of Reading — a text's decodability and
linguistic complexity directly affect whether a reader can comprehend it.
"""

import math
import re
import statistics
from collections import Counter
from typing import Any


# Common word frequency list (top 1000 English words, simplified)
# Log frequency based on Corpus of Contemporary American English (COCA)
COMMON_WORDS: set[str] = {
    "the", "be", "to", "of", "and", "a", "in", "that", "have", "i",
    "it", "for", "not", "on", "with", "he", "as", "you", "do", "at",
    "this", "but", "his", "by", "from", "they", "we", "her", "she",
    "or", "an", "will", "my", "one", "all", "would", "there", "their",
    "what", "so", "up", "out", "if", "about", "who", "get", "which",
    "go", "me", "when", "make", "can", "like", "time", "no", "just",
    "him", "know", "take", "people", "into", "year", "your", "good",
    "some", "could", "them", "see", "other", "than", "then", "now",
    "look", "only", "come", "its", "over", "think", "also", "back",
    "after", "use", "two", "how", "our", "work", "first", "well",
    "way", "even", "new", "want", "because", "any", "these", "give",
    "day", "most", "us", "great", "tell", "say", "ask", "man",
    "woman", "child", "world", "life", "hand", "part", "place",
    "case", "week", "company", "system", "program", "question",
    "government", "number", "night", "point", "home", "water",
    "room", "mother", "area", "money", "story", "fact", "month",
    "lot", "right", "study", "book", "eye", "job", "word", "side",
    "kind", "head", "house", "service", "friend", "father", "power",
    "hour", "game", "line", "end", "member", "law", "car", "city",
    "community", "name", "president", "team", "minute", "idea",
    "body", "information", "back", "parent", "face", "level",
    "office", "door", "health", "person", "art", "war", "history",
    "party", "result", "morning", "reason", "research", "girl",
    "guy", "moment", "air", "teacher", "force", "education",
}


def compute_lexile(text: str) -> dict[str, Any]:
    """Compute Lexile-level metrics for a given text.

    Args:
        text: The text to analyze.

    Returns:
        Dictionary with Lexile score, word count, sentence stats, and
        grade-level equivalency.
    """
    if not text or not text.strip():
        return {
            "error": "No text provided for analysis",
            "lexile_score": None,
        }

    # Tokenize words (handle contractions and hyphens)
    words = re.findall(r"[a-zA-Z]+(?:'[a-zA-Z]+)?", text.lower())
    if not words:
        return {
            "lexile_score": None,
            "error": "No recognizable words found in text",
        }

    # Sentence segmentation (simple period-based split)
    sentences = re.split(r'[.!?]+\s+', text)
    sentences = [s.strip() for s in sentences if s.strip() and len(s.split()) > 1]
    if not sentences:
        sentences = [text.strip()]

    word_count = len(words)
    sentence_count = len(sentences)
    unique_words = len(set(words))
    unique_ratio = unique_words / word_count if word_count > 0 else 0

    # Mean Sentence Length (MSL)
    msl = word_count / sentence_count if sentence_count > 0 else word_count

    # Mean Log Word Frequency (MLWF)
    # Words not in common list get higher "rarity" weight
    rare_count = sum(1 for w in words if w not in COMMON_WORDS)
    rare_ratio = rare_count / word_count if word_count > 0 else 0

    # Simplified Lexile formula:
    # Lexile ≈ 200 + (MSL * 15) + (rare_ratio * 1200) - (unique_ratio * 100)
    # Based on correlation between Lexile measures and these text features
    lexile_raw = 200 + (msl * 15) + (rare_ratio * 1200) - (unique_ratio * 100)

    # Clamp to reasonable range
    lexile_score = max(0, min(2000, round(lexile_raw / 10) * 10))

    # Word length statistics
    word_lengths = [len(w) for w in words]
    avg_word_length = statistics.mean(word_lengths) if word_lengths else 0
    word_length_std = statistics.stdev(word_lengths) if len(word_lengths) > 1 else 0

    # Grade level mapping (approximate)
    grade_level = lexile_to_grade(lexile_score)

    # Theoretical alignment
    framework_note = _framework_guidance(lexile_score, grade_level)

    return {
        "lexile_score": lexile_score,
        "grade_level": grade_level,
        "word_count": word_count,
        "sentence_count": sentence_count,
        "unique_words": unique_words,
        "unique_word_ratio": round(unique_ratio, 3),
        "mean_sentence_length": round(msl, 1),
        "mean_word_length": round(avg_word_length, 1),
        "word_length_std": round(word_length_std, 2),
        "rare_word_ratio": round(rare_ratio, 3),
        "framework_alignment": framework_note,
    }


def lexile_to_grade(lexile: int) -> str:
    """Map Lexile score to approximate grade level."""
    if lexile <= 100:
        return "BR (Beginning Reader)"
    elif lexile <= 300:
        return "K-1"
    elif lexile <= 500:
        return "2"
    elif lexile <= 650:
        return "3"
    elif lexile <= 800:
        return "4"
    elif lexile <= 950:
        return "5"
    elif lexile <= 1050:
        return "6-8"
    elif lexile <= 1200:
        return "9-10"
    elif lexile <= 1400:
        return "11-12"
    else:
        return "College/Advanced"


def _framework_guidance(lexile: int, grade: str) -> str:
    """Provide framework-aligned guidance based on Lexile."""
    if lexile <= 300:
        return ("Simple View of Reading — At this level, decoding (word recognition) is the "
                "primary constraint. Scarborough's Rope: word recognition strands "
                "(phonological awareness, decoding) must be secure for comprehension. "
                "NRP Pillars: Phonemic Awareness and Phonics are priority.")
    elif lexile <= 650:
        return ("Simple View of Reading — Both decoding and linguistic comprehension are "
                "developing. Scarborough's Rope: word recognition becoming increasingly "
                "automatic. NRP Pillars: Phonics fluency transition, vocabulary building.")
    elif lexile <= 950:
        return ("Simple View of Reading — Linguistic comprehension increasingly drives "
                "reading outcomes as decoding becomes automatic. Scarborough's Rope: "
                "language comprehension strands (background knowledge, vocabulary, "
                "language structures) gain prominence. NRP Pillars: Fluency, Vocabulary, "
                "Comprehension.")
    else:
        return ("Simple View of Reading — Decoding is largely automated; comprehension "
                "is driven by linguistic knowledge. Scarborough's Rope: all strands "
                "woven together for skilled reading. NRP Pillars: Vocabulary and "
                "Comprehension are primary with fluency maintenance.")


if __name__ == "__main__":
    import json
    sample = (
        "The cat sat on the mat. It was a sunny day. "
        "The cat looked at the bird in the tree."
    )
    result = compute_lexile(sample)
    print(json.dumps(result, indent=2))
