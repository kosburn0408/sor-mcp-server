"""Tests for SoRClient — async httpx client with retry, caching, and backoff."""

from __future__ import annotations

import httpx
import pytest

from tests.conftest import make_client, MOCK_BASE
from src.client.sor_client import SoRClient
from src.client.cache import TTLCache
from src.config import Settings


# ── TTLCache Tests ──────────────────────────────────────────────────────


class TestTTLCache:
    """Tests for the TTL in-memory cache."""

    def test_get_set(self) -> None:
        """Basic set and get."""
        cache = TTLCache(ttl_seconds=60)
        cache.set("key1", {"data": "value"})
        assert cache.get("key1") == {"data": "value"}

    def test_expiry(self) -> None:
        """Entries expire after TTL."""
        cache = TTLCache(ttl_seconds=0)  # immediately expired
        cache.set("key1", "value")
        assert cache.get("key1") is None

    def test_contains(self) -> None:
        """The __contains__ method respects TTL."""
        cache = TTLCache(ttl_seconds=60)
        cache.set("key1", "value")
        assert "key1" in cache
        assert "nonexistent" not in cache

    def test_clear(self) -> None:
        """clear() removes all entries."""
        cache = TTLCache(ttl_seconds=60)
        cache.set("a", 1)
        cache.set("b", 2)
        assert len(cache) == 2
        cache.clear()
        assert len(cache) == 0

    def test_remove(self) -> None:
        """remove() deletes a specific key."""
        cache = TTLCache(ttl_seconds=60)
        cache.set("a", 1)
        cache.set("b", 2)
        cache.remove("a")
        assert cache.get("a") is None
        assert cache.get("b") == 2

    def test_custom_ttl(self) -> None:
        """Custom TTL per entry overrides default."""
        cache = TTLCache(ttl_seconds=60)
        cache.set("short", "expires", ttl=0)
        cache.set("long", "stays", ttl=3600)
        assert cache.get("short") is None
        assert cache.get("long") == "stays"


# ── SoRClient Tests ─────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_get_phonics_scope(mock_api) -> None:
    """Fetch phonics scope — should return valid data."""
    client = make_client()
    try:
        scope = await client.get_phonics_scope("1", "1")
        assert scope.grade_level == "1"
        assert scope.unit == "1"
        assert "/a/" in scope.target_phonemes
        assert len(scope.taught_graphemes) > 0
        assert len(scope.heart_words) > 0
        assert len(scope.unit_objectives) > 0
    finally:
        await client.close()


@pytest.mark.asyncio
async def test_get_phonics_scope_cached(mock_api) -> None:
    """Second call to get_phonics_scope returns cached result."""
    client = make_client()
    try:
        scope1 = await client.get_phonics_scope("1", "1")
        scope2 = await client.get_phonics_scope("1", "1")
        assert scope1.grade_level == scope2.grade_level
        assert scope1.unit == scope2.unit
    finally:
        await client.close()


@pytest.mark.asyncio
async def test_verify_decodable_text(mock_api) -> None:
    """Verify decodable text — should return decodability result."""
    client = make_client()
    try:
        result = await client.verify_decodable_text(
            "The cat sat on the mat.", "1", "1",
        )
        assert result.decodable_pct == 96.0
        assert result.total_words == 25
        assert result.off_scope_words == []
        assert "the" in result.heart_words
    finally:
        await client.close()


@pytest.mark.asyncio
async def test_map_orthography(mock_api) -> None:
    """Map orthography for multiple words."""
    client = make_client()
    try:
        mappings = await client.map_orthography(["cat", "chat", "light"])
        assert len(mappings) == 3
        assert mappings[0].word == "cat"
        assert mappings[0].phonemes == ["/k/", "/a/", "/t/"]
        assert mappings[0].syllable_types == ["closed"]
    finally:
        await client.close()


@pytest.mark.asyncio
async def test_lookup_competency(mock_api) -> None:
    """Look up competency standards for a skill."""
    client = make_client()
    try:
        matches = await client.lookup_competency("consonant_digraphs", "GA")
        assert len(matches) == 2
        assert matches[0].state_code == "ELAGSE1RF3a"
        assert matches[0].grade == "1"
    finally:
        await client.close()


@pytest.mark.asyncio
async def test_lookup_competency_cached(mock_api) -> None:
    """Second lookup returns cached result."""
    client = make_client()
    try:
        m1 = await client.lookup_competency("consonant_digraphs", "GA")
        m2 = await client.lookup_competency("consonant_digraphs", "GA")
        assert len(m1) == len(m2)
        assert m1[0].case_guid == m2[0].case_guid
    finally:
        await client.close()


# ── Retry / Backoff Tests ──────────────────────────────────────────────


@pytest.mark.asyncio
async def test_retry_on_503(flaky_api) -> None:
    """Client retries on 503 and succeeds on third attempt."""
    client = make_client()
    try:
        scope = await client.get_phonics_scope("1", "1")
        assert scope.grade_level == "1"
        assert "/a/" in scope.target_phonemes
    finally:
        await client.close()


@pytest.mark.asyncio
async def test_error_handling_404(error_api) -> None:
    """404 from API raises HTTPStatusError."""
    client = make_client()
    try:
        with pytest.raises(httpx.HTTPStatusError):
            await client.get_phonics_scope("1", "99")
    finally:
        await client.close()


@pytest.mark.asyncio
async def test_error_handling_401(error_api) -> None:
    """401 from API raises HTTPStatusError."""
    client = make_client()
    try:
        with pytest.raises(httpx.HTTPStatusError):
            await client.verify_decodable_text("test", "1", "1")
    finally:
        await client.close()


# ── Timeout Handling ───────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_timeout_handling() -> None:
    """Client handles timeouts gracefully (retry + error)."""
    import respx

    base = "https://sor.edtechlabs.dev/api/v1"

    async with respx.mock(base_url=base) as respx_mock:
        respx_mock.get("/phonics/scope").mock(
            side_effect=httpx.TimeoutException("timed out")
        )
        s = Settings(
            sor_api_base_url=base,
            request_timeout=0.01,
            max_retries=1,
            retry_backoff_base=0.001,
        )
        c = SoRClient(s)
        try:
            with pytest.raises(httpx.TimeoutException):
                await c.get_phonics_scope("1", "1")
        finally:
            await c.close()
