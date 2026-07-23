"""Test fixtures and conftest for SoR MCP server pytest test suite."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Generator

import pytest

FIXTURES_DIR = Path(__file__).resolve().parent.parent / "tests" / "fixtures"


@pytest.fixture(scope="session")
def sample_scope() -> dict[str, Any]:
    """Load sample K-2 phonics scope and sequence from fixtures."""
    scope_path = FIXTURES_DIR / "sample_scope.json"
    if scope_path.exists():
        with open(scope_path) as f:
            return json.load(f)
    return _default_scope()


@pytest.fixture
def k_scope(sample_scope: dict[str, Any]) -> dict[str, Any]:
    """Kindergarten scope data."""
    return sample_scope["grade_levels"]["K"]["strands"]["phonology"]


@pytest.fixture
def g1_scope(sample_scope: dict[str, Any]) -> dict[str, Any]:
    """Grade 1 scope data."""
    return sample_scope["grade_levels"]["1"]["strands"]["phonology"]


@pytest.fixture
def g2_scope(sample_scope: dict[str, Any]) -> dict[str, Any]:
    """Grade 2 scope data."""
    return sample_scope["grade_levels"]["2"]["strands"]["phonology"]


@pytest.fixture
def sample_decodable_text() -> str:
    """Simple decodable text for testing."""
    return "The cat sat on the mat. Pat has a hat."


@pytest.fixture
def cued_text() -> str:
    """Text that contains 3-cueing language (should be flagged)."""
    return (
        "When you read this story, look at the picture to figure out "
        "the words. Does it make sense? Skip it and go on if you're stuck."
    )


@pytest.fixture
def clean_decodable_text() -> str:
    """Fully decodable text with no cueing or off-scope patterns."""
    return "Pat and Max sat on the mat. The cat is big."


@pytest.fixture
def multisyllabic_words() -> list[str]:
    """Sample multisyllabic words for division tests."""
    return ["rabbit", "fantastic", "tiger", "table", "sunset"]


@pytest.fixture
def remediation_codes(sample_scope: dict[str, Any]) -> list[str]:
    """Available remediation codes from scope data."""
    return sample_scope.get("remediation_codes", [
        "cvc_short_a", "cvc_mixed", "cvce_silent_e",
        "consonant_blends", "consonant_digraphs",
    ])


def _default_scope() -> dict[str, Any]:
    """Fallback scope data if fixture file is missing."""
    return {
        "grade_levels": {
            "K": {"strands": {"phonology": {"concepts": ["CVC"], "phonemes": ["/a/"], "patterns": ["CVC"]}}},
            "1": {"strands": {"phonology": {"concepts": ["CVCe"], "phonemes": ["/ā/"], "patterns": ["CVCe"]}}},
            "2": {"strands": {"phonology": {"concepts": ["vowel_teams"], "phonemes": ["/ā/", "/ē/"], "patterns": ["vowel_teams"]}}},
        },
        "remediation_codes": ["cvc_short_a", "cvc_mixed", "cvce_silent_e"],
        "cueing_flag_phrases": ["look at the picture", "does it make sense"],
    }
