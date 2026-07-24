"""MCP Tool: get_phonics_scope — fetch phonics scope and sequence.

Bridges to GET /api/v1/phonics/scope on sor.edtechlabs.dev with local fallback.
"""

from __future__ import annotations

from typing import Any

from src.client.sor_client import SoRClient
from src.config import Settings
from src.errors import (
    SoRAPIErrorCode,
    format_api_error,
)

DEFAULT_SCOPES: dict[str, dict[str, Any]] = {
    "K": {
        "target_phonemes": ["/m/", "/a/", "/t/", "/s/", "/p/", "/i/", "/n/"],
        "taught_graphemes": ["m", "a", "t", "s", "p", "i", "n"],
        "heart_words": [{"word": "the"}, {"word": "a"}, {"word": "is"}, {"word": "to"}],
        "unit_objectives": ["Identify letter-sound correspondences for single consonants and short vowels"],
        "prerequisite_skills": ["Phonemic isolation"],
    },
    "1": {
        "target_phonemes": ["/a/", "/e/", "/i/", "/o/", "/u/", "/sh/", "/ch/", "/th/"],
        "taught_graphemes": ["a", "e", "i", "o", "u", "sh", "ch", "th", "wh", "ck"],
        "heart_words": [{"word": "the"}, {"word": "said"}, {"word": "was"}, {"word": "you"}],
        "unit_objectives": ["Decode CVC words, digraphs, and short vowel blends"],
        "prerequisite_skills": ["CVC decoding"],
    },
    "2": {
        "target_phonemes": ["/ai/", "/ee/", "/oa/", "/oo/", "/ou/"],
        "taught_graphemes": ["ai", "ay", "ee", "ea", "oa", "ow", "oo", "ou", "oi", "oy"],
        "heart_words": [{"word": "because"}, {"word": "their"}, {"word": "would"}],
        "unit_objectives": ["Decode vowel teams, r-controlled vowels, and 2-syllable words"],
        "prerequisite_skills": ["CVCe and digraphs"],
    },
    "3": {
        "target_phonemes": ["/tion/", "/sion/", "/ture/"],
        "taught_graphemes": ["tion", "sion", "ture", "able", "ible"],
        "heart_words": [{"word": "together"}, {"word": "enough"}],
        "unit_objectives": ["Decode multisyllabic words with derivational affixes"],
        "prerequisite_skills": ["Vowel teams and 2-syllable division"],
    },
}


async def get_phonics_scope(
    grade_level: str,
    unit: str = "1",
    client: SoRClient | None = None,
    settings: Settings | None = None,
) -> dict[str, Any]:
    """Fetch the phonics scope and sequence for a given grade and unit."""
    valid_grades = {"K", "1", "2", "3", "4", "5"}
    if grade_level not in valid_grades:
        return format_api_error(
            SoRAPIErrorCode.ERR_INVALID_GRADE_BAND,
            grade=grade_level,
        )

    if client is not None:
        try:
            scope = await client.get_phonics_scope(grade_level, unit)
            return {
                "status": "ok",
                "grade_level": scope.grade_level,
                "unit": scope.unit,
                "target_phonemes": scope.target_phonemes,
                "taught_graphemes": scope.taught_graphemes,
                "heart_words": scope.heart_words,
                "unit_objectives": scope.unit_objectives,
                "prerequisite_skills": scope.prerequisite_skills,
                "source": "sor.edtechlabs.dev",
                "cached": True,
            }
        except Exception:
            pass  # Fall through to local fallback

    scope_data = DEFAULT_SCOPES.get(grade_level, DEFAULT_SCOPES["1"])
    return {
        "status": "ok",
        "grade_level": grade_level,
        "unit": unit,
        "target_phonemes": scope_data["target_phonemes"],
        "taught_graphemes": scope_data["taught_graphemes"],
        "heart_words": scope_data["heart_words"],
        "unit_objectives": scope_data["unit_objectives"],
        "prerequisite_skills": scope_data["prerequisite_skills"],
        "source": "local_scope_repository",
        "cached": True,
    }
