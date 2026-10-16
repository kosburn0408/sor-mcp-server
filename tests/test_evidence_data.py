"""Tests that the research data matches what the cited sources say, and that seeding works."""

from __future__ import annotations

import duckdb
import pytest

import db.database as database
from db.seed import seed_database
from src.resources.frameworks import FRAMEWORKS
from src.tools.evidence import _interpret_effect_size, list_frameworks, search_evidence


def test_phonics_effect_size_matches_the_ehri_abstract() -> None:
    paper = next(p for p in search_evidence("phonics")["papers"] if p["id"] == 1)
    assert paper["effect_size"] == 0.41
    assert "0.74" not in paper["finding"]


def test_marulis_neuman_is_not_described_as_tier_2_specific() -> None:
    paper = next(p for p in search_evidence("vocabulary")["papers"] if p["id"] == 4)
    assert paper["url"].endswith("0034654310377087")
    assert "does not isolate Tier 2" in paper["finding"]


def test_unverified_or_unreported_effect_sizes_are_null() -> None:
    papers = search_evidence("foundational skills")["papers"]
    guide = next(p for p in papers if p["id"] == 8)
    assert guide["effect_size"] is None
    assert "strong" in guide["finding"]


def test_nrp_pillars_carry_no_invented_effect_sizes() -> None:
    nrp = next(f for f in FRAMEWORKS if f["name"].startswith("National Reading Panel"))
    assert all("effect_size" not in pillar for pillar in nrp["pillars"])
    assert "no vocabulary" not in nrp["evidence_note"] or "ran none" in nrp["evidence_note"]


def test_active_view_is_listed() -> None:
    assert "Active View of Reading" in [f["name"] for f in list_frameworks()["frameworks"]]


def test_effect_size_labels_follow_cohen() -> None:
    assert _interpret_effect_size(0.41).startswith("Small")
    assert _interpret_effect_size(0.53).startswith("Moderate")
    assert _interpret_effect_size(0.88).startswith("Large")


def test_seed_works_on_a_fresh_database(tmp_path, monkeypatch: pytest.MonkeyPatch) -> None:
    path = tmp_path / "fresh.duckdb"
    monkeypatch.setenv("SOR_DB_PATH", str(path))
    monkeypatch.setattr(database, "_connection", None)
    seed_database(path)
    conn = duckdb.connect(str(path), read_only=True)
    try:
        assert conn.execute("SELECT count(*) FROM research_papers").fetchone()[0] >= 10
        columns = [r[0] for r in conn.execute("DESCRIBE research_papers").fetchall()]
        assert "verification" in columns
    finally:
        conn.close()
    monkeypatch.setattr(database, "_connection", None)
