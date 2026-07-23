"""Tests for MCP prompts — decodable passage generator and phonics routine."""

from __future__ import annotations

import pytest

from src.prompts.decodable import generate_aligned_decodable, DECODABLE_PASSAGE_PROMPT
from src.prompts.phonics import explicit_phonics_routine, EXPLICIT_PHONICS_PROMPT


# ── generate_aligned_decodable ─────────────────────────────────────────


@pytest.mark.asyncio
async def test_decodable_prompt_generation() -> None:
    """Prompt includes grade, unit, topic."""
    result = await generate_aligned_decodable("1", "3", "animals")
    assert "grade 1" in result
    assert "unit 3" in result
    assert "animals" in result
    assert "get_phonics_scope" in result
    assert "verify_decodable_text" in result
    assert "decodable_pct ≥ 95%" in result.replace("\u2265", "≥") or "decodable_pct" in result
    assert "no off-scope words" in result.lower() or "off_scope_words" in result


@pytest.mark.asyncio
async def test_decodable_prompt_default_topic() -> None:
    """Default topic is 'reading'."""
    result = await generate_aligned_decodable("2", "1")
    assert "reading" in result


@pytest.mark.asyncio
async def test_decodable_prompt_anti_cueing() -> None:
    """Prompt explicitly forbids cueing language."""
    result = await generate_aligned_decodable("K", "1", "pets")
    assert "look at the picture" in result.lower()
    assert "does it make sense" in result.lower()
    assert "guess the word" in result.lower()
    assert "sound" in result.lower() or "decode" in result.lower()


@pytest.mark.asyncio
async def test_decodable_prompt_template_placeholders() -> None:
    """Template has the expected format placeholders."""
    assert "{grade}" in DECODABLE_PASSAGE_PROMPT
    assert "{unit}" in DECODABLE_PASSAGE_PROMPT
    assert "{topic}" in DECODABLE_PASSAGE_PROMPT


# ── explicit_phonics_routine ───────────────────────────────────────────


@pytest.mark.asyncio
async def test_phonics_routine_generation() -> None:
    """Prompt includes target phoneme, grade, multisensory cue."""
    result = await explicit_phonics_routine("/a/", "K", "Elkonin boxes")
    assert "/a/" in result
    assert "grade level: K" in result
    assert "Elkonin boxes" in result
    assert "I DO" in result
    assert "WE DO" in result
    assert "YOU DO" in result
    assert "WORD CHAIN" in result
    assert "CORRECTIVE FEEDBACK" in result


@pytest.mark.asyncio
async def test_phonics_routine_defaults() -> None:
    """Default grade and multisensory are used when not specified."""
    result = await explicit_phonics_routine("/sh/")
    assert "/sh/" in result
    assert "grade level: 1" in result
    assert "finger tapping" in result


@pytest.mark.asyncio
async def test_phonics_routine_anti_cueing() -> None:
    """Prompt explicitly forbids cueing strategies."""
    result = await explicit_phonics_routine("/ā/", "1")
    assert "look at the picture" in result.lower()
    assert "does it make sense" in result.lower()
    assert "skip the word" in result.lower()
    assert "3-cueing" in result.lower() or "guessing" in result.lower()


@pytest.mark.asyncio
async def test_phonics_routine_template_placeholders() -> None:
    """Template has the expected format placeholders."""
    assert "{target_phoneme}" in EXPLICIT_PHONICS_PROMPT
    assert "{grade}" in EXPLICIT_PHONICS_PROMPT
    assert "{multisensory}" in EXPLICIT_PHONICS_PROMPT


@pytest.mark.asyncio
async def test_phonics_routine_framework_alignment() -> None:
    """Prompt references SoR theoretical frameworks."""
    result = await explicit_phonics_routine("/ch/", "2")
    assert "Simple View of Reading" in result
    assert "National Reading Panel" in result
    assert "Scarborough" in result
