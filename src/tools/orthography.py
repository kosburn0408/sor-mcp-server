"""MCP Tool: map_orthography — phoneme-grapheme mapping.

Bridges to GET /api/v1/orthography/map on sor.edtechlabs.dev with local fallback.
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


def _local_orthography_mapper(word: str) -> dict[str, Any]:
    w = word.lower().strip()
    # Simple heuristic mapping for fallback
    vowels = re.findall(r"[aeiouy]+", w)
    syllable_count = max(1, len(vowels))

    # Basic grapheme split
    graphemes = re.findall(r"sh|ch|th|wh|ph|ck|ng|ai|ay|ee|ea|oa|oo|ou|ow|oi|oy|[a-z]", w)
    phonemes = [f"/{g}/" for g in graphemes]

    if w.endswith("e") and len(w) > 3 and not w.endswith("ee"):
        s_type = "VCe"
    elif any(v in w for v in ["ai", "ay", "ee", "ea", "oa", "oo", "ou"]):
        s_type = "vowel_team"
    elif w.endswith("er") or w.endswith("ar") or w.endswith("or"):
        s_type = "r_controlled"
    else:
        s_type = "closed"

    return {
        "word": word,
        "phonemes": phonemes,
        "graphemes": graphemes,
        "syllable_breaks": [w],
        "syllable_types": [s_type],
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

    if client is not None:
        try:
            mappings = await client.map_orthography(words)
            return {
                "status": "ok",
                "total": len(mappings),
                "words": [
                    {
                        "word": m.word,
                        "phonemes": m.phonemes,
                        "graphemes": m.graphemes,
                        "syllable_breaks": m.syllable_breaks,
                        "syllable_types": m.syllable_types,
                    }
                    for m in mappings
                ],
                "source": "sor.edtechlabs.dev",
            }
        except Exception:
            pass  # Fall through to local fallback

    mapped = [_local_orthography_mapper(w) for w in words]
    return {
        "status": "ok",
        "total": len(mapped),
        "words": mapped,
        "source": "local_orthography_engine",
    }
