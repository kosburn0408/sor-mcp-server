"""Decodability analysis by grapheme-phoneme alignment.

For each word, look up its pronunciation in the CMU Pronouncing Dictionary
and search for a way to spell that pronunciation using the GPC catalog. Each
GPC used costs 0 if taught and 1 if not, so the cheapest alignment says
whether the word is decodable now and, if not, which patterns are missing.

Word statuses:

- ``decodable``           every grapheme maps to its sound with a taught GPC
- ``heart_word``          not fully decodable, but taught as a heart word
- ``not_yet_decodable``   decodable with patterns not yet taught (listed)
- ``irregular``           cannot be spelled with any catalogued GPC and has not
                          been taught as a heart word; pre-teach or replace it
- ``not_in_dictionary``   no pronunciation available (names, rare words);
                          a teacher needs to review it
"""

from __future__ import annotations

import re
from functools import lru_cache
from typing import Any, Iterable

from src.engine.gpc import (
    CATALOG,
    LONG_VOWELS,
    VOWEL_LETTERS,
    gpc_label,
    gpcs_by_first_letter,
)

WORD_RE = re.compile(r"[A-Za-z]+(?:'[A-Za-z]+)?")

CONSONANT_LETTERS = set("bcdfghjklmnpqrstvwxyz")
_FIRST_LETTER_INDEX = gpcs_by_first_letter()

# Teacher-friendly phoneme display.
DISPLAY = {
    "AE": "ă", "EH": "ĕ", "IH": "ĭ", "AA": "ŏ", "AO": "ô", "AH": "ŭ", "AX": "ə",
    "EY": "ā", "IY": "ē", "AY": "ī", "OW": "ō", "UW": "oo", "UH": "o͝o",
    "AW": "ow", "OY": "oi", "ER": "er", "SH": "sh", "CH": "ch", "TH": "th",
    "DH": "th", "NG": "ng", "JH": "j", "ZH": "zh", "HH": "h", "Y": "y",
}


def _display(phonemes: Iterable[str]) -> str:
    return "".join(DISPLAY.get(p, p.lower()) for p in phonemes)


@lru_cache(maxsize=1)
def _cmu() -> dict[str, list[list[str]]]:
    import cmudict  # bundled CMU Pronouncing Dictionary (BSD-licensed)

    return cmudict.dict()


def normalize_pron(pron: list[str]) -> tuple[str, ...]:
    out = []
    for p in pron:
        if p == "AH0":
            out.append("AX")
        elif p.startswith("ER"):
            out.append("ER")
        else:
            out.append(re.sub(r"\d", "", p))
    return tuple(out)


# Words whose alternate dictionary entries are citation forms ("thee", "ay")
# that would make an irregular everyday pronunciation look decodable.
PRIMARY_ONLY = {"the", "a"}


def pronunciations(word: str) -> list[tuple[str, ...]]:
    """All dictionary pronunciations (dialect and reduced forms vary).

    A word counts as decodable if any listed pronunciation can be spelled with
    taught patterns. For PRIMARY_ONLY words only the first entry is used.
    """
    w = word.lower()
    prons = _cmu().get(w, [])
    if w in PRIMARY_ONLY:
        prons = prons[:1]
    return list(dict.fromkeys(normalize_pron(p) for p in prons))


# ── Alignment ───────────────────────────────────────────────────────────────

Step = tuple[str, tuple[str, ...], str]  # (grapheme, phonemes, gpc_id)


VOWEL_PHONEMES = {"AE", "EH", "IH", "AA", "AO", "AH", "AX", "EY", "IY", "AY", "OW", "UW", "UH", "AW", "OY", "ER"}


def _candidates(spelling: str, i: int, multisyllabic: bool = True) -> list[tuple[int, tuple[tuple[str, ...], ...], tuple[str, ...]]]:
    """Possible moves from letter i: (letters consumed, phoneme options, gpc ids).

    Returns tuples of (length, phoneme_options, gpc_ids_required).
    """
    n = len(spelling)
    ch = spelling[i]
    moves: list[tuple[int, tuple[tuple[str, ...], ...], tuple[str, ...]]] = []

    # Plain catalog GPCs.
    for g in _FIRST_LETTER_INDEX.get(ch, []):
        L = len(g.grapheme)
        if spelling[i:i + L] != g.grapheme:
            continue
        if g.position == "final" and i + L != n:
            continue
        if g.position == "initial" and i != 0:
            continue
        if g.before and (i + L >= n or spelling[i + L] not in g.before):
            continue
        moves.append((L, g.phonemes, (g.id,)))

    if ch in VOWEL_LETTERS:
        rest_after = lambda k: spelling[k:]  # noqa: E731

        # Silent-e (VCe): vowel + single consonant (not r, w, x, y) + e, at the
        # end of the word or before -s / -d.
        if (
            i + 2 < n
            and spelling[i + 2] == "e"
            and spelling[i + 1] in CONSONANT_LETTERS - set("rwxy")
            and rest_after(i + 3) in ("", "s", "d")
        ):
            cons = spelling[i + 1]
            for g in _FIRST_LETTER_INDEX.get(cons, []):
                if g.grapheme != cons or g.position == "initial":
                    continue
                if g.before and "e" not in g.before:
                    continue
                for long_p in LONG_VOWELS[ch]:
                    for cons_p in g.phonemes:
                        moves.append((3, (long_p + cons_p,), (f"vce_{ch}", g.id)))

        # Open syllable: vowel ends the word, or vowel + one consonant + vowel (VCV).
        if i == n - 1 or (
            i + 2 < n
            and spelling[i + 1] in CONSONANT_LETTERS
            and spelling[i + 2] in VOWEL_LETTERS | {"y"}
            and not (i + 3 == n and spelling[i + 2] == "e")
        ):
            moves.append((1, LONG_VOWELS[ch], ("open_syllable",)))

        # Schwa in an unstressed syllable (multisyllabic words only; one-syllable
        # schwa words such as "the", "a", "was" stay heart words).
        if multisyllabic:
            moves.append((1, (("AX",),), ("schwa",)))

    # Final -d after a silent-e consumed by VCe (baked, smiled).
    if ch == "d" and i == n - 1 and i > 0 and spelling[i - 1] == "e":
        moves.append((1, (("T",), ("D",)), ("suffix_ed",)))

    return moves


def _align(spelling: str, pron: tuple[str, ...], taught: frozenset[str]) -> tuple[float, list[Step]]:
    n, m = len(spelling), len(pron)
    multisyllabic = sum(1 for p in pron if p in VOWEL_PHONEMES) >= 2
    INF = float("inf")

    @lru_cache(maxsize=None)
    def best(i: int, j: int) -> tuple[float, tuple[Step, ...]]:
        if i == n:
            return (0.0, ()) if j == m else (INF, ())
        result: tuple[float, tuple[Step, ...]] = (INF, ())
        for length, options, ids in _candidates(spelling, i, multisyllabic):
            step_cost = sum(0 if gid in taught else 1 for gid in ids)
            for ph in options:
                k = len(ph)
                if pron[j:j + k] != ph:
                    continue
                sub_cost, sub_path = best(i + length, j + k)
                total = step_cost + sub_cost
                # Prefer lower cost; on ties prefer longer graphemes (sh over s+h).
                if total < result[0]:
                    step = (spelling[i:i + length], ph, "+".join(ids))
                    result = (total, (step,) + sub_path)
        return result

    cost, path = best(0, 0)
    return cost, list(path)


def analyze_word(word: str, taught_gpcs: Iterable[str], heart_words: Iterable[str] = ()) -> dict[str, Any]:
    taught = frozenset(taught_gpcs)
    hearts = {w.lower() for w in heart_words}
    lower = word.lower()
    spelling = lower.replace("'", "")

    best_cost = float("inf")
    best_path: list[Step] = []
    for pron in pronunciations(lower):
        cost, path = _align(spelling, pron, taught)
        if cost < best_cost:
            best_cost, best_path = cost, path
            if cost == 0:
                break

    display_steps: list[tuple[str, tuple[str, ...], list[str]]] = []
    for g, ph, gid in best_path:
        ids = gid.split("+")
        if ids[0].startswith("vce_"):
            vowel, cons = g[0], g[1]
            long_len = 2 if ph[:2] == ("Y", "UW") else 1
            display_steps.append((f"{vowel}_e", ph[:long_len], [ids[0]]))
            display_steps.append((cons, ph[long_len:], ids[1:]))
        else:
            display_steps.append((g, ph, ids))

    mapping = [
        {
            "grapheme": g,
            "sound": "/" + _display(ph) + "/" if ph else "(silent)",
            "pattern": " + ".join(gpc_label(x) for x in ids),
            "taught": all(x in taught for x in ids),
        }
        for g, ph, ids in display_steps
    ]
    breakdown = ""
    if display_steps:
        breakdown = " - ".join(g for g, _, _ in display_steps) + " → " + " ".join(
            "/" + _display(ph) + "/" for _, ph, _ in display_steps
        )

    missing: list[str] = []
    for _, _, gid in best_path:
        for x in gid.split("+"):
            if x not in taught and x not in missing:
                missing.append(x)

    if not pronunciations(lower):
        status = "heart_word" if lower in hearts else "not_in_dictionary"
    elif best_cost == 0:
        status = "decodable"
    elif lower in hearts:
        status = "heart_word"
    elif best_path:
        status = "not_yet_decodable"
    else:
        status = "irregular"

    return {
        "word": word,
        "status": status,
        "breakdown": breakdown,
        "mapping": mapping,
        "missing_patterns": [gpc_label(x) for x in missing] if status == "not_yet_decodable" else [],
        "missing_gpc_ids": missing if status == "not_yet_decodable" else [],
    }


def analyze_text(
    text: str,
    taught_gpcs: Iterable[str],
    heart_words: Iterable[str] = (),
    target_pct: float = 90.0,
    min_decodable_pct: float | None = None,
) -> dict[str, Any]:
    taught = list(taught_gpcs)
    hearts = [w.lower() for w in heart_words]
    tokens = WORD_RE.findall(text)
    cache: dict[str, dict[str, Any]] = {}
    words: list[dict[str, Any]] = []
    for t in tokens:
        key = t.lower()
        if key not in cache:
            cache[key] = analyze_word(t, taught, hearts)
        words.append(cache[key])

    total = len(words)
    counts = {s: 0 for s in ("decodable", "heart_word", "not_yet_decodable", "irregular", "not_in_dictionary")}
    for w in words:
        counts[w["status"]] += 1

    missing: dict[str, list[str]] = {}
    for info in cache.values():
        for label in info["missing_patterns"]:
            missing.setdefault(label, []).append(info["word"].lower())

    decodable_pct = round(100.0 * counts["decodable"] / total, 1) if total else 0.0
    accessible_pct = round(100.0 * (counts["decodable"] + counts["heart_word"]) / total, 1) if total else 0.0

    def unique(status: str) -> list[str]:
        return sorted({w["word"].lower() for w in words if w["status"] == status})

    return {
        "total_words": total,
        "counts": counts,
        "decodable_pct": decodable_pct,
        "accessible_pct": accessible_pct,
        "target_pct": target_pct,
        "min_decodable_pct": min_decodable_pct,
        "meets_target": accessible_pct >= target_pct
        and (min_decodable_pct is None or decodable_pct >= min_decodable_pct),
        "heart_words": unique("heart_word"),
        "not_yet_decodable_words": unique("not_yet_decodable"),
        "irregular_words": unique("irregular"),
        "not_in_dictionary_words": unique("not_in_dictionary"),
        "missing_patterns": {k: sorted(set(v)) for k, v in missing.items()},
        "words": [cache[k] for k in dict.fromkeys(t.lower() for t in tokens)],
    }


def catalog_ids() -> list[str]:
    return sorted({g.id for g in CATALOG})
