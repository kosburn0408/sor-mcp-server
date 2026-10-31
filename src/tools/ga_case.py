"""Live Georgia K-12 ELA standards from Georgia's CASE repository (SuitCASE).

Georgia's K-12 English Language Arts standards (in effect from the 2025-26
school year) are published in 1EdTech CASE format. This module downloads the
ELA framework package once, caches it on disk, and searches the K-3
Foundations domain (phonological awareness, concepts of print, phonics,
fluency) for standards matching a skill description.

Codes follow the pattern ``<grade>.F.<strand>.<n>`` (e.g. ``K.F.P.2``), where
strand is PA (phonological awareness), CP (concepts of print), P (phonics),
F (fluency) or H (handwriting).

Configuration (environment variables):

- ``SOR_GA_CASE_BASE_URL``     default ``https://case.georgiastandards.org/ims/case/v1p1``
- ``SOR_GA_ELA_FRAMEWORK_ID``  default ``391c3abe-c1ec-4a4a-a942-c9e152b35102``
                               ("English Language Arts - Georgia Department of Education", Adopted)
- ``SOR_GA_CASE_CACHE``        cache file path (default ``db/ga_ela_case_package.json``)
- ``SOR_GA_CASE_TTL_DAYS``     cache lifetime in days (default 7)
- ``SOR_GA_CASE_OFFLINE``      set to 1 to never download (use cache only; used in tests)

If the repository is unreachable (for example, outside a network it allows),
the cached copy is used; if there is no cache, callers fall back to the
bundled legacy codes and say so.
"""

from __future__ import annotations

import json
import os
import re
import time
from pathlib import Path
from typing import Any

DEFAULT_BASE_URL = "https://case.georgiastandards.org/ims/case/v1p1"
DEFAULT_FRAMEWORK_ID = "391c3abe-c1ec-4a4a-a942-c9e152b35102"
DEFAULT_CACHE = Path(__file__).resolve().parents[2] / "db" / "ga_ela_case_package.json"

STRANDS = {
    "PA": "Phonological Awareness",
    "CP": "Concepts of Print",
    "P": "Phonics",
    "F": "Fluency",
    "H": "Handwriting",
}

# Skill-description keywords → Foundations strand.
STRAND_KEYWORDS: list[tuple[str, tuple[str, ...]]] = [
    ("PA", ("phonemic", "phonological", "phoneme", "segment", "rhym", "syllable", "onset", "rime", "sounds in spoken")),
    ("CP", ("print", "book handling", "left to right", "letter recognition", "alphabet")),
    ("F", ("fluency", "fluent", "prosody", "accuracy", "rate", "expression", "automaticity")),
    ("H", ("handwriting", "letter formation", "write letters")),
    ("P", ("phonics", "decod", "encod", "spell", "grapheme", "silent e", "silent-e", "vowel", "digraph",
           "blend", "cvc", "syllable type", "suffix", "prefix", "heart word", "high-frequency", "irregular")),
]

CODE_RE = re.compile(r"^(K|[1-3])\.F\.(PA|CP|P|F|H)(\.\d+)*$")
GRADE_PREFIX = {"K": "K", "KINDERGARTEN": "K", "0": "K", "1": "1", "1ST": "1", "2": "2", "2ND": "2", "3": "3", "3RD": "3"}


def _settings() -> tuple[str, str, Path, float]:
    base = os.environ.get("SOR_GA_CASE_BASE_URL", DEFAULT_BASE_URL).rstrip("/")
    fw = os.environ.get("SOR_GA_ELA_FRAMEWORK_ID", DEFAULT_FRAMEWORK_ID)
    cache = Path(os.environ.get("SOR_GA_CASE_CACHE", str(DEFAULT_CACHE)))
    ttl_days = float(os.environ.get("SOR_GA_CASE_TTL_DAYS", "7"))
    return base, fw, cache, ttl_days * 86400


def _download(base: str, framework_id: str, timeout: float = 30.0) -> dict[str, Any]:
    import httpx

    resp = httpx.get(f"{base}/CFPackages/{framework_id}", timeout=timeout, follow_redirects=True)
    resp.raise_for_status()
    data = resp.json()
    if "CFItems" not in data:
        raise ValueError("CASE response has no CFItems")
    return data


def load_package(force_refresh: bool = False) -> tuple[dict[str, Any] | None, str]:
    """Return (package, source) where source is 'live', 'cache', 'stale_cache' or 'unavailable'."""
    base, fw, cache, ttl = _settings()
    fresh_cache = cache.exists() and (time.time() - cache.stat().st_mtime) < ttl
    if fresh_cache and not force_refresh:
        try:
            return json.loads(cache.read_text()), "cache"
        except (OSError, ValueError):
            pass
    try:
        if os.environ.get("SOR_GA_CASE_OFFLINE") == "1":
            raise RuntimeError("offline mode")
        pkg = _download(base, fw)
        try:
            cache.parent.mkdir(parents=True, exist_ok=True)
            cache.write_text(json.dumps(pkg))
        except OSError:
            pass
        return pkg, "live"
    except Exception:
        if cache.exists():
            try:
                return json.loads(cache.read_text()), "stale_cache"
            except (OSError, ValueError):
                pass
    return None, "unavailable"


def _clean(statement: str) -> tuple[str, str]:
    """Split a fullStatement like '**Decoding words** Students ...' into (title, text)."""
    s = (statement or "").strip()
    m = re.match(r"^\*\*(.+?)\*\*\s*(.*)$", s, re.S)
    if m:
        return m.group(1).strip(), m.group(2).strip()
    return "", s


def foundations_items(pkg: dict[str, Any]) -> list[dict[str, Any]]:
    out = []
    for item in pkg.get("CFItems", []):
        code = (item.get("humanCodingScheme") or "").strip()
        if not CODE_RE.match(code):
            continue
        grade, _, strand = code.split(".")[:3]
        title, text = _clean(item.get("fullStatement", ""))
        out.append({
            "code": code,
            "grade": grade,
            "strand": strand,
            "strand_name": STRANDS.get(strand, strand),
            "item_type": item.get("CFItemType", ""),
            "title": title,
            "statement": text or title,
            "identifier": item.get("identifier", ""),
            "case_uri": item.get("uri", ""),
            "depth": code.count("."),
        })
    return out


def _strands_for(description: str) -> list[str]:
    d = description.lower()
    hits = [s for s, words in STRAND_KEYWORDS if any(w in d for w in words)]
    return hits or ["P"]


def _score(item: dict[str, Any], words: set[str]) -> int:
    text = f"{item['title']} {item['statement']}".lower()
    return sum(1 for w in words if w in text)


def search_ga_foundations(description: str, grade: str | None = None, limit: int = 8) -> dict[str, Any] | None:
    """Search current Georgia K-3 Foundations standards. Returns None if unavailable."""
    pkg, source = load_package()
    if pkg is None:
        return None
    items = foundations_items(pkg)
    if not items:
        return None

    strands = _strands_for(description)
    g = GRADE_PREFIX.get(str(grade).strip().upper()) if grade else None
    words = {w for w in re.findall(r"[a-z]{4,}", description.lower())}

    pool = [i for i in items if i["strand"] in strands and (g is None or i["grade"] == g)]
    # Standards (depth 3) before their sub-skills; rank by keyword overlap.
    pool.sort(key=lambda i: (-_score(i, words), i["depth"] != 3, i["grade"], i["code"]))
    doc = pkg.get("CFDocument", {})
    return {
        "source": source,
        "framework": {
            "title": doc.get("title", "English Language Arts - Georgia Department of Education"),
            "identifier": doc.get("identifier", _settings()[1]),
            "adoption_status": doc.get("adoptionStatus", ""),
            "last_change": doc.get("lastChangeDateTime", ""),
        },
        "strands_searched": [STRANDS[s] for s in strands],
        "matches": pool[:limit],
    }
