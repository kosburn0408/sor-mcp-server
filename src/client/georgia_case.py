"""Read Georgia's K-12 ELA standards from the state's CASE server.

Georgia publishes its standards as 1EdTech CASE packages at case.georgiastandards.org.
This module downloads the ELA package, keeps it in memory (and optionally on disk) for a
day, and searches it. Everything here is read-only and uses only the public CASE v1p1
endpoint. If the server cannot be reached, callers fall back to the small seeded table
and say so.

Environment:
  SOR_CASE_LIVE       "false" turns live lookups off (default on).
  SOR_CASE_BASE_URL   Override the server (default https://case.georgiastandards.org).
  SOR_CASE_PACKAGE_ID Override the ELA package id.
  SOR_CASE_CACHE_DIR  Directory for an on-disk copy, used if the server is unreachable.
"""

from __future__ import annotations

import json
import os
import re
import time
from pathlib import Path
from typing import Any

import httpx

DEFAULT_BASE_URL = "https://case.georgiastandards.org"
# "English Language Arts - Georgia Department of Education" (implemented 2025-26)
DEFAULT_ELA_PACKAGE_ID = "391c3abe-c1ec-4a4a-a942-c9e152b35102"
CACHE_TTL_SECONDS = 24 * 60 * 60
REQUEST_TIMEOUT = 8.0

_memory: dict[str, tuple[float, dict[str, Any]]] = {}

_PLACEHOLDER_PHRASES = (
    "this progression begins in",
    "only applies to the",
)
_STOP = {
    "the", "and", "for", "with", "that", "this", "from", "into", "words", "word", "students",
    "student", "use", "using", "skills", "skill", "grade", "level",
}
# Teacher wording -> words that appear in the standards text.
_SYNONYMS = {
    "silent": ["vce", "vvce"],
    "cvce": ["vce", "vvce"],
    "magic": ["vce", "vvce"],
    "blend": ["blends", "blend", "ccvc", "cvcc"],
    "digraph": ["digraphs", "digraph"],
    "phonemic": ["phoneme", "phonemes", "sounds"],
    "phoneme": ["phonemes", "sounds"],
    "decode": ["decode", "decoding"],
    "decoding": ["decode"],
    "vowel": ["vowel", "vowels", "vv"],
    "team": ["vv"],
    "rcontrolled": ["r-controlled"],
    "fluency": ["fluency", "fluently", "accuracy"],
    "syllable": ["syllable", "syllables", "two-syllable"],
    "multisyllabic": ["syllable", "syllables"],
    "encode": ["encode", "spell", "spelling"],
    "spelling": ["encode", "spell"],
}


class GeorgiaCaseError(Exception):
    """The state's CASE server could not be read or returned something unexpected."""


def live_enabled() -> bool:
    return os.environ.get("SOR_CASE_LIVE", "true").strip().lower() not in {"false", "0", "no", "off"}


def _base_url() -> str:
    return os.environ.get("SOR_CASE_BASE_URL", DEFAULT_BASE_URL).rstrip("/")


def package_id() -> str:
    return os.environ.get("SOR_CASE_PACKAGE_ID", DEFAULT_ELA_PACKAGE_ID)


def package_url() -> str:
    return f"{_base_url()}/ims/case/v1p1/CFPackages/{package_id()}"


def clear_cache() -> None:
    _memory.clear()


def _clean(text: str) -> str:
    """Drop the markdown bold markers Georgia uses in some statements."""
    return re.sub(r"\s+", " ", (text or "").replace("**", "")).strip()


def _grade_from_code(code: str) -> str | None:
    head = code.split(".", 1)[0].upper()
    return head if head in {"K", "1", "2", "3", "4", "5"} else None


def parse_package(data: dict[str, Any]) -> dict[str, Any]:
    """Turn a CASE CFPackage into a small, searchable structure."""
    doc = data.get("CFDocument")
    items = data.get("CFItems")
    if not isinstance(doc, dict) or not isinstance(items, list):
        raise GeorgiaCaseError("Response is not a CASE package (missing CFDocument or CFItems).")
    parsed: list[dict[str, Any]] = []
    for raw in items:
        if not isinstance(raw, dict):
            continue
        code = str(raw.get("humanCodingScheme") or "").strip()
        statement = _clean(str(raw.get("fullStatement") or ""))
        if not code or not statement:
            continue
        if any(p in statement.lower() for p in _PLACEHOLDER_PHRASES):
            continue
        parsed.append({
            "identifier": raw.get("identifier"),
            "uri": raw.get("uri"),
            "code": code,
            "statement": statement,
            "item_type": raw.get("CFItemType") or "",
            "grade": _grade_from_code(code),
            "strand": code.split(".")[1] if code.count(".") >= 1 and len(code.split(".")) > 1 else "",
        })
    if not parsed:
        raise GeorgiaCaseError("The CASE package contained no usable standards.")
    return {
        "title": _clean(str(doc.get("title") or "")),
        "version": doc.get("caseVersion") or doc.get("version"),
        "last_change": doc.get("lastChangeDateTime"),
        "package_uri": package_url(),
        "items": parsed,
    }


def _cache_file() -> Path | None:
    directory = os.environ.get("SOR_CASE_CACHE_DIR", "").strip()
    return Path(directory) / f"case-{package_id()}.json" if directory else None


def load_package(client: httpx.Client | None = None, *, force: bool = False) -> dict[str, Any]:
    """Return the parsed ELA package, from memory, the server, or the disk copy."""
    key = package_url()
    now = time.time()
    if not force and key in _memory and now - _memory[key][0] < CACHE_TTL_SECONDS:
        return _memory[key][1]

    owns_client = client is None
    http = client or httpx.Client(timeout=REQUEST_TIMEOUT, follow_redirects=True)
    try:
        response = http.get(key, headers={"Accept": "application/json"})
        response.raise_for_status()
        package = parse_package(response.json())
        package["fetched_from"] = "live"
    except (httpx.HTTPError, ValueError, GeorgiaCaseError) as exc:
        disk = _cache_file()
        if disk and disk.exists():
            try:
                package = parse_package(json.loads(disk.read_text(encoding="utf-8")))
                package["fetched_from"] = "disk_cache"
                _memory[key] = (now, package)
                return package
            except (OSError, ValueError, GeorgiaCaseError):
                pass
        raise GeorgiaCaseError(f"Could not read Georgia's CASE server: {exc}") from exc
    finally:
        if owns_client:
            http.close()

    disk = _cache_file()
    if disk:
        try:
            disk.parent.mkdir(parents=True, exist_ok=True)
            disk.write_text(json.dumps(response.json()), encoding="utf-8")
        except OSError:
            pass
    _memory[key] = (now, package)
    return package


def _terms(text: str) -> set[str]:
    words = {w for w in re.findall(r"[a-z][a-z\-]+", text.lower().replace("_", "")) if w not in _STOP}
    expanded = set(words)
    for w in words:
        expanded.update(_SYNONYMS.get(w, []))
    # "r controlled" arrives as two words
    if "controlled" in words:
        expanded.add("r-controlled")
    return {w for w in expanded if len(w) >= 3 or w in {"vv"}}


def search_standards(
    package: dict[str, Any],
    description: str,
    grade: str | None = None,
    limit: int = 12,
) -> list[dict[str, Any]]:
    """Rank standards by how many of the description's terms they contain."""
    wanted = _terms(description)
    if not wanted:
        return []
    want_grade = (str(grade).strip().upper() if grade else "") or None
    if want_grade:
        want_grade = {"KINDERGARTEN": "K", "1ST": "1", "2ND": "2", "3RD": "3", "4TH": "4", "5TH": "5"}.get(
            want_grade, want_grade
        )
    reading_foundations = bool(wanted & {"phoneme", "phonemes", "sounds", "decode", "decoding", "vce", "digraphs",
                                         "digraph", "blends", "blend", "vowel", "vowels", "vv", "encode", "spell",
                                         "syllable", "syllables", "fluently", "fluency", "r-controlled"})
    scored: list[tuple[float, dict[str, Any]]] = []
    for item in package["items"]:
        if want_grade and item["grade"] != want_grade:
            continue
        if item["grade"] not in {"K", "1", "2", "3", "4", "5"}:
            continue
        haystack = _terms(item["statement"] + " " + item["code"].lower())
        overlap = len(wanted & haystack)
        if overlap == 0:
            continue
        score = float(overlap)
        if reading_foundations and item["strand"] == "F":
            score += 1.5
        if item["item_type"] in {"Expectation", "Standard"}:
            score += 0.5
        scored.append((score, item))
    scored.sort(key=lambda pair: (-pair[0], pair[1]["code"]))
    return [item for _, item in scored[:limit]]
