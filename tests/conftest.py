"""Test fixtures for sor-mcp-server API bridge test suite.

Mock the sor.edtechlabs.dev API with respx so tests run without a live API.
"""

from __future__ import annotations

from typing import Any, Generator

import pytest
import respx
from httpx import Response

from src.config import Settings
from src.client.sor_client import SoRClient


# ── Mock API Base URL ───────────────────────────────────────────────────

MOCK_BASE = "https://sor.edtechlabs.dev/api/v1"


@pytest.fixture
def settings() -> Settings:
    """Return test settings pointed at mock base URL."""
    return Settings(
        sor_api_base_url=MOCK_BASE,
        sor_api_key="test-key",
        request_timeout=5.0,
        cache_ttl_seconds=60,
        max_retries=2,
        retry_backoff_base=0.01,  # fast in tests
    )


@pytest.fixture
async def async_client(settings: Settings) -> SoRClient:
    """Create and yield an SoRClient (cleans up after test).

    Use this for standalone async test functions, NOT for class-based tests.
    """
    c = SoRClient(settings)
    try:
        yield c
    finally:
        await c.close()


def make_client(settings: Settings | None = None) -> SoRClient:
    """Create a SoRClient for use in test methods (non-async factory)."""
    s = settings or Settings(
        sor_api_base_url=MOCK_BASE,
        sor_api_key="test-key",
        request_timeout=5.0,
        cache_ttl_seconds=60,
        max_retries=2,
        retry_backoff_base=0.01,
    )
    return SoRClient(s)


# ── Mock Response Fixtures ──────────────────────────────────────────────

PHONICS_SCOPE_RESPONSE: dict[str, Any] = {
    "grade_level": "1",
    "unit": "1",
    "target_phonemes": ["/a/", "/i/", "/o/"],
    "taught_graphemes": ["a", "i", "o", "c", "t", "n", "s", "m", "p"],
    "heart_words": [
        {"word": "the", "regular": "th", "heart": "e says schwa"},
        {"word": "said", "regular": "s", "heart": "ai says /e/"},
    ],
    "unit_objectives": [
        "Decode CVC words with short vowels a, i, o",
        "Blend onset and rime",
        "Read and spell 5 heart words",
    ],
    "prerequisite_skills": [
        "Letter-sound correspondence for consonants m, t, s, p",
        "Phoneme segmentation of 2-3 phoneme words",
    ],
}

DECODABILITY_RESPONSE: dict[str, Any] = {
    "decodable_pct": 96.0,
    "total_words": 25,
    "off_scope_words": [],
    "heart_words": ["the"],
    "substitutions": {},
    "cueing_flags": [],
}

ORTHOGRAPHY_RESPONSE: list[dict[str, Any]] = [
    {
        "word": "cat",
        "phonemes": ["/k/", "/a/", "/t/"],
        "graphemes": ["c", "a", "t"],
        "syllable_breaks": [],
        "syllable_types": ["closed"],
    },
    {
        "word": "chat",
        "phonemes": ["/ch/", "/a/", "/t/"],
        "graphemes": ["ch", "a", "t"],
        "syllable_breaks": [],
        "syllable_types": ["closed"],
    },
    {
        "word": "light",
        "phonemes": ["/l/", "/ī/", "/t/"],
        "graphemes": ["l", "igh", "t"],
        "syllable_breaks": [],
        "syllable_types": ["closed"],
    },
]

COMPETENCY_RESPONSE: list[dict[str, Any]] = [
    {
        "case_guid": "https://case.example/items/ga-ela-g1-rf3a",
        "state_code": "ELAGSE1RF3a",
        "grade": "1",
        "description": (
            "Know the spelling-sound correspondences for common consonant "
            "digraphs (e.g., sh, ch, th, wh)."
        ),
        "strand": "Reading Foundational",
    },
    {
        "case_guid": "https://case.example/items/ga-ela-g1-rf3b",
        "state_code": "ELAGSE1RF3b",
        "grade": "1",
        "description": (
            "Decode regularly spelled one-syllable words with consonant blends "
            "(l-blends, r-blends, s-blends)."
        ),
        "strand": "Reading Foundational",
    },
]


# ── respx Router Fixtures ───────────────────────────────────────────────


@pytest.fixture
def mock_api(respx_mock: respx.MockRouter) -> respx.MockRouter:
    """Set up respx routes for all four API endpoints with realistic responses."""
    # Phonics scope
    respx_mock.get(
        f"{MOCK_BASE}/phonics/scope",
    ).mock(return_value=Response(200, json=PHONICS_SCOPE_RESPONSE))

    # Decodability verification
    respx_mock.post(
        f"{MOCK_BASE}/decodability/verify",
    ).mock(return_value=Response(200, json=DECODABILITY_RESPONSE))

    # Orthography mapping
    respx_mock.get(
        f"{MOCK_BASE}/orthography/map",
    ).mock(return_value=Response(200, json=ORTHOGRAPHY_RESPONSE))

    # Competency lookup
    respx_mock.get(
        f"{MOCK_BASE}/standards/competency",
    ).mock(return_value=Response(200, json=COMPETENCY_RESPONSE))

    return respx_mock


@pytest.fixture
def flaky_api(respx_mock: respx.MockRouter) -> respx.MockRouter:
    """Set up routes that fail twice then succeed on the third attempt."""
    route = respx_mock.get(f"{MOCK_BASE}/phonics/scope")
    route.side_effect = [
        Response(503, json={"error": "Service Unavailable"}),
        Response(503, json={"error": "Service Unavailable"}),
        Response(200, json=PHONICS_SCOPE_RESPONSE),
    ]
    return respx_mock


@pytest.fixture
def error_api(respx_mock: respx.MockRouter) -> respx.MockRouter:
    """Set up routes that return 4xx/5xx errors."""
    respx_mock.get(f"{MOCK_BASE}/phonics/scope").mock(
        return_value=Response(404, json={"error": "Unit not found"})
    )
    respx_mock.post(f"{MOCK_BASE}/decodability/verify").mock(
        return_value=Response(401, json={"error": "Unauthorized"})
    )
    respx_mock.get(f"{MOCK_BASE}/orthography/map").mock(
        return_value=Response(500, json={"error": "Internal Server Error"})
    )
    respx_mock.get(f"{MOCK_BASE}/standards/competency").mock(
        return_value=Response(403, json={"error": "Forbidden"})
    )
    return respx_mock
