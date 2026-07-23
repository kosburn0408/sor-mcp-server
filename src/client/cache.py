"""TTL-based in-memory cache for API responses.

Simple dict-backed cache with per-key expiry. Suitable for static or
slow-changing data like phonics scopes and CASE competency GUIDs.
"""

from __future__ import annotations

import time
from typing import Any


class TTLCache:
    """Time-to-live in-memory cache for API responses.

    Thread-safe for single-worker MCP usage. Keys are strings; values can be
    any JSON-serializable object. Expired entries are pruned on read.
    """

    def __init__(self, ttl_seconds: int = 300) -> None:
        """Initialize the cache.

        Args:
            ttl_seconds: Default TTL for cached entries (default: 300s / 5min).
        """
        self._store: dict[str, tuple[float, Any]] = {}
        self._ttl = ttl_seconds

    @property
    def ttl(self) -> int:
        return self._ttl

    def get(self, key: str) -> Any | None:
        """Get a cached value if it exists and hasn't expired.

        Args:
            key: Cache key.

        Returns:
            Cached value or None if missing/expired.
        """
        entry = self._store.get(key)
        if entry is None:
            return None
        expires_at, value = entry
        if time.monotonic() >= expires_at:
            del self._store[key]
            return None
        return value

    def set(self, key: str, value: Any, ttl: int | None = None) -> None:
        """Store a value in the cache with an optional custom TTL.

        Args:
            key: Cache key.
            value: Value to cache (must be serializable).
            ttl: Optional custom TTL in seconds (defaults to cache-wide TTL).
        """
        ttl = ttl if ttl is not None else self._ttl
        self._store[key] = (time.monotonic() + ttl, value)

    def clear(self) -> None:
        """Remove all entries from the cache."""
        self._store.clear()

    def remove(self, key: str) -> None:
        """Remove a specific key from the cache."""
        self._store.pop(key, None)

    def __len__(self) -> int:
        return len(self._store)

    def __contains__(self, key: str) -> bool:
        return self.get(key) is not None
