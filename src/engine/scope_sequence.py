"""Phonics scope & sequence: which GPCs and heart words are taught by when.

The DEFAULT sequence below is an illustrative progression modelled on the
general order common to structured-literacy programs (single consonants and
short vowels → digraphs → silent-e → r-controlled and vowel teams →
multisyllabic patterns). It is NOT the sequence of any specific published
program, and units differ between programs.

Decodability is only meaningful against what a given class has actually been
taught, so districts should supply their adopted program's sequence:

- set ``SOR_SCOPE_PATH`` to a JSON file with the same shape as
  ``DEFAULT_SEQUENCE`` (see ``load_sequence``), or
- pass ``taught_gpcs`` / ``taught_heart_words`` directly to the tools.

Scope is cumulative: grade 1 unit 3 includes all of kindergarten, plus
grade 1 units 1–3.
"""

from __future__ import annotations

import json
import os
from functools import lru_cache
from pathlib import Path
from typing import Any

from src.engine.gpc import ALL_GPC_IDS, gpc_label

GRADE_ORDER = ["K", "1", "2", "3"]

GRADE_ALIASES = {
    "K": "K", "KINDERGARTEN": "K", "0": "K",
    "1": "1", "1ST": "1", "GRADE 1": "1", "GRADE1": "1", "FIRST": "1",
    "2": "2", "2ND": "2", "GRADE 2": "2", "GRADE2": "2", "SECOND": "2",
    "3": "3", "3RD": "3", "GRADE 3": "3", "GRADE3": "3", "THIRD": "3",
}

# Each unit: title, new GPC ids, new heart words (words with a part students
# must learn "by heart" until the pattern is taught).
DEFAULT_SEQUENCE: dict[str, list[dict[str, Any]]] = {
    "K": [
        {"title": "m, s, t, p, short a", "gpcs": ["m", "s", "t", "p", "short_a"], "heart_words": ["the", "a", "I"]},
        {"title": "n, c, d, short i", "gpcs": ["n", "c", "d", "short_i"], "heart_words": ["to", "is"]},
        {"title": "f, h, g, b, short o", "gpcs": ["f", "h", "g", "b", "short_o"], "heart_words": ["of", "said"]},
        {"title": "l, r, k, short e, s as /z/", "gpcs": ["l", "r", "k", "short_e", "s_z"], "heart_words": ["was", "you"]},
        {"title": "short u, j, w, v, y", "gpcs": ["short_u", "j", "w", "v", "y"], "heart_words": ["he", "we", "me", "be", "she", "do"]},
        {"title": "x, qu, z", "gpcs": ["x", "qu", "z"], "heart_words": ["are", "for", "go", "no", "so"]},
        {"title": "FLOSS rule, ck", "gpcs": ["floss", "ck"], "heart_words": ["they", "what", "my", "by"]},
        {"title": "sh, th", "gpcs": ["sh", "th"], "heart_words": ["one", "two", "come", "some"]},
        {"title": "ch, wh", "gpcs": ["ch", "wh"], "heart_words": ["from", "put", "want"]},
        {"title": "welded sounds: ng, nk", "gpcs": ["ng", "nk"], "heart_words": ["here", "there", "where", "were", "have", "give", "live"]},
    ],
    "1": [
        {"title": "tch, consonant blends review", "gpcs": ["tch"], "heart_words": ["does", "done", "again"]},
        {"title": "silent-e: a_e, i_e", "gpcs": ["vce_a", "vce_i"], "heart_words": ["who", "whose"]},
        {"title": "silent-e: o_e, u_e, e_e", "gpcs": ["vce_o", "vce_u", "vce_e"], "heart_words": ["could", "would", "should"]},
        {"title": "soft c, soft g, dge", "gpcs": ["soft_c", "soft_g", "dge"], "heart_words": ["many", "any"]},
        {"title": "open syllables, y as a vowel", "gpcs": ["open_syllable", "y_vowel"], "heart_words": ["once", "only"]},
        {"title": "inflectional endings -ed, -es", "gpcs": ["suffix_ed", "suffix_es"], "heart_words": ["their", "friend"]},
        {"title": "r-controlled: ar, or, ore", "gpcs": ["r_ar", "r_or"], "heart_words": ["because", "laugh"]},
        {"title": "r-controlled: er, ir, ur", "gpcs": ["r_er"], "heart_words": ["eye", "buy"]},
        {"title": "vowel teams: ai/ay, ee/ea, oa/ow/oe", "gpcs": ["vt_ai", "vt_ee", "vt_oa"], "heart_words": ["people", "pretty"]},
        {"title": "two-syllable words: doubled consonants, schwa", "gpcs": ["double_consonant", "schwa"], "heart_words": ["water", "busy"]},
    ],
    "2": [
        {"title": "igh, ie", "gpcs": ["vt_igh"], "heart_words": ["though", "through"]},
        {"title": "oo, ew, ue", "gpcs": ["vt_oo", "vt_ew"], "heart_words": ["enough", "touch"]},
        {"title": "ou/ow, oi/oy", "gpcs": ["diph_ou", "diph_oi"], "heart_words": ["ocean", "young"]},
        {"title": "au/aw, all", "gpcs": ["vt_au"], "heart_words": ["machine", "piece"]},
        {"title": "consonant-le", "gpcs": ["c_le"], "heart_words": ["early", "learn"]},
        {"title": "silent letters: kn, wr, gn, mb", "gpcs": ["silent_kn", "silent_wr", "silent_gn", "silent_mb"], "heart_words": ["island", "answer"]},
        {"title": "ph, short ea", "gpcs": ["ph", "ea_short"], "heart_words": ["great", "break"]},
        {"title": "final ve and se; ou as /oo/; ie as /ē/", "gpcs": ["final_ve", "final_se", "ou_oo", "ie_ee"], "heart_words": ["sure", "sugar"]},
    ],
    "3": [
        {"title": "-tion, -sion", "gpcs": ["suffix_tion"], "heart_words": ["special", "ancient"]},
        {"title": "-ture", "gpcs": ["suffix_ture"], "heart_words": ["certain", "mountain"]},
    ],
}

# Explanations of the irregular ("heart") part of common heart words.
HEART_WORD_NOTES: dict[str, str] = {
    "the": "e says /ŭ/ (schwa)",
    "a": "a says /ŭ/ (schwa)",
    "i": "i says /ī/ — decodable once open syllables are taught",
    "to": "o says /oo/",
    "do": "o says /oo/",
    "is": "s says /z/ — decodable once s→/z/ is taught",
    "of": "o says /ŭ/; f says /v/",
    "said": "ai says /ĕ/",
    "was": "a says /ŭ/ (or /ŏ/); s says /z/",
    "you": "ou says /oo/",
    "he": "e says /ē/ — decodable once open syllables are taught",
    "we": "e says /ē/ — decodable once open syllables are taught",
    "me": "e says /ē/ — decodable once open syllables are taught",
    "be": "e says /ē/ — decodable once open syllables are taught",
    "she": "e says /ē/ — decodable once open syllables are taught",
    "go": "o says /ō/ — decodable once open syllables are taught",
    "no": "o says /ō/ — decodable once open syllables are taught",
    "so": "o says /ō/ — decodable once open syllables are taught",
    "are": "are says /ar/",
    "for": "or says /or/ — decodable once r-controlled or is taught",
    "they": "ey says /ā/",
    "what": "a says /ŭ/",
    "my": "y says /ī/ — decodable once y as a vowel is taught",
    "by": "y says /ī/ — decodable once y as a vowel is taught",
    "one": "o says /w/ + /ŭ/; e is silent",
    "two": "w is silent; o says /oo/",
    "come": "o says /ŭ/; the e does not make o long",
    "some": "o says /ŭ/; the e does not make o long",
    "from": "o says /ŭ/",
    "put": "u says /oo/ as in book",
    "want": "a says /ŏ/",
    "here": "ere says /ēr/",
    "there": "ere says /air/",
    "where": "ere says /air/",
    "were": "ere says /er/",
    "have": "the vowel stays short; final e is there because English words don't end in v",
    "give": "the vowel stays short; final e is there because English words don't end in v",
    "live": "the vowel stays short; final e is there because English words don't end in v",
    "does": "oe says /ŭ/; s says /z/",
    "done": "o says /ŭ/",
    "again": "ai says /ĕ/; first a is schwa",
    "who": "w is silent; o says /oo/",
    "whose": "w is silent; o says /oo/; s says /z/",
    "could": "oul says /oo/; l is silent",
    "would": "oul says /oo/; l is silent",
    "should": "oul says /oo/; l is silent",
    "many": "a says /ĕ/",
    "any": "a says /ĕ/",
    "once": "o says /wŭ/",
    "only": "o says /ō/ in a closed syllable",
    "their": "eir says /air/",
    "friend": "ie says /ĕ/",
    "because": "au says /ŭ/ (or /ô/); se says /z/",
    "laugh": "augh says /ăf/",
    "eye": "eye says /ī/",
    "buy": "uy says /ī/",
    "people": "eo says /ē/",
    "pretty": "e says /ĭ/",
    "water": "a says /ô/",
    "busy": "u says /ĭ/; s says /z/",
}


def normalize_grade(grade: str | int | None) -> str | None:
    if grade is None:
        return None
    return GRADE_ALIASES.get(str(grade).strip().upper())


@lru_cache(maxsize=4)
def load_sequence(path: str | None = None) -> dict[str, list[dict[str, Any]]]:
    """Load a custom scope & sequence from JSON, or return the default.

    JSON shape: {"K": [{"title": str, "gpcs": [ids], "heart_words": [words]}, ...], "1": [...], ...}
    """
    path = path or os.environ.get("SOR_SCOPE_PATH")
    if not path:
        return DEFAULT_SEQUENCE
    data = json.loads(Path(path).read_text())
    unknown = {g for units in data.values() for u in units for g in u.get("gpcs", [])} - ALL_GPC_IDS
    if unknown:
        raise ValueError(f"Unknown GPC ids in scope file {path}: {sorted(unknown)}")
    return data


def resolve_scope(grade: str | int, unit: str | int = 1, sequence: dict[str, list[dict[str, Any]]] | None = None) -> dict[str, Any]:
    """Return the cumulative taught GPCs and heart words through grade/unit."""
    g = normalize_grade(grade)
    if g is None:
        raise ValueError(f"Unsupported grade '{grade}'. Use K, 1, 2 or 3.")
    seq = sequence or load_sequence()
    try:
        u = max(1, int(str(unit).strip()))
    except ValueError:
        u = 1

    taught: list[str] = []
    hearts: list[str] = []
    current: dict[str, Any] = {}
    for grade_key in GRADE_ORDER:
        units = seq.get(grade_key, [])
        limit = min(u, len(units)) if grade_key == g else len(units)
        for unit_data in units[:limit]:
            taught.extend(unit_data.get("gpcs", []))
            hearts.extend(w.lower() for w in unit_data.get("heart_words", []))
        if grade_key == g:
            if units:
                current = units[min(u, len(units)) - 1]
            break

    unit_used = min(u, len(seq.get(g, []))) or 1
    return {
        "grade_level": g,
        "unit": unit_used,
        "unit_requested": u,
        "unit_title": current.get("title", ""),
        "new_gpcs": current.get("gpcs", []),
        "new_heart_words": current.get("heart_words", []),
        "taught_gpcs": list(dict.fromkeys(taught)),
        "heart_words": list(dict.fromkeys(hearts)),
        "source": "custom" if os.environ.get("SOR_SCOPE_PATH") else "default_illustrative_sequence",
    }


def describe_scope(scope: dict[str, Any]) -> dict[str, Any]:
    """Teacher-facing description of a resolved scope."""
    return {
        **scope,
        "new_patterns": [gpc_label(g) for g in scope["new_gpcs"]],
        "taught_patterns": [gpc_label(g) for g in scope["taught_gpcs"]],
        "heart_word_notes": {w: HEART_WORD_NOTES.get(w, "") for w in scope["heart_words"]},
    }
