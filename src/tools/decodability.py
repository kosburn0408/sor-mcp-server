"""Decodable text verifier tool.

Verifies text decodability against phonics scope & sequence, detects 3-cueing
strategies, identifies heart words, and provides decodable substitutions.
Supports both remote API bridge and local DuckDB/Python offline fallback.
"""

from __future__ import annotations

import re
from typing import Any

from src.client.sor_client import SoRClient
from src.config import Settings
from src.errors import SoRAPIErrorCode, format_api_error
from src.tools import scope_engine
from src.tools.scope_engine import (
    all_heart_words,
    analyze_word,
    parse_unit,
    scope_for,
    tokenize,
)

# Union of every taught heart word across grades. Regular words such as "on" or "can"
# are not heart words: they are decodable once their letters are taught.
MANDATORY_HEART_WORDS: set[str] = all_heart_words()

GRADE_MAP: dict[str, str] = {
    "K": "K", "KINDERGARTEN": "K",
    "1": "1", "1ST": "1", "GRADE 1": "1", "GRADE1": "1",
    "2": "2", "2ND": "2", "GRADE 2": "2", "GRADE2": "2",
    "3": "3", "3RD": "3", "GRADE 3": "3", "GRADE3": "3",
    "4": "4", "4TH": "4", "GRADE 4": "4", "GRADE4": "4",
    "5": "5", "5TH": "5", "GRADE 5": "5", "GRADE5": "5",
}

# Small, curated swaps. Each candidate is re-checked against the same scope before it is
# offered, so a swap is only suggested when it is decodable at that grade and unit.
SUBSTITUTION_CANDIDATES: dict[str, list[str]] = {
    "happy": ["glad"], "huge": ["big"], "large": ["big"], "quickly": ["fast"], "quick": ["fast"],
    "jump": ["hop"], "ocean": ["sea"], "puppy": ["pup"], "kitten": ["cat"], "mother": ["mom"],
    "father": ["dad"], "yacht": ["boat"], "children": ["kids"], "child": ["kid"],
    "beautiful": ["fine"], "little": ["small", "tiny"], "walk": ["go"], "house": ["home"],
    "friend": ["pal"], "tiny": ["small"], "begin": ["start"], "finish": ["end"],
    "shout": ["yell"], "enormous": ["big"], "chilly": ["cold"], "unhappy": ["sad"],
}

_GUESSING_PROMPTS = [
    (r"\blook at the (picture|pictures|photo|photos|illustration)\b", "picture-based prompt"),
    (r"\b(use|using) the (picture|pictures|context|clues?)\b", "picture or context prompt"),
    (r"\bguess\b", "guessing prompt"),
    (r"\bwhat (word )?(do you think|would make sense|looks right|fits)\b", "meaning-based word prompt"),
    (r"\bskip (the|that|this) word\b", "skip-the-word prompt"),
    (r"\bfirst letter and the (picture|context)\b", "first-letter-plus-picture prompt"),
]

LIMITATIONS = [
    "Orthographic heuristic: spelling is checked against taught graphemes, not pronunciation, "
    "so teach exceptions as heart words.",
    "Default scope and sequence is a common ordering, not your program's. Check results against "
    "your own materials.",
]


def _cueing_flags(text: str, words: list[str], pct: float) -> list[dict[str, str]]:
    """Heuristic flags for text features that invite guessing instead of decoding."""
    flags: list[dict[str, str]] = []
    lowered = text.lower()
    for pattern, label in _GUESSING_PROMPTS:
        if re.search(pattern, lowered):
            flags.append({"type": "guessing_prompt", "detail": f"Found a {label}. Teach students to decode from the letters instead."})
    if words and pct < 90.0:
        flags.append({
            "type": "high_guessing_risk",
            "detail": f"Only {pct:.0f}% of words are decodable or taught heart words, so students are likely to guess from pictures or context.",
        })
    sentences = [s.split() for s in re.split(r"[.!?]+\s*", lowered) if len(s.split()) >= 4]
    run = 1
    for prev, cur in zip(sentences, sentences[1:]):
        run = run + 1 if prev[:-1] == cur[:-1] else 1
        if run >= 3:
            flags.append({
                "type": "repeated_sentence_frame",
                "detail": "Three or more sentences repeat one frame with a single changing word. Predictable text invites memorizing and guessing.",
            })
            break
    return flags


def _substitutions(off_scope: list[str], scope: dict[str, Any]) -> dict[str, list[str]]:
    subs: dict[str, list[str]] = {}
    for word in off_scope:
        ok = [
            cand for cand in SUBSTITUTION_CANDIDATES.get(word, [])
            if analyze_word(cand, scope)["status"] != "off_scope"
        ]
        if ok:
            subs[word] = ok
    return subs


def check_decodability(
    text: str,
    grade_level: str = "1",
    target_skill: str = "cvc",
    unit: str | int | None = None,
) -> dict[str, Any]:
    """Check text decodability against a cumulative grapheme scope (local engine).

    Args:
        text: Passage to check.
        grade_level: K-5 (several spellings accepted).
        target_skill: Free-text label carried through to the result.
        unit: Optional unit (1-10) within the grade. When omitted the whole grade is taught.
    """
    if not text or not text.strip():
        return {"error_code": "ERR_INVALID_INPUT", "message": "Text is empty"}

    raw_grade = str(grade_level).strip().upper()
    grade = GRADE_MAP.get(raw_grade)
    if not grade:
        return format_api_error(SoRAPIErrorCode.ERR_INVALID_GRADE_BAND, grade=grade_level)

    words = tokenize(text)
    if not words:
        return {"error_code": "ERR_INVALID_INPUT", "message": "No valid words found"}

    unit_n = parse_unit(unit)
    scope = scope_for(grade, unit_n)
    permissive = grade in ("4", "5")

    analysis: dict[str, dict[str, Any]] = {}
    decodable_count = 0
    regular_count = 0
    heart_count = 0
    off_scope: list[str] = []
    heart_words_found: list[str] = []

    for w in words:
        if w not in analysis:
            analysis[w] = (
                {"word": w, "status": "decodable", "reason": "grade 4-5 not modeled"}
                if permissive else analyze_word(w, scope)
            )
        status = analysis[w]["status"]
        if status == "decodable":
            decodable_count += 1
            regular_count += 1
        elif status == "heart_word":
            decodable_count += 1
            heart_count += 1
            if w not in heart_words_found:
                heart_words_found.append(w)
        else:
            off_scope.append(w)

    total = len(words)
    pct = round((decodable_count / total) * 100.0, 1)

    if pct >= 95:
        level = "independent"
    elif pct >= 90:
        level = "instructional"
    else:
        level = "frustration"

    off_unique = sorted(set(off_scope))
    warnings: list[str] = []
    if permissive:
        warnings.append("Grade 4-5 decodability is not modeled; every word was treated as in scope.")

    return {
        "status": "ok",
        "decodable_pct": pct,
        "regular_decodable_pct": round(regular_count / total * 100.0, 1),
        "heart_word_pct": round(heart_count / total * 100.0, 1),
        "total_words": total,
        "decodable_count": decodable_count,
        "off_scope_words": off_unique,
        "heart_words": heart_words_found,
        "instructional_level": level,
        "level_note": (
            "Level labels reuse the 95% / 90% accuracy bands from running records. They are a "
            "rule of thumb for how many words students can read without guessing, not a "
            "research-validated decodability cutoff."
        ),
        "cueing_flags": _cueing_flags(text, words, pct),
        "substitutions": _substitutions(off_unique, scope),
        "word_analysis": list(analysis.values()),
        "grade_level": grade,
        "unit": unit_n,
        "target_skill": target_skill,
        "scope_model": "cumulative_grapheme_scope_v2",
        "scope_name": scope_engine.SCOPE_NAME,
        "scope_groups_taught": scope["groups"],
        "warnings": warnings,
        "limitations": LIMITATIONS,
        "source": "local_scope_engine",
    }


async def verify_decodable_text(
    text: str,
    grade_level: str,
    unit: str | None = None,
    client: SoRClient | None = None,
    settings: Settings | None = None,
) -> dict[str, Any]:
    """Verify text decodability asynchronously via API with local fallback."""
    raw_grade = str(grade_level).strip().upper()
    grade = GRADE_MAP.get(raw_grade)
    if not grade:
        return format_api_error(SoRAPIErrorCode.ERR_INVALID_GRADE_BAND, grade=grade_level)

    if not text or not text.strip():
        return format_api_error(SoRAPIErrorCode.ERR_INVALID_INPUT, detail="text is empty")

    if len(text) > 5000:
        return format_api_error(
            SoRAPIErrorCode.ERR_INVALID_INPUT,
            detail=f"text exceeds 5000 character limit ({len(text)} chars)",
        )

    if client is not None:
        try:
            result = await client.verify_decodable_text(text, grade, unit or "1")
            level = "independent" if result.decodable_pct >= 95 else ("instructional" if result.decodable_pct >= 90 else "frustration")
            return {
                "status": "ok",
                "decodable_pct": result.decodable_pct,
                "total_words": result.total_words,
                "off_scope_words": result.off_scope_words,
                "heart_words": result.heart_words,
                "substitutions": result.substitutions,
                "cueing_flags": result.cueing_flags,
                "warnings": [],
                "instructional_level": level,
                "recommendation": _get_recommendation(level, result.decodable_pct),
                "grade_level": grade,
                "unit": unit,
                "source": "sor.edtechlabs.dev",
            }
        except Exception:
            pass

    local_res = check_decodability(text, grade, unit=unit)
    if "error_code" in local_res:
        return local_res
    pct = local_res["decodable_pct"]
    level = local_res["instructional_level"]
    local_res["recommendation"] = _get_recommendation(level, pct)
    return local_res


def _get_recommendation(level: str, pct: float) -> str:
    if level == "independent":
        return f"{pct:.0f}% of words are decodable or taught heart words. Students can practice this text without guessing."
    elif level == "instructional":
        return f"{pct:.0f}% decodable. Use with teacher support and pre-teach the off-scope words."
    else:
        return f"{pct:.0f}% decodable. Too many untaught words; revise or swap the off-scope words."
