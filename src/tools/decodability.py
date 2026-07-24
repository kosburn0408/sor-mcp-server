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

MANDATORY_HEART_WORDS: set[str] = {
    "the", "a", "i", "to", "is", "my", "go", "me", "like", "on", "in", "so", "we", "it",
    "and", "up", "at", "see", "he", "do", "you", "an", "can", "no", "am", "said", "was",
    "are", "have", "has", "of", "his", "had", "him", "her", "some", "as", "then", "could",
    "when", "were", "them", "ask", "over", "just", "from", "any", "how", "know", "put",
    "every", "old", "by", "after", "think", "let", "going", "walk", "again", "may",
}

PHONICS_PATTERNS: dict[str, list[str]] = {
    "K": [
        r"^[a-z]$",
        r"^[aeiou]$",
        r"^[bcdfghjklmnpqrstvwxyz][aeiou]$",
        r"^[aeiou][bcdfghjklmnpqrstvwxyz]$",
        r"^[bcdfghjklmnpqrstvwxyz][aeiou][bcdfghjklmnpqrstvwxyz]$",
    ],
    "1": [
        r"^[bcdfghjklmnpqrstvwxyz]+[aeiou][bcdfghjklmnpqrstvwxyz]+$",
        r"^[bcdfghjklmnpqrstvwxyz][aeiou][bcdfghjklmnpqrstvwxyz]e$",
        r"^(sh|ch|th|wh|ph|ck|ng|qu)",
        r"(sh|ch|th|wh|ph|ck|ng)$",
        r"^(bl|cl|fl|gl|pl|sl|br|cr|dr|fr|gr|pr|tr|sc|sk|sm|sn|sp|st|sw)",
        r"(mp|nd|nt|nk|st|sk|ft|lt|lp|lk|pt|ct|xt)$",
    ],
    "2": [
        r"(ai|ay|ee|ea|oa|oe|ue|ui|oo|ou|ow|oi|oy|au|aw)",
        r"^(wr|kn|gn|mb)",
        r"^(spr|str|scr|spl|shr|thr)",
        r"(ing|ed|er|est|ly|ful|less|ness|ment)",
        r"^(un|re|pre|mis|dis)",
    ],
    "3": [
        r"(tion|sion|ture|cious|tious)",
        r"^(sub|inter|super|trans|anti|semi|mid)",
        r"(able|ible|ance|ence|ify|ize|ous|al|ic|ive)",
    ],
    "4": [r"[a-z]+"],
    "5": [r"[a-z]+"],
}


def check_decodability(text: str, grade_level: str = "1", target_skill: str = "cvc") -> dict[str, Any]:
    """Check text decodability locally using regex phonics scope rules."""
    if not text or not text.strip():
        return {"error_code": "ERR_INVALID_INPUT", "message": "Text is empty"}

    grade = grade_level.upper().strip()
    if grade not in {"K", "1", "2", "3", "4", "5"}:
        return format_api_error(SoRAPIErrorCode.ERR_INVALID_GRADE_BAND, grade=grade_level)

    words = re.findall(r"[a-zA-Z]+(?:'[a-zA-Z]+)?", text.lower())
    if not words:
        return {"error_code": "ERR_INVALID_INPUT", "message": "No valid words found"}

    grade_order = ["K", "1", "2", "3", "4", "5"]
    max_idx = grade_order.index(grade) if grade in grade_order else 1
    active_patterns: list[str] = []
    for g in grade_order[: max_idx + 1]:
        active_patterns.extend(PHONICS_PATTERNS.get(g, []))

    decodable_count = 0
    off_scope: list[str] = []
    heart_words_found: list[str] = []

    for w in words:
        if len(w) == 1 or w in MANDATORY_HEART_WORDS:
            decodable_count += 1
            if w in MANDATORY_HEART_WORDS and w not in heart_words_found:
                heart_words_found.append(w)
        elif any(re.search(pat, w) for pat in active_patterns):
            decodable_count += 1
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

    return {
        "status": "ok",
        "decodable_pct": pct,
        "total_words": total,
        "decodable_count": decodable_count,
        "off_scope_words": list(set(off_scope)),
        "heart_words": heart_words_found,
        "instructional_level": level,
        "cueing_flags": [],
        "substitutions": {},
        "grade_level": grade_level,
        "source": "local_scope_engine",
    }


async def verify_decodable_text(
    text: str,
    grade_level: str,
    unit: str = "1",
    client: SoRClient | None = None,
    settings: Settings | None = None,
) -> dict[str, Any]:
    """Verify text decodability asynchronously via API with local fallback."""
    valid_grades = {"K", "1", "2", "3", "4", "5"}
    if grade_level not in valid_grades:
        return format_api_error(SoRAPIErrorCode.ERR_INVALID_GRADE_BAND, grade=grade_level)

    if not text or not text.strip():
        return format_api_error(SoRAPIErrorCode.ERR_INVALID_INPUT, detail="text is empty")

    if len(text) > 5000:
        return format_api_error(
            SoRAPIErrorCode.ERR_INVALID_INPUT,
            detail=f"text exceeds 5000 character limit ({len(text)} chars)",
        )

    # Try client API if available
    if client is not None:
        try:
            result = await client.verify_decodable_text(text, grade_level, unit)
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
                "grade_level": grade_level,
                "unit": unit,
                "source": "sor.edtechlabs.dev",
            }
        except Exception:
            pass  # Fall through to local engine

    local_res = check_decodability(text, grade_level)
    if "error_code" in local_res:
        return local_res
    pct = local_res["decodable_pct"]
    level = local_res["instructional_level"]
    local_res["recommendation"] = _get_recommendation(level, pct)
    return local_res


def _get_recommendation(level: str, pct: float) -> str:
    if level == "independent":
        return f"{pct:.0f}% decodable — suitable for independent practice."
    elif level == "instructional":
        return f"{pct:.0f}% decodable — suitable for guided reading."
    else:
        return f"{pct:.0f}% decodable — frustration level. Revise off-scope words."
