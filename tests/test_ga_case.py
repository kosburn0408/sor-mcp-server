"""Tests for live Georgia K-12 ELA standards lookup (CASE)."""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest

from src.tools.evidence import align_standards
from src.tools.ga_case import foundations_items, load_package, search_ga_foundations

FIXTURE = Path(__file__).parent / "fixtures" / "ga_ela_case_sample.json"


@pytest.fixture
def cached_package(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Path:
    dest = tmp_path / "ga.json"
    shutil.copy(FIXTURE, dest)
    monkeypatch.setenv("SOR_GA_CASE_CACHE", str(dest))
    return dest


def test_foundations_filter(cached_package: Path) -> None:
    pkg, source = load_package()
    assert source == "cache"
    codes = {i["code"] for i in foundations_items(pkg)}
    assert "K.F.P.2" in codes and "1.F.P.2.1" in codes
    assert "K.L.GC.1" not in codes  # not Foundations
    assert "K.F" not in codes  # domain itself excluded


def test_search_phonics_by_grade(cached_package: Path) -> None:
    r = search_ga_foundations("decode words with silent e", grade="1")
    assert r["matches"][0]["code"] == "1.F.P.2"
    assert r["strands_searched"] == ["Phonics"]


def test_search_phonological_awareness(cached_package: Path) -> None:
    r = search_ga_foundations("segment phonemes in spoken words", grade="K")
    assert r["matches"][0]["code"] == "K.F.PA.1"


def test_statement_title_split(cached_package: Path) -> None:
    r = search_ga_foundations("decoding cvc words", grade="K")
    top = r["matches"][0]
    assert top["title"] == "Decoding words"
    assert top["statement"].startswith("FIXTURE")


def test_align_standards_uses_live_georgia(cached_package: Path) -> None:
    r = align_standards("decode words with silent e", "GA", "1")
    assert r["matches"][0]["code"] == "1.F.P.2"
    assert r["matches"][0]["url"].startswith("https://case.georgiastandards.org/")
    assert "Current Georgia K-12 ELA standards" in r["notices"][0]


def test_falls_back_to_legacy_when_unavailable() -> None:
    r = align_standards("decode words with silent e", "GA")
    assert any("legacy" in n for n in r["notices"])
    assert r["matches"]
