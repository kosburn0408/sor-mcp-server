"""Tests for the live Georgia CASE lookup (the server is mocked; no network)."""

from __future__ import annotations

import httpx
import pytest
import respx

from src.client import georgia_case
from src.client.georgia_case import GeorgiaCaseError, load_package, parse_package, search_standards
from src.tools.evidence import align_standards

PKG_URL = georgia_case.package_url()


def _item(code: str, statement: str, item_type: str = "Expectation", ident: str | None = None) -> dict:
    ident = ident or code.replace(".", "-")
    return {
        "identifier": ident,
        "uri": f"https://case.georgiastandards.org/ims/case/v1p1/CFItems/{ident}",
        "fullStatement": statement,
        "humanCodingScheme": code,
        "CFItemType": item_type,
        "educationLevel": ["02"],
    }


PACKAGE = {
    "CFDocument": {
        "identifier": georgia_case.DEFAULT_ELA_PACKAGE_ID,
        "title": "English Language Arts - Georgia Department of Education",
        "caseVersion": "1.1",
        "lastChangeDateTime": "2026-07-09T13:12:32+00:00",
    },
    "CFItems": [
        _item("2.F.P.2", "**Decoding with Phonics** Use grade-level phonics skills to decode words in context and in isolation.", "Standard"),
        _item("2.F.P.2.a", "Decode regularly spelled two-syllable words with a variety of spelling patterns (VVCC, VVCe, VCCC, VVCCC) by applying knowledge of basic phonics skills, including high-frequency words."),
        _item("2.F.P.4", "**Decoding & Encoding with Phonics** This progression begins in 3rd grade.", "Standard"),
        _item("1.F.P.2", "**Decoding with Phonics** Use grade-level phonics skills to decode words in context and in isolation.", "Standard"),
        _item("K.F.PA.2", "**Phonemic Awareness** Isolate and segment sounds in spoken words.", "Standard"),
        _item("3.R.1", "Ask and answer questions about a text.", "Standard"),
        {"identifier": "x", "fullStatement": "No code here"},
    ],
}


def test_parse_drops_placeholders_and_cleans_markup() -> None:
    parsed = parse_package(PACKAGE)
    codes = [i["code"] for i in parsed["items"]]
    assert "2.F.P.4" not in codes  # "This progression begins in 3rd grade."
    assert all("**" not in i["statement"] for i in parsed["items"])
    assert parsed["title"].startswith("English Language Arts")
    assert parsed["version"] == "1.1"


def test_parse_rejects_non_case_json() -> None:
    with pytest.raises(GeorgiaCaseError):
        parse_package({"hello": "world"})
    with pytest.raises(GeorgiaCaseError):
        parse_package({"CFDocument": {}, "CFItems": []})


def test_search_ranks_and_filters_by_grade() -> None:
    package = parse_package(PACKAGE)
    found = search_standards(package, "decode two syllable words", grade="2")
    assert found[0]["code"] == "2.F.P.2.a"
    assert all(i["grade"] == "2" for i in found)
    assert search_standards(package, "decode words", grade="K") == []


def test_teacher_wording_maps_to_standard_wording() -> None:
    package = parse_package(PACKAGE)
    found = search_standards(package, "silent e words", grade="2")
    assert found and found[0]["code"] == "2.F.P.2.a"
    assert [i["code"] for i in search_standards(package, "phonemic awareness segment sounds")][0] == "K.F.PA.2"


@respx.mock
def test_load_package_caches_in_memory() -> None:
    route = respx.get(PKG_URL).mock(return_value=httpx.Response(200, json=PACKAGE))
    first = load_package()
    second = load_package()
    assert first is second
    assert route.call_count == 1
    assert first["fetched_from"] == "live"


@respx.mock
def test_load_package_falls_back_to_disk_copy(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("SOR_CASE_CACHE_DIR", str(tmp_path))
    respx.get(PKG_URL).mock(return_value=httpx.Response(200, json=PACKAGE))
    load_package()
    georgia_case.clear_cache()
    respx.get(PKG_URL).mock(return_value=httpx.Response(503))
    again = load_package()
    assert again["fetched_from"] == "disk_cache"
    assert len(again["items"]) >= 4


@respx.mock
def test_server_down_without_cache_raises_clear_error() -> None:
    respx.get(PKG_URL).mock(return_value=httpx.Response(500))
    with pytest.raises(GeorgiaCaseError, match="Could not read Georgia"):
        load_package()


@respx.mock
def test_align_standards_uses_live_data_for_georgia(monkeypatch) -> None:
    monkeypatch.setenv("SOR_CASE_LIVE", "true")
    respx.get(PKG_URL).mock(return_value=httpx.Response(200, json=PACKAGE))
    result = align_standards("decode two-syllable words with silent e", "GA", "2")
    assert result["source"] == "georgia_case_live"
    top = result["matches"][0]
    assert top["code"] == "2.F.P.2.a"
    assert top["case_item_uri"].startswith("https://case.georgiastandards.org/ims/case/v1p1/CFItems/")
    assert result["standards_package"]["case_version"] == "1.1"
    assert "ELAGSE" not in str(result["matches"])


@respx.mock
def test_align_standards_reports_why_it_fell_back(monkeypatch) -> None:
    monkeypatch.setenv("SOR_CASE_LIVE", "true")
    respx.get(PKG_URL).mock(return_value=httpx.Response(500))
    result = align_standards("decode words with silent e", "GA")
    assert result["source"] == "seeded_table"
    assert result["live_case_status"].startswith("unavailable")
    assert "older Georgia code formats" in result["note"]
    assert result["matches"]  # still useful


def test_other_states_and_disabled_mode_never_touch_the_network() -> None:
    with respx.mock(assert_all_called=False) as router:
        route = router.get(PKG_URL)
        align_standards("decode words", "TX")
        align_standards("decode words", "GA")  # live disabled by the autouse fixture
        assert route.call_count == 0
    assert align_standards("decode words", "GA")["live_case_status"] == "disabled"
