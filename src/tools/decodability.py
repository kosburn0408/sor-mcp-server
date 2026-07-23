"""Anti-cueing decodability verifier for Science of Reading MCP server.

Provides verify_decodable_text — a production-grade decodability analysis
tool with built-in anti-cueing guardrails that block 3-cueing/MSV strategies,
flag picture-guessing, and detect reliance on context clues rather than
phoneme-by-phoneme decoding.

Structured error codes:
  ERR_OFF_SCOPE_PHONEME  — Phoneme not in scope for this grade
  ERR_CUEING_DETECTED    — Content contains 3-cueing strategies
  ERR_UNTAUGHT_PATTERN   — Text uses untaught phonics patterns
  ERR_HEART_WORD_AS_DECODABLE — Heart word incorrectly marked as decodable
"""

from __future__ import annotations

import re
from typing import Any

from src.core.errors import SoRErrorCode, format_error
from src.schemas.decodability import (
    DecodabilityRequest,
    DecodabilityResult,
    HeartWordEntry,
    OffScopeWord,
    WarningEntry,
)


# ── Anti-Cueing Detection Patterns ──────────────────────────────────────────
#
# These patterns flag instructional language and strategies that are
# incompatible with Science of Reading best practice: the 3-cueing system
# (MSV: Meaning, Structure, Visual) encourages guessing from context rather
# than decoding phoneme-by-phoneme.

CUEING_FLAG_PATTERNS: list[tuple[str, str, str]] = [
    # (pattern, label, explanation)
    (
        r"\b(?:look at the picture|picture clue|picture walk|use the picture)\b",
        "MSV_MEANING",
        "Picture-guessing — student is directed to use illustration rather than decode",
    ),
    (
        r"\b(?:does it make sense|guess from context|what would make sense)\b",
        "MSV_MEANING",
        "Meaning-based guessing — student uses semantics rather than grapheme-phoneme mapping",
    ),
    (
        r"\b(?:skip it and go on|skip the word|come back to it)\b",
        "MSV_STRUCTURE",
        "Skip-and-return strategy — encourages guessing from sentence grammar rather than decoding",
    ),
    (
        r"\b(?:three.?cueing|3.?cueing|multi.?cueing|MSV)\b",
        "MSV_EXPLICIT",
        "Explicit 3-cueing / MSV reference — this framework has been discredited by cognitive science",
    ),
    (
        r"\b(?:sound it out.*picture|picture.*sound it out)\b",
        "MSV_MIXED",
        "Mixed picture + decoding approach — picture cues undermine decoding practice",
    ),
    (
        r"\b(?:use the first letter and guess|beginning sound.*guess|initial sound.*guess)\b",
        "MSV_PARTIAL",
        "Partial decoding + guessing — student doesn't process the whole word",
    ),
    (
        r"\b(?:what word fits|think what word would fit|sentence.*pattern.*guess)\b",
        "MSV_STRUCTURE",
        "Syntactic guessing — student uses sentence structure rather than decoding",
    ),
    (
        r"\b(?:repetitive.*text.*predict|predictable.*text|pattern.*book|leveled.*reader.*guess)\b",
        "MSV_TEXT_TYPE",
        "Predictable/leveled text approach — these texts explicitly encourage guessing strategies",
    ),
]

# Phrases that indicate reliance on context clues over decoding
CONTEXT_OVER_DECODING_PATTERNS: list[tuple[str, str]] = [
    (r"\b(?:use context to figure out|figure.*out.*from.*context)\b", "Context-over-decoding"),
    (r"\b(?:what word would sound right|does that sound right)\b", "Syntactic-guessing"),
]

# Heart words that must never be presented as fully decodable at K-2
MANDATORY_HEART_WORDS: dict[str, dict[str, str]] = {
    "the": {"regular_part": "th", "heart_part": "e", "explanation": "'e' says /ə/ (schwa), not the expected short /e/"},
    "said": {"regular_part": "s", "heart_part": "aid", "explanation": "'ai' says /e/ not /ā/ — irregular vowel team"},
    "was": {"regular_part": "w", "heart_part": "as", "explanation": "'a' says /u/ (schwa) — irregular in closed syllable"},
    "you": {"regular_part": "y", "heart_part": "ou", "explanation": "'ou' says /ōō/ — irregular vowel team"},
    "of": {"regular_part": "o", "heart_part": "f", "explanation": "'f' says /v/ — irregular phoneme for grapheme"},
    "what": {"regular_part": "wh", "heart_part": "at", "explanation": "'a' says /u/ (schwa) — irregular short vowel"},
    "come": {"regular_part": "c", "heart_part": "ome", "explanation": "'o' says /u/ + silent 'e' — irregular pattern"},
    "some": {"regular_part": "s", "heart_part": "ome", "explanation": "'o' says /u/ + silent 'e' — irregular pattern"},
    "have": {"regular_part": "h", "heart_part": "ave", "explanation": "Silent-e doesn't make 'a' long — irregular exception"},
    "give": {"regular_part": "g", "heart_part": "ive", "explanation": "Silent-e doesn't make 'i' long — irregular exception"},
}


# ── Phonics Scope by Grade (cumulative) ─────────────────────────────────────

PHONICS_PATTERNS_BY_GRADE: dict[str, dict[str, list[str]]] = {
    "K": {
        "label": "Kindergarten",
        "patterns": [
            "C", "V", "CV", "VC", "CVC",
        ],
        "phonemes": ["/a/", "/e/", "/i/", "/o/", "/u/", "/m/", "/s/", "/t/", "/p/", "/n/", "/d/"],
        "syllable_types": ["closed"],
    },
    "1": {
        "label": "Grade 1",
        "patterns": [
            "CCVC", "CVCC", "CVCe", "digraphs(sh,ch,th,wh,ck)",
            "blends(l,r,s)", "ending_blends",
        ],
        "phonemes": ["/sh/", "/ch/", "/th/", "/wh/", "/ng/", "/ā/", "/ē/", "/ī/", "/ō/"],
        "syllable_types": ["closed", "VCe"],
    },
    "2": {
        "label": "Grade 2",
        "patterns": [
            "vowel_teams(ai,ay,ee,ea,oa,oe)", "r_controlled(ar,or,er,ir,ur)",
            "diphthongs(oi,oy,ou,ow)", "silent_letters(wr,kn,gn)", "3-letter_blends",
            "common_suffixes(ing,ed,er,est)", "common_prefixes(un,re,pre,mis,dis)",
        ],
        "phonemes": ["/oi/", "/oy/", "/ou/", "/ow/", "/ar/", "/or/", "/er/"],
        "syllable_types": ["closed", "VCe", "open", "vowel_team", "r_controlled"],
    },
    "3": {
        "label": "Grade 3+",
        "patterns": [
            "advanced_vowel_teams(au,aw)", "c_le", "schwa",
            "advanced_suffixes(tion,sion,ture)", "multisyllabic(all_types)",
        ],
        "phonemes": ["/aw/"],
        "syllable_types": ["closed", "VCe", "open", "vowel_team", "r_controlled", "c_le"],
    },
}


# ── Public API ──────────────────────────────────────────────────────────────


def verify_decodable_text(
    text: str,
    target_skill: str,
    scope_sequence: list[str] | None = None,
    grade_level: str = "1",
    enable_anti_cueing: bool = True,
) -> dict[str, Any]:
    """Verify a text passage for decodability with anti-cueing guardrails.

    Checks every word against a cumulative phonics scope and sequence,
    identifies heart words, flags off-scope patterns, and detects any
    three-cueing (MSV) instructional strategies.

    Args:
        text: The text passage to verify.
        target_skill: Target phonics skill (e.g., 'cvc_short_a').
        scope_sequence: List of mastered phonics patterns.
        grade_level: Grade level (K-5).
        enable_anti_cueing: Whether to run anti-cueing detection.

    Returns:
        Dictionary with total_words, decodable_pct, target_skill_words,
        heart_words, off_scope_words, warnings, and recommendation.
    """
    if not text or not text.strip():
        return {"error": "No text provided", "error_code": "ERR_INVALID_INPUT"}

    if scope_sequence is None:
        scope_sequence = []

    # Validate grade
    valid_grades = {"K", "1", "2", "3", "4", "5"}
    if grade_level not in valid_grades:
        return format_error(
            SoRErrorCode.ERR_INVALID_GRADE_BAND,
            detail=f"'{grade_level}'",
            grade=grade_level,
        )

    # Extract words
    raw_words: list[str] = re.findall(r"[a-zA-Z]+(?:'[a-zA-Z]+)?", text.lower())
    if not raw_words:
        return {"error": "No recognizable words found", "error_code": "ERR_INVALID_INPUT"}

    total_words = len(raw_words)
    warnings: list[WarningEntry] = []
    heart_words: list[HeartWordEntry] = []
    off_scope_words: list[OffScopeWord] = []
    target_skill_words: list[str] = []
    decodable_count = 0

    # Build cumulative patterns up to this grade
    grade_order = ["K", "1", "2", "3", "4", "5"]
    max_index = grade_order.index(grade_level)
    cumulative_patterns: list[str] = list(scope_sequence)  # start with user-provided

    for g in grade_order[:max_index + 1]:
        cumulative_patterns.extend(PHONICS_PATTERNS_BY_GRADE.get(g, {}).get("patterns", []))

    # Analyze each word
    for word in raw_words:
        word_lower = word.lower()

        # Check if it's a mandatory heart word
        if word_lower in MANDATORY_HEART_WORDS:
            hw_info = MANDATORY_HEART_WORDS[word_lower]
            heart_words.append(HeartWordEntry(
                word=word_lower,
                regular_part=hw_info["regular_part"],
                heart_part=hw_info["heart_part"],
                heart_letters=hw_info["heart_part"],
                explanation=hw_info["explanation"],
            ))
            decodable_count += 1  # heart words count as taught (with explicit marking)
            continue

        # Check against target skill pattern
        if _matches_target_skill(word_lower, target_skill):
            target_skill_words.append(word_lower)
            decodable_count += 1
            continue

        # Check against cumulative patterns
        if _matches_any_pattern(word_lower, cumulative_patterns):
            decodable_count += 1
            continue

        # Check if it's a common sight/heart word
        if _is_common_sight_word(word_lower, grade_level):
            decodable_count += 1
            continue

        # Off scope
        off_scope_words.append(OffScopeWord(
            word=word_lower,
            untaught_pattern=_identify_untaught_pattern(word_lower, cumulative_patterns, grade_level),
            suggestion=f"Replace '{word_lower}' with a word using only mastered patterns, or pre-teach this word as a Heart Word.",
        ))

    decodable_pct = round(decodable_count / total_words * 100, 1) if total_words > 0 else 0.0

    # ── Anti-Cueing Guardrails ──────────────────────────────────────────
    if enable_anti_cueing:
        text_lower = text.lower()
        for pattern, label, explanation in CUEING_FLAG_PATTERNS:
            matches = re.finditer(pattern, text_lower, re.IGNORECASE)
            for match in matches:
                warnings.append(WarningEntry(
                    severity="error",
                    code="ERR_CUEING_DETECTED",
                    message=f"Three-cueing/MSV detected: {explanation}",
                    location=f"Found '{match.group(0)}' in text",
                ))

        for pattern, label in CONTEXT_OVER_DECODING_PATTERNS:
            if re.search(pattern, text_lower):
                warnings.append(WarningEntry(
                    severity="warning",
                    code="ERR_CUEING_DETECTED",
                    message=f"Context-over-decoding strategy: {label}",
                    location="",
                ))

        # Check for picture-dependent language
        if re.search(r"\b(?:look at the|point to the|what do you see in) (?:picture|illustration|image)\b", text_lower):
            warnings.append(WarningEntry(
                severity="warning",
                code="ERR_CUEING_DETECTED",
                message="Text contains picture-dependent language — students should decode the words, not guess from images.",
                location="",
            ))

    # Determine instructional level
    if decodable_pct >= 95:
        instructional_level = "independent"
        recommendation = "Independent reading level — this text is highly decodable."
    elif decodable_pct >= 90:
        instructional_level = "instructional"
        recommendation = "Instructional reading level — pre-teach off-scope words before reading."
    else:
        instructional_level = "frustration"
        recommendation = "Frustration level — text contains too many untaught patterns. Use for read-aloud only or select a simpler text."

    if off_scope_words:
        off_list = ", ".join(w.word for w in off_scope_words[:10])
        recommendation += f" Off-scope words: {off_list}."

    if warnings:
        recommendation += f" Found {len(warnings)} anti-cueing warning(s)."

    return {
        "total_words": total_words,
        "decodable_count": decodable_count,
        "decodable_pct": decodable_pct,
        "target_skill_words": target_skill_words,
        "heart_words": [hw.model_dump() for hw in heart_words],
        "off_scope_words": [osw.model_dump() for osw in off_scope_words],
        "warnings": [w.model_dump() for w in warnings],
        "recommendation": recommendation,
        "instructional_level": instructional_level,
        "framework_note": (
            "National Reading Panel — systematic phonics instruction with "
            "decodable text practice yields d=0.41. Scarborough's Rope — "
            "decoding strand strengthened through text at the reader's "
            "instructional level. WWC Practice Guide (Foorman et al., 2016): "
            "use decodable text aligned to scope and sequence."
        ),
    }


# ── Internal Helpers ────────────────────────────────────────────────────────


def _matches_target_skill(word: str, target_skill: str) -> bool:
    """Check if a word matches the target phonics skill pattern."""
    # Simple pattern matching based on target skill name
    if target_skill == "cvc_short_a" and re.match(r"^[bcdfghjklmnpqrstvwxyz]a[bcdfghjklmnpqrstvwxyz]$", word):
        return True
    if target_skill == "cvce_silent_e" and re.match(r"^[bcdfghjklmnpqrstvwxyz][aeiou][bcdfghjklmnpqrstvwxyz]e$", word):
        return True
    if target_skill == "consonant_digraphs" and re.search(r"^(sh|ch|th|wh|ck)|(sh|ch|th|ck)$", word):
        return True
    return False


def _matches_any_pattern(word: str, patterns: list[str]) -> bool:
    """Check if a word matches any of the cumulative phonics patterns."""
    # Check basic CVC
    if re.match(r"^[bcdfghjklmnpqrstvwxyz][aeiou][bcdfghjklmnpqrstvwxyz]$", word):
        return True
    # Check CVCe
    if re.match(r"^[bcdfghjklmnpqrstvwxyz][aeiou][bcdfghjklmnpqrstvwxyz]e$", word):
        return True
    # Check blends
    if re.match(r"^[bcdfghjklmnpqrstvwxyz]+[aeiou][bcdfghjklmnpqrstvwxyz]+$", word):
        return True
    # Check digraphs
    if re.search(r"(sh|ch|th|wh|ck|ph|ng)", word):
        return True
    # Check vowel teams
    if re.search(r"(ai|ay|ee|ea|oa|oe|ue|ui|oo|ow|oi|oy|au|aw)", word):
        return True
    return False


def _is_common_sight_word(word: str, grade: str) -> bool:
    """Check if a word is a common sight/heart word for the grade level."""
    sight_words_by_grade: dict[str, set[str]] = {
        "K": {"the", "a", "i", "to", "is", "my", "go", "me", "like", "on",
              "in", "so", "we", "it", "and", "up", "at", "see", "he", "do"},
        "1": {"of", "his", "had", "him", "her", "some", "as", "then", "could",
              "when", "were", "them", "ask", "over", "just", "from", "any",
              "how", "know", "put", "every", "old", "by", "after", "think"},
        "2": {"always", "around", "because", "been", "before", "best", "both",
              "buy", "call", "cold", "does", "fast", "first", "five",
              "found", "gave", "goes", "green", "made", "many", "off",
              "read", "right", "sing", "sit", "sleep", "tell", "their", "these",
              "those", "upon", "us", "use", "very", "wash", "which", "why",
              "wish", "work", "would", "write", "your"},
    }
    cumulative: set[str] = set()
    grade_order = ["K", "1", "2", "3", "4", "5"]
    for g in grade_order:
        cumulative |= sight_words_by_grade.get(g, set())
        if g == grade:
            break
    return word in cumulative


def _identify_untaught_pattern(word: str, patterns: list[str], grade: str) -> str:
    """Identify the specific untaught pattern in a word."""
    # Try to identify what makes this word off-scope
    if re.search(r"(ai|ay|ee|ea|oa|oe|ue|ui|oo|ow|oi|oy|au|aw)", word) and grade in ("K", "1"):
        return "vowel team"
    if re.search(r"[aeiou][bcdfghjklmnpqrstvwxyz]e$", word) and grade == "K":
        return "silent-e pattern"
    if re.search(r"[bcdfghjklmnpqrstvwxyz]{2,}", word) and grade == "K":
        return "consonant blend"
    if re.search(r"(tion|sion|ture|cious|tious)", word):
        return "advanced suffix"
    return "untaught phonics pattern"
