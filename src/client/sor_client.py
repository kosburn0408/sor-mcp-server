"""Async httpx client for sor.edtechlabs.dev API.

Provides connection pooling, exponential backoff retry, TTL caching for
static lookups, and structured error handling.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any

import httpx

from src.config import Settings
from src.client.cache import TTLCache
from src.errors import (
    SoRAPIErrorCode,
    format_api_error,
)
from src.schemas.api import (
    PhonicsScope,
    DecodabilityResult,
    OrthographyMap,
    StandardMatch,
)

logger = logging.getLogger(__name__)


class SoRClient:
    """Async HTTP client for the Science of Reading API at sor.edtechlabs.dev.

    Features:
    - Connection pooling via httpx.AsyncClient
    - Exponential backoff with jitter: 1s, 2s, 4s (up to max_retries)
    - TTL in-memory cache for GET endpoints (phonics scopes, CASE GUIDs)
    - Structured error codes for 4xx/5xx responses
    """

    def __init__(self, settings: Settings | None = None) -> None:
        """Initialize the client.

        Args:
            settings: Configuration (loads from env if None).
        """
        self._settings = settings or Settings()
        self._cache = TTLCache(ttl_seconds=self._settings.cache_ttl_seconds)
        self._client: httpx.AsyncClient | None = None

    @property
    def base_url(self) -> str:
        return self._settings.sor_api_base_url.rstrip("/")

    async def _get_client(self) -> httpx.AsyncClient:
        """Lazy-init the httpx client with connection pooling."""
        if self._client is None or self._client.is_closed:
            headers: dict[str, str] = {
                "Accept": "application/json",
                "User-Agent": "sor-mcp-server/2.0",
            }
            if self._settings.sor_api_key:
                headers["Authorization"] = f"Bearer {self._settings.sor_api_key}"

            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                timeout=self._settings.request_timeout,
                headers=headers,
                limits=httpx.Limits(max_keepalive_connections=5, max_connections=20),
            )
        return self._client

    async def close(self) -> None:
        """Close the underlying httpx client."""
        if self._client and not self._client.is_closed:
            await self._client.aclose()
            self._client = None

    # ── Retry / Backoff ──────────────────────────────────────────────────

    async def _request_with_retry(
        self,
        method: str,
        path: str,
        **kwargs: Any,
    ) -> httpx.Response:
        """Execute an HTTP request with exponential backoff retry.

        Retries on 5xx, connection errors, and timeouts. Does NOT retry 4xx.
        Backoff: base * 2^attempt with ±10% jitter.
        """
        client = await self._get_client()
        last_exc: Exception | None = None

        for attempt in range(self._settings.max_retries + 1):
            try:
                response = await client.request(method, path, **kwargs)
                if response.status_code < 500:
                    return response
                # 5xx — retryable
                if attempt < self._settings.max_retries:
                    wait = self._settings.retry_backoff_base * (2**attempt)
                    jitter = wait * 0.1 * (hash(str(attempt)) % 100) / 100
                    wait += jitter
                    logger.warning(
                        "Server error %d on %s %s (attempt %d/%d), retrying in %.2fs",
                        response.status_code,
                        method,
                        path,
                        attempt + 1,
                        self._settings.max_retries,
                        wait,
                    )
                    await asyncio.sleep(wait)
                else:
                    return response
            except (httpx.TimeoutException, httpx.ConnectError, httpx.RemoteProtocolError) as exc:
                last_exc = exc
                if attempt < self._settings.max_retries:
                    wait = self._settings.retry_backoff_base * (2**attempt)
                    jitter = wait * 0.1 * (hash(str(attempt)) % 100) / 100
                    wait += jitter
                    logger.warning(
                        "%s on %s %s (attempt %d/%d), retrying in %.2fs",
                        type(exc).__name__,
                        method,
                        path,
                        attempt + 1,
                        self._settings.max_retries,
                        wait,
                    )
                    await asyncio.sleep(wait)

        # All retries exhausted
        raise last_exc  # type: ignore[misc]

    # ── API Methods ──────────────────────────────────────────────────────

    async def get_phonics_scope(
        self,
        grade_level: str,
        unit: str = "1",
    ) -> PhonicsScope:
        """Fetch phonics scope and sequence for a grade/unit.

        GET /api/v1/phonics/scope?grade={grade}&unit={unit}

        Cached for cache_ttl_seconds.
        """
        cache_key = f"phonics_scope:{grade_level}:{unit}"
        cached = self._cache.get(cache_key)
        if cached is not None:
            return PhonicsScope.model_validate(cached)

        response = await self._request_with_retry(
            "GET",
            "/phonics/scope",
            params={"grade": grade_level, "unit": unit},
        )
        response.raise_for_status()
        data = response.json()
        self._cache.set(cache_key, data)
        return PhonicsScope.model_validate(data)

    async def verify_decodable_text(
        self,
        text: str,
        grade_level: str,
        unit: str = "1",
    ) -> DecodabilityResult:
        """Verify text decodability against a phonics scope.

        POST /api/v1/decodability/verify
        Body: {text, grade, unit}

        NOT cached (text-dependent, always fresh).
        """
        response = await self._request_with_retry(
            "POST",
            "/decodability/verify",
            json={
                "text": text,
                "grade": grade_level,
                "unit": unit,
            },
        )
        response.raise_for_status()
        return DecodabilityResult.model_validate(response.json())

    async def map_orthography(
        self,
        words: list[str],
    ) -> list[OrthographyMap]:
        """Map words to their orthographic structure.

        GET /api/v1/orthography/map?words=cat,chat,light

        NOT cached (variable word lists).
        """
        response = await self._request_with_retry(
            "GET",
            "/orthography/map",
            params={"words": ",".join(words)},
        )
        response.raise_for_status()
        data = response.json()
        if isinstance(data, list):
            return [OrthographyMap.model_validate(item) for item in data]
        # Handle wrapped response
        items = data.get("words", data.get("results", data if isinstance(data, list) else []))
        if isinstance(items, list):
            return [OrthographyMap.model_validate(item) for item in items]
        return []

    async def lookup_competency(
        self,
        skill: str,
        state: str = "GA",
    ) -> list[StandardMatch]:
        """Look up academic standards for a phonics skill.

        GET /api/v1/standards/competency?skill={skill}&state={state}

        Cached for cache_ttl_seconds.
        """
        cache_key = f"competency:{skill}:{state}"
        cached = self._cache.get(cache_key)
        if cached is not None:
            return [StandardMatch.model_validate(m) for m in cached]

        response = await self._request_with_retry(
            "GET",
            "/standards/competency",
            params={"skill": skill, "state": state},
        )
        response.raise_for_status()
        data = response.json()
        items = data if isinstance(data, list) else data.get("matches", data.get("results", []))
        self._cache.set(cache_key, items)
        return [StandardMatch.model_validate(item) for item in items]

    # ── Error helpers ────────────────────────────────────────────────────

    async def handle_response_error(
        self,
        response: httpx.Response,
        context: str = "",
    ) -> dict[str, Any]:
        """Convert an HTTP error response to a structured error dict."""
        if response.status_code == 401 or response.status_code == 403:
            return format_api_error(SoRAPIErrorCode.ERR_API_AUTH, f"{context}: HTTP {response.status_code}")
        if response.status_code == 404:
            return format_api_error(
                SoRAPIErrorCode.ERR_INVALID_SCOPE_UNIT,
                detail=context,
                grade="?",
                unit="?",
            )
        return format_api_error(
            SoRAPIErrorCode.ERR_UPSTREAM_REGISTRY_UNAVAILABLE,
            detail=f"{context}: HTTP {response.status_code}",
        )
