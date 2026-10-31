"""MCP Tool: map_orthography — phoneme-grapheme mapping.

Uses the local GPC alignment engine (src/engine/decoder.py); the client
parameter is kept for interface compatibility.
"""

from __future__ import annotations

import re
from typing import Any

from src.client.sor_client import SoRClient
from src.config import Settings
from src.errors import (
    SoRAPIErrorCode,
    format_api_error,
)


def _syllable_type(chunk: str) -> str:
    c = chunk.lower()
    if re.search(r"[aeiou][^aeiouwxy]e$", c):
        return "VCe"
    if re.search(r"[aeiou]r", c):
        return "r_controlled"
    if re.search(r"(ai|ay|ee|ea|oa|oe|ie|igh|oo|ou|ow|oi|oy|au|aw|ew|ue)", c):
        return "vowel_team"
    if re.search(r"[^aeiou]le$", c):
        return "consonant_le"
    if re.search(r"[aeiouy]$", c):
        return "open"
    return "closed"


def _local_orthography_mapper(word: str) -> dict[str, Any]:
    """Map a word to graphemes and phonemes using the GPC alignment engine.

    Alignment is against the CMU Pronouncing Dictionary with every catalogued
    pattern allowed, so it reflects the word itself rather than any scope.
    """
    from src.engine.decoder import analyze_word
    from src.engine.gpc import ALL_GPC_IDS

    result = analyze_word(word, ALL_GPC_IDS)
    graphemes = [m["grapheme"] for m in result["mapping"]]
    phonemes = [m["sound"] for m in result["mapping"]]
    found = bool(result["mapping"])
    return {
        "word": word,
        "phonemes": phonemes,
        "graphemes": graphemes,
        "breakdown": result["breakdown"],
        "patterns": [m["pattern"] for m in result["mapping"]],
        "syllable_breaks": [word.lower()],
        "syllable_types": [_syllable_type(word)],
        "status": "mapped" if found else ("irregular" if result["status"] == "irregular" else "not_in_dictionary"),
    }


async def map_orthography(
    words: list[str],
    client: SoRClient | None = None,
    settings: Settings | None = None,
) -> dict[str, Any]:
    """Map words to their orthographic structure."""
    if not words:
        return format_api_error(
            SoRAPIErrorCode.ERR_INVALID_INPUT,
            detail="words list is empty",
        )

    if len(words) > 50:
        return format_api_error(
            SoRAPIErrorCode.ERR_INVALID_INPUT,
            detail=f"maximum 50 words allowed, got {len(words)}",
        )

    mapped = [_local_orthography_mapper(w) for w in words]
    return {
        "status": "ok",
        "total": len(mapped),
        "words": mapped,
        "source": "local_orthography_engine",
    }
