"""MCP Tool: map_orthography — phoneme-grapheme mapping.

Bridges to GET /api/v1/orthography/map on sor.edtechlabs.dev.
"""

from __future__ import annotations

from typing import Any

from src.client.sor_client import SoRClient
from src.config import Settings
from src.errors import (
    SoRAPIErrorCode,
    format_api_error,
)
from src.schemas.api import OrthographyMap


async def map_orthography(
    words: list[str],
    client: SoRClient | None = None,
    settings: Settings | None = None,
) -> dict[str, Any]:
    """Map words to their orthographic structure (phonemes, graphemes, syllables).

    For each word, returns phoneme sequence, grapheme sequence, syllable
    breaks, and syllable types. Based on structured literacy / Orton-Gillingham
    syllable division rules.

    Args:
        words: List of words to map (max 50).
        client: Optional pre-configured SoRClient.
        settings: Optional Settings.

    Returns:
        Dict with 'words' array of OrthographyMap entries and total count.
    """
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

    if client is None:
        client = SoRClient(settings or Settings())

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
    except Exception as exc:
        return format_api_error(
            SoRAPIErrorCode.ERR_UPSTREAM_REGISTRY_UNAVAILABLE,
            detail=str(exc),
        )
