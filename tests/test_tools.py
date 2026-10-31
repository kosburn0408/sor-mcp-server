"""Tests for MCP tools — bridging to sor.edtechlabs.dev API."""

from __future__ import annotations

import pytest

from tests.conftest import make_client


# ── get_phonics_scope ──────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_get_phonics_scope_success(mock_api) -> None:
    """Successful phonics scope fetch returns structured data."""
    client = make_client()
    try:
        from src.tools.phonics import get_phonics_scope
        result = await get_phonics_scope("1", "1", client=client)
        assert result["status"] == "ok"
        assert result["grade_level"] == "1"
        assert result["unit"] == "1"
        assert "short_a" in result["taught_gpc_ids"]
        assert "tch" in result["taught_graphemes"]
        assert "the" in [hw["word"] for hw in result["heart_words"]]
        assert result["source"] == "default_illustrative_sequence"
    finally:
        await client.close()


@pytest.mark.asyncio
async def test_get_phonics_scope_invalid_grade(mock_api) -> None:
    """Invalid grade returns error."""
    client = make_client()
    try:
        from src.tools.phonics import get_phonics_scope
        result = await get_phonics_scope("X", "1", client=client)
        assert result["error_code"] == "ERR_INVALID_GRADE_BAND"
    finally:
        await client.close()


@pytest.mark.asyncio
async def test_get_phonics_scope_different_units(mock_api) -> None:
    """Different units return data."""
    client = make_client()
    try:
        from src.tools.phonics import get_phonics_scope
        result = await get_phonics_scope("K", "2", client=client)
        assert result["status"] == "ok"
    finally:
        await client.close()


# ── verify_decodable_text ──────────────────────────────────────────────


@pytest.mark.asyncio
async def test_verify_decodable_text_success(mock_api) -> None:
    """Successful decodability verification."""
    client = make_client()
    try:
        from src.tools.decodability import verify_decodable_text
        result = await verify_decodable_text(
            "The cat sat on the mat.", "1", "1", client=client,
        )
        assert result["status"] == "ok"
        assert result["total_words"] == 6
        assert result["accessible_pct"] == 100.0
        assert result["off_scope_words"] == []
        assert result["meets_target"] is True
        assert result["source"] == "local_scope_engine"
    finally:
        await client.close()


@pytest.mark.asyncio
async def test_verify_decodable_text_invalid_grade(mock_api) -> None:
    """Invalid grade returns error."""
    client = make_client()
    try:
        from src.tools.decodability import verify_decodable_text
        result = await verify_decodable_text("test", "X", "1", client=client)
        assert result["error_code"] == "ERR_INVALID_GRADE_BAND"
    finally:
        await client.close()


@pytest.mark.asyncio
async def test_verify_decodable_text_empty(mock_api) -> None:
    """Empty text returns error."""
    client = make_client()
    try:
        from src.tools.decodability import verify_decodable_text
        result = await verify_decodable_text("", "1", "1", client=client)
        assert result["error_code"] == "ERR_INVALID_INPUT"
    finally:
        await client.close()


@pytest.mark.asyncio
async def test_verify_decodable_text_too_long(mock_api) -> None:
    """Text exceeding 5000 chars returns error."""
    client = make_client()
    try:
        from src.tools.decodability import verify_decodable_text
        result = await verify_decodable_text("x" * 6000, "1", "1", client=client)
        assert result["error_code"] == "ERR_INVALID_INPUT"
    finally:
        await client.close()


# ── map_orthography ────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_map_orthography_success(mock_api) -> None:
    """Successful orthography mapping."""
    client = make_client()
    try:
        from src.tools.orthography import map_orthography
        result = await map_orthography(["cat", "chat", "light"], client=client)
        assert result["status"] == "ok"
        assert result["total"] == 3
        assert result["words"][0]["word"] == "cat"
        assert result["words"][0]["phonemes"] == ["/k/", "/ă/", "/t/"]
        assert result["words"][1]["graphemes"] == ["ch", "a", "t"]
        assert result["words"][2]["graphemes"] == ["l", "igh", "t"]
        assert result["words"][0]["syllable_types"] == ["closed"]
        assert result["source"] == "local_orthography_engine"
    finally:
        await client.close()


@pytest.mark.asyncio
async def test_map_orthography_empty_list(mock_api) -> None:
    """Empty word list returns error."""
    client = make_client()
    try:
        from src.tools.orthography import map_orthography
        result = await map_orthography([], client=client)
        assert result["error_code"] == "ERR_INVALID_INPUT"
    finally:
        await client.close()


@pytest.mark.asyncio
async def test_map_orthography_too_many(mock_api) -> None:
    """More than 50 words returns error."""
    client = make_client()
    try:
        from src.tools.orthography import map_orthography
        words = [f"word{i}" for i in range(51)]
        result = await map_orthography(words, client=client)
        assert result["error_code"] == "ERR_INVALID_INPUT"
    finally:
        await client.close()


# ── lookup_competency ──────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_lookup_competency_success(mock_api) -> None:
    """Successful competency lookup."""
    client = make_client()
    try:
        from src.tools.standards import lookup_competency
        result = await lookup_competency("consonant_digraphs", "GA", client=client)
        assert result["status"] == "ok"
        assert result["skill"] == "consonant_digraphs"
        assert result["state"] == "GA"
        assert result["total_matches"] == 2
        assert result["matches"][0]["state_code"] == "ELAGSE1RF3a"
        assert result["matches"][0]["grade"] == "1"
        assert result["source"] == "sor.edtechlabs.dev"
        assert result["cached"] is True
    finally:
        await client.close()


@pytest.mark.asyncio
async def test_lookup_competency_invalid_state(mock_api) -> None:
    """Invalid state returns error."""
    client = make_client()
    try:
        from src.tools.standards import lookup_competency
        result = await lookup_competency("consonant_blends", "XX", client=client)
        assert result["error_code"] == "ERR_INVALID_INPUT"
    finally:
        await client.close()


@pytest.mark.asyncio
async def test_lookup_competency_empty_skill(mock_api) -> None:
    """Empty skill returns error."""
    client = make_client()
    try:
        from src.tools.standards import lookup_competency
        result = await lookup_competency("", "GA", client=client)
        assert result["error_code"] == "ERR_INVALID_INPUT"
    finally:
        await client.close()
