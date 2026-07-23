"""Diagnostics tools: Lexile analysis and Simple View evaluation.

Moved from tools/lexile.py and server.py inline evaluation logic.
Now uses Pydantic v2 models for routing.
"""

from __future__ import annotations

import math
import re
import statistics
from typing import Any

from src.schemas.curriculum import CurriculumResult


# ── Lexile Analysis ────────────────────────────────────────────────────────

# Common word frequency list (top English words, simplified from COCA)
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
    "body", "information", "parent", "face", "level",
    "office", "door", "health", "person", "art", "war", "history",
    "party", "result", "morning", "reason", "research", "girl",
    "guy", "moment", "air", "teacher", "force", "education",
}


def analyze_lexile(text: str) -> dict[str, Any]:
    """Compute Lexile-level metrics for a given text.

    Args:
        text: The text to analyze.

    Returns:
        Dictionary with Lexile score, word count, sentence stats, and
        grade-level equivalency.
    """
    if not text or not text.strip():
        return {"error": "No text provided for analysis", "lexile_score": None}

    words = re.findall(r"[a-zA-Z]+(?:'[a-zA-Z]+)?", text.lower())
    if not words:
        return {"lexile_score": None, "error": "No recognizable words found in text"}

    sentences = re.split(r'[.!?]+\s+', text)
    sentences = [s.strip() for s in sentences if s.strip() and len(s.split()) > 1]
    if not sentences:
        sentences = [text.strip()]

    word_count = len(words)
    sentence_count = len(sentences)
    unique_words = len(set(words))
    unique_ratio = unique_words / word_count if word_count > 0 else 0

    msl = word_count / sentence_count if sentence_count > 0 else word_count
    rare_count = sum(1 for w in words if w not in COMMON_WORDS)
    rare_ratio = rare_count / word_count if word_count > 0 else 0

    lexile_raw = 200 + (msl * 15) + (rare_ratio * 1200) - (unique_ratio * 100)
    lexile_score = max(0, min(2000, round(lexile_raw / 10) * 10))

    word_lengths = [len(w) for w in words]
    avg_word_length = statistics.mean(word_lengths) if word_lengths else 0
    word_length_std = statistics.stdev(word_lengths) if len(word_lengths) > 1 else 0

    grade_level = _lexile_to_grade(lexile_score)
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


def _lexile_to_grade(lexile: int) -> str:
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
        return (
            "Simple View of Reading — At this level, decoding (word recognition) is the "
            "primary constraint. Scarborough's Rope: word recognition strands "
            "(phonological awareness, decoding) must be secure for comprehension. "
            "NRP Pillars: Phonemic Awareness and Phonics are priority."
        )
    elif lexile <= 650:
        return (
            "Simple View of Reading — Both decoding and linguistic comprehension are "
            "developing. Scarborough's Rope: word recognition becoming increasingly "
            "automatic. NRP Pillars: Phonics fluency transition, vocabulary building."
        )
    elif lexile <= 950:
        return (
            "Simple View of Reading — Linguistic comprehension increasingly drives "
            "reading outcomes as decoding becomes automatic. Scarborough's Rope: "
            "language comprehension strands gain prominence. NRP Pillars: Fluency, Vocabulary, Comprehension."
        )
    else:
        return (
            "Simple View of Reading — Decoding is largely automated; comprehension "
            "is driven by linguistic knowledge. Scarborough's Rope: all strands "
            "woven together for skilled reading. NRP Pillars: Vocabulary and "
            "Comprehension are primary with fluency maintenance."
        )


# ── Simple View of Reading ──────────────────────────────────────────────────


def evaluate_simple_view(
    decoding: float,
    language_comprehension: float,
    grade: str = "1st",
) -> dict[str, Any]:
    """Evaluate a student using the Simple View of Reading.

    Returns reading profile (typical/dyslexia/hyperlexic/garden_variety),
    deficit codes, and auto-attached remediation cards when decoding < 0.60.

    Args:
        decoding: Decoding score (0.0-1.0).
        language_comprehension: Language comprehension score (0.0-1.0).
        grade: Grade level string (e.g., '1st').

    Returns:
        Dictionary with diagnostic, remediations, and next_steps.
    """
    from src.tools.remediation import get_bulk_remediations

    # Validate score ranges
    if not 0.0 <= decoding <= 1.0:
        return {
            "error_code": "ERR_INVALID_SCORE_RANGE",
            "error": f"Decoding score {decoding} is outside valid range [0.0, 1.0]",
        }
    if not 0.0 <= language_comprehension <= 1.0:
        return {
            "error_code": "ERR_INVALID_SCORE_RANGE",
            "error": f"Language comprehension score {language_comprehension} outside valid range [0.0, 1.0]",
        }

    # Determine profile
    if decoding >= 0.60 and language_comprehension >= 0.60:
        profile = "typical"
    elif decoding < 0.60 and language_comprehension >= 0.60:
        profile = "dyslexia"
    elif decoding >= 0.60 and language_comprehension < 0.60:
        profile = "hyperlexic"
    else:
        profile = "garden_variety"

    deficit_codes: list[str] = []
    if decoding < 0.60:
        if decoding < 0.30:
            deficit_codes = ["phoneme_segmentation", "cvc_mixed", "cvc_short_a"]
        elif decoding < 0.45:
            deficit_codes = ["cvc_mixed", "consonant_blends", "consonant_digraphs"]
        else:
            deficit_codes = ["cvce_silent_e", "vowel_teams", "r_controlled"]

    remediations = []
    if decoding < 0.60:
        remediations = get_bulk_remediations(deficit_codes, grade)

    if profile == "typical":
        next_steps = "Student is on track. Continue grade-level instruction."
    elif profile == "dyslexia":
        next_steps = (
            f"Decoding deficit (score={decoding:.2f}). Use attached "
            f"{len(remediations)} remediation cards 4-5x/week. "
            "Administer CORE Phonics Survey. Consider Tier 2."
        )
    elif profile == "hyperlexic":
        next_steps = (
            "Strong decoder, weak comprehender. Focus on vocabulary, "
            "background knowledge, and read-alouds with discussion."
        )
    else:
        next_steps = (
            "Dual deficit. Prioritize decoding, layer comprehension. "
            "Tier 2 or Tier 3 intervention recommended."
        )

    return {
        "diagnostic": {
            "decoding_score": decoding,
            "language_comprehension_score": language_comprehension,
            "reading_profile": profile,
            "deficit_codes": deficit_codes,
        },
        "remediations": [r.to_markdown() for r in remediations],
        "next_steps": next_steps,
    }


# ── Scope Sequence Lookup (used by router) ──────────────────────────────────


SCOPE_SEQUENCE: dict[str, dict[str, list[str]]] = {
    "K": {
        "phonology": {
            "concepts": [
                "Rhyming words", "Syllable counting", "Initial/final sound identification",
                "Phoneme blending (2-3 sounds)", "Phoneme segmentation (2-3 sounds)",
            ],
            "phonemes": ["/a/", "/e/", "/i/", "/o/", "/u/", "/m/", "/s/", "/t/", "/p/", "/n/", "/d/", "/k/", "/g/", "/b/", "/f/"],
            "syllable_types": ["closed"],
            "prerequisites": ["Print concepts", "Letter recognition"],
            "next_steps": ["CVC words", "Digraph introduction"],
        },
        "morphology": {
            "concepts": ["Plural -s (spoken)"],
            "phonemes": [],
            "syllable_types": [],
            "prerequisites": ["Oral language development"],
            "next_steps": ["Inflectional endings", "Compound words"],
        },
    },
    "1": {
        "phonology": {
            "concepts": [
                "CVC blending/segmenting", "Consonant digraphs (sh, ch, th, wh, ck)",
                "Consonant blends (l-blends, r-blends, s-blends)",
                "CVCe silent-e pattern", "Open syllables (CV)",
            ],
            "phonemes": ["/sh/", "/ch/", "/th/", "/wh/", "/ng/", "/qu/", "/ā/", "/ē/", "/ī/", "/ō/", "/ū/"],
            "syllable_types": ["closed", "VCe", "open"],
            "prerequisites": ["K phoneme awareness", "CVC decoding"],
            "next_steps": ["Vowel teams", "R-controlled vowels", "Multisyllabic words"],
        },
        "morphology": {
            "concepts": ["Inflectional endings (-s, -es, -ed, -ing)", "Compound words"],
            "phonemes": [],
            "syllable_types": [],
            "prerequisites": ["K oral language"],
            "next_steps": ["Prefix un-/re-", "Suffix -er/-est"],
        },
    },
    "2": {
        "phonology": {
            "concepts": [
                "Vowel teams (ai, ay, ee, ea, oa, oe, ue, ui)",
                "R-controlled vowels (ar, or, er, ir, ur)",
                "Diphthongs (oi, oy, ou, ow)", "Silent letters (wr, kn, gn, mb)",
                "Three-letter blends (scr, str, spr, spl)",
                "Multisyllabic decoding (VC/CV)",
            ],
            "phonemes": ["/oi/", "/oy/", "/ou/", "/ow/", "/ar/", "/or/", "/er/", "/ir/", "/ur/"],
            "syllable_types": ["closed", "VCe", "open", "vowel_team", "r_controlled"],
            "prerequisites": ["Grade 1 phonics", "Silent-e mastery"],
            "next_steps": ["C+le syllables", "Advanced vowel teams"],
        },
        "morphology": {
            "concepts": [
                "Prefix un-/re-/pre-/mis-/dis-", "Suffix -er/-est/-ly/-ful/-less",
                "Past tense -ed (3 sounds)", "Plural rules",
            ],
            "phonemes": [],
            "syllable_types": [],
            "prerequisites": ["Grade 1 morphology"],
            "next_steps": ["Greek/Latin roots", "Advanced affixes"],
        },
    },
    "3": {
        "phonology": {
            "concepts": [
                "Advanced vowel teams (au, aw, ei, ey, eu, ew)",
                "Consonant+le syllables", "Schwa sound",
                "Multisyllabic decoding (all 6 types)",
            ],
            "phonemes": ["/aw/", "/au/", "/schwa/"],
            "syllable_types": ["closed", "VCe", "open", "vowel_team", "r_controlled", "c_le"],
            "prerequisites": ["Grade 2 phonics", "Basic syllable division"],
            "next_steps": ["Complex morphology", "Content-area vocabulary"],
        },
        "morphology": {
            "concepts": [
                "Greek roots (bio, graph, phon, scope)",
                "Latin roots (dict, port, struct, tract)",
                "Prefixes (sub-, inter-, super-, trans-)",
                "Suffixes (-able, -ible, -ance, -ence, -ify, -ize)",
            ],
            "phonemes": [],
            "syllable_types": [],
            "prerequisites": ["Grade 2 morphology"],
            "next_steps": ["Advanced Greek/Latin roots", "Content-specific morphology"],
        },
    },
    "4": {
        "phonology": {
            "concepts": [
                "Advanced multisyllabic decoding", "Stress and accent patterns",
                "Schwa in unstressed syllables",
            ],
            "phonemes": [],
            "syllable_types": ["all"],
            "prerequisites": ["Grade 3 phonics"],
            "next_steps": ["Grade 5 fluency"],
        },
        "morphology": {
            "concepts": [
                "Advanced affixes (anti-, semi-, mid-, -ous, -al, -ic, -ive)",
                "Greek combining forms", "Syllable stress patterns",
            ],
            "phonemes": [],
            "syllable_types": [],
            "prerequisites": ["Grade 3 morphology"],
            "next_steps": ["Grade 5 advanced morphology"],
        },
    },
    "5": {
        "phonology": {
            "concepts": [
                "Fluent multisyllabic decoding", "Irregular spelling patterns",
                "Content-area vocabulary decoding",
            ],
            "phonemes": [],
            "syllable_types": ["all"],
            "prerequisites": ["Grade 4 phonics", "All syllable types"],
            "next_steps": ["Middle school literacy"],
        },
        "morphology": {
            "concepts": [
                "Full affix system", "Academic word families",
                "Etymology patterns across content areas",
            ],
            "phonemes": [],
            "syllable_types": [],
            "prerequisites": ["Grade 4 morphology"],
            "next_steps": ["Middle school content literacy"],
        },
    },
}

# Vocabulary and fluency scope data (simplified)
_VOCAB_FLUENCY: dict[str, dict[str, dict[str, list[str]]]] = {
    "K": {
        "vocabulary": {
            "concepts": ["Tier 1 oral vocabulary", "Category sorting", "Story vocabulary"],
            "prerequisites": ["Oral language"],
            "next_steps": ["Tier 2 introduction", "Text-based vocabulary"],
        },
        "fluency": {
            "concepts": ["Letter naming fluency", "Initial sound fluency"],
            "prerequisites": ["Letter knowledge"],
            "next_steps": ["CVC word reading fluency"],
        },
    },
    "1": {
        "vocabulary": {
            "concepts": ["Tier 2 oral vocabulary", "Multiple meaning words", "Shades of meaning"],
            "prerequisites": ["K vocabulary"],
            "next_steps": ["Context clues", "Academic vocabulary"],
        },
        "fluency": {
            "concepts": ["CVC word automaticity", "Sight word fluency", "Phrased reading"],
            "prerequisites": ["K fluency"],
            "next_steps": ["Silent-e fluency", "Digraph fluency"],
        },
    },
}


def get_scope_sequence(grade: str, strand: str) -> dict[str, Any]:
    """Retrieve scope and sequence data for a grade and strand.

    Args:
        grade: Grade level (K, 1, 2, 3, 4, 5).
        strand: Literacy strand (phonology, morphology, vocabulary, fluency, comprehension).

    Returns:
        Dictionary with concepts, prerequisites, and next_steps.
    """
    if strand in ("phonology", "morphology"):
        entry = SCOPE_SEQUENCE.get(grade, {}).get(strand)
        if entry:
            return dict(entry)
    if strand in ("vocabulary", "fluency"):
        entry = _VOCAB_FLUENCY.get(grade, {}).get(strand)
        if entry:
            return dict(entry)
    if strand == "comprehension":
        return {
            "concepts": [
                f"Grade {grade} comprehension strategies",
                "Literal and inferential questioning",
            ],
            "prerequisites": ["Decoding fluency", "Vocabulary knowledge"],
            "next_steps": ["Higher-order thinking", "Cross-text synthesis"],
        }

    return {"concepts": [], "prerequisites": [], "next_steps": []}
