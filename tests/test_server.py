"""End-to-end tests that call the registered MCP tools through server.py.

These guard against wiring bugs (wrong argument names, unserializable return types)
that unit tests on the underlying functions cannot catch.
"""

from __future__ import annotations

import json
from typing import Any

import pytest

import server


@pytest.fixture(autouse=True)
def offline(monkeypatch: pytest.MonkeyPatch) -> None:
    """Force the local engines so tests never touch the network."""
    monkeypatch.setattr(server, "get_client", lambda: None)


async def call(name: str, args: dict[str, Any]) -> dict[str, Any]:
    result = await server.mcp.call_tool(name, args)
    if isinstance(result, tuple):
        return result[1]
    return json.loads(result[0].text)


@pytest.mark.asyncio
async def test_registered_surface() -> None:
    assert len(await server.mcp.list_tools()) == 14
    assert len(await server.mcp.list_prompts()) == 4
    assert len(await server.mcp.list_resources()) == 6


@pytest.mark.asyncio
async def test_evaluate_simple_view_runs_through_mcp() -> None:
    out = await call(
        "evaluate_simple_view",
        {"decoding_score": 0.4, "language_comp_score": 0.8, "student_grade": "1"},
    )
    assert out["diagnostic"]["reading_profile"] == "decoding_weak"
    assert out["remediations"]
    assert "not a diagnosis" in out["diagnostic"]["caveat"]


@pytest.mark.asyncio
@pytest.mark.parametrize("code", ["vowel_teams", "r_controlled", "cvce_silent_e"])
async def test_remediation_cards_exist(code: str) -> None:
    out = await call("get_instructional_remediation", {"deficit_code": code})
    assert out["status"] == "ok"
    assert out["card"]["deficit_code"] == code
    assert out["card"]["evidence_note"]


@pytest.mark.asyncio
async def test_unknown_remediation_code_is_a_structured_error() -> None:
    out = await call("get_instructional_remediation", {"deficit_code": "nope"})
    assert out["error_code"] == "ERR_UNKNOWN_DEFICIT_CODE"
    assert out["available"]


@pytest.mark.asyncio
async def test_match_word_uses_the_corpus() -> None:
    out = await call("match_word", {"word": "dog"})
    assert out["found"] is True
    assert out["tier"] == 1
    assert out["basis"] == "corpus"


@pytest.mark.asyncio
async def test_classify_vocabulary_marks_heuristics() -> None:
    out = await call("classify_vocabulary", {"text": "The tiger will analyze the habitat."})
    habitat = next(w for w in out["tier_3_words"] if w["word"] == "habitat")
    assert habitat["basis"] == "corpus"
    assert out["heuristic_word_count"] >= 1


@pytest.mark.asyncio
async def test_verify_decodable_text_flags_untaught_patterns() -> None:
    out = await call(
        "verify_decodable_text",
        {"text": "The night knight thought about the ocean.", "grade_level": "1"},
    )
    for word in ("night", "knight", "thought"):
        assert word in out["off_scope_words"]


@pytest.mark.asyncio
async def test_search_evidence_only_averages_verified_effect_sizes() -> None:
    out = await call("search_evidence", {"topic": "phonics"})
    assert out["average_effect_size"] == 0.41
    assert all(
        p["verification"] == "verified" for p in out["papers"] if p["effect_size"] is not None
    )
