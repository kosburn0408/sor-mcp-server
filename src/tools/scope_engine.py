"""Cumulative grapheme scope engine for decodability checking.

A word counts as decodable only if every grapheme in it has been taught by the
chosen grade and unit, and the word does not need a pattern that has not been
taught yet (silent-e, vowel teams, multisyllable decoding, and so on). This
replaces the earlier letter-shape matching, which treated words such as "night",
"knight" and "through" as decodable in first grade.

This is an orthographic heuristic. It does not use a pronunciation lexicon, so it
can accept a word whose spelling follows taught patterns but whose pronunciation
is an exception (teach those as heart words), and it errs toward flagging words
as off-scope. The default sequence below is a common ordering, not a specific
program's scope and sequence; check the results against your own materials.
"""

from __future__ import annotations

import math
import re
from typing import Any

VOWEL_LETTERS = set("aeiou")
CONSONANT_LETTERS = set("bcdfghjklmnpqrstvwxyz")

# ── Default scope and sequence ──────────────────────────────────────────────
# Each grade is an ordered list of groups. Tokens starting with "@" switch on a
# rule instead of adding a grapheme. Unit N of 10 unlocks the first
# ceil(N/10 * number_of_groups) groups of the chosen grade; earlier grades are
# fully taught.

SCOPE_GROUPS: dict[str, list[list[str]]] = {
    "K": [
        ["s", "a", "t", "p", "i", "n"],
        ["m", "d", "g", "o", "c", "k"],
        ["e", "u", "r", "h", "b", "f", "l"],
        ["j", "v", "w", "x", "y", "z"],
    ],
    "1": [
        ["ff", "ll", "ss", "zz", "ck"],
        ["sh", "ch", "th", "wh"],
        ["ng", "nk", "qu"],
        ["@inflect"],
        ["@VCe"],
        ["@open", "@compound"],
    ],
    "2": [
        ["ai", "ay"],
        ["ee", "ea"],
        ["oa", "ow", "oe"],
        ["ar", "or"],
        ["er", "ir", "ur"],
        ["oi", "oy", "ou"],
        ["oo", "au", "aw", "ew", "ue", "ui"],
        ["igh", "ie", "@y_vowel"],
        ["tch", "dge", "@soft_c", "@soft_g", "@doublets"],
        ["kn", "wr", "gn", "mb", "ph"],
        ["@affix", "@contractions", "@multisyl", "@vv_split"],
    ],
    "3": [
        ["ei", "ey", "eu", "eigh"],
        ["tion", "sion", "ture"],
        ["ough", "augh"],
        ["ous", "able", "ible"],
        ["@cle"],
    ],
}

GRADE_ORDER = ["K", "1", "2", "3", "4", "5"]

# Every multi-letter grapheme the engine knows about. A letter sequence found in
# a word that matches one of these must be read as that grapheme, and fails if it
# has not been taught yet (so "kn" in "knight" cannot be read as k + n).
# "gh" is only ever read as part of igh/eigh/ough/augh, so alone it is never taught.
_NEVER_TAUGHT_ATOMIC = {"gh"}
ATOMIC_GRAPHEMES: list[str] = sorted(
    {
        g
        for groups in SCOPE_GROUPS.values()
        for group in groups
        for g in group
        if len(g) > 1 and not g.startswith("@")
    }
    | _NEVER_TAUGHT_ATOMIC,
    key=len,
    reverse=True,
)
R_CONTROLLED = {"ar", "or", "er", "ir", "ur"}
VOWEL_TEAMS = {
    "ai", "ay", "ee", "ea", "oa", "ow", "oe", "oi", "oy", "ou", "oo", "au", "aw",
    "ew", "ue", "ui", "ie", "ei", "ey", "eu", "igh", "eigh", "ough", "augh",
}

HARD_G_EXCEPTIONS = {"get", "give", "girl", "gift", "begin", "forget", "target", "gear"}

# ── Heart words (cumulative by grade) ───────────────────────────────────────
# Words with irregular spelling-sound parts, taught explicitly. Regular words
# such as "on", "can" or "then" are deliberately absent: they are decodable.

HEART_WORDS_BY_GRADE: dict[str, set[str]] = {
    "K": {
        "the", "a", "i", "is", "his", "has", "as", "was", "to", "do", "of", "are",
        "you", "your", "said", "they", "have", "he", "she", "me", "we", "be", "my",
        "by", "no", "so", "go", "what", "one", "see", "like", "look", "for",
    },
    "1": {
        "there", "where", "here", "some", "come", "from", "give", "live", "love",
        "were", "would", "could", "should", "who", "two", "put", "pull", "push",
        "full", "very", "any", "many", "once", "been", "does", "goes", "their",
        "these", "those", "because", "people", "friend", "every", "other", "again",
        "only", "also", "always",
    },
    "2": {
        "through", "thought", "though", "enough", "laugh", "eye", "eyes", "pretty",
        "busy", "heart", "great", "break", "water", "other", "mother", "brother",
        "father", "gone", "done", "move", "prove", "whose", "whole", "word", "work",
        "world", "worm", "worth", "warm", "warn", "want", "watch",
    },
    "3": {
        "together", "answer", "woman", "women", "island", "build", "built", "bought",
        "brought", "caught", "daughter", "special", "different", "important",
        "beautiful", "favorite", "usually", "science", "journey",
    },
}

# Compound words are accepted only when both halves are common short words. Without a
# lexicon, any other split ("thro" + "ugh") would produce false positives.
COMPOUND_PARTS = {
    "sun", "set", "bath", "tub", "cup", "cake", "hot", "dog", "pan", "cap", "mat", "back",
    "pack", "bed", "time", "fish", "net", "hand", "bag", "sand", "box", "play", "pen", "pot",
    "top", "rain", "coat", "day", "light", "book", "ball", "foot", "fire", "gold", "home",
    "house", "jump", "lunch", "milk", "moon", "news", "paper", "pop", "corn", "sail", "snow",
    "star", "tooth", "wash", "ship", "shell", "side", "walk", "up", "in", "on", "out", "land",
    "mad", "man", "hill", "kick", "stick", "lip", "pick", "rock", "wind", "mill", "bug", "bat",
    "dust", "pin", "pit", "sit", "tip", "web", "wag", "yes", "zip",
}

INFLECTIONS = ("es", "ed", "ing", "s")
PREFIXES = ("un", "re", "pre", "mis", "dis", "non", "sub", "inter", "super", "trans", "anti", "semi", "mid")
SUFFIXES = ("less", "ness", "ment", "ful", "est", "ly", "er", "ish", "en")


def normalize_grade(grade: str) -> str | None:
    raw = str(grade).strip().upper()
    table = {
        "K": "K", "KINDERGARTEN": "K",
        "1": "1", "1ST": "1", "GRADE 1": "1", "GRADE1": "1",
        "2": "2", "2ND": "2", "GRADE 2": "2", "GRADE2": "2",
        "3": "3", "3RD": "3", "GRADE 3": "3", "GRADE3": "3",
        "4": "4", "4TH": "4", "GRADE 4": "4", "GRADE4": "4",
        "5": "5", "5TH": "5", "GRADE 5": "5", "GRADE5": "5",
    }
    return table.get(raw)


def parse_unit(unit: str | int | None) -> int | None:
    """Return a unit from 1 to 10, or None for the whole grade."""
    if unit is None or str(unit).strip() == "":
        return None
    digits = "".join(ch for ch in str(unit) if ch.isdigit())
    if not digits:
        return None
    return max(1, min(10, int(digits)))


def taught_scope(grade: str, unit: int | None) -> dict[str, Any]:
    """Compute the graphemes, rules and heart words taught by this grade and unit."""
    graphemes: set[str] = set()
    rules: set[str] = set()
    names: list[str] = []
    hearts: set[str] = set()
    idx = GRADE_ORDER.index(grade)

    for g in GRADE_ORDER[: idx + 1]:
        groups = SCOPE_GROUPS.get(g, [])
        hearts |= HEART_WORDS_BY_GRADE.get(g, set())
        if g == grade and unit is not None and groups:
            n = max(1, math.ceil(unit / 10 * len(groups)))
            groups = groups[:n]
        for group in groups:
            for token in group:
                if token.startswith("@"):
                    rules.add(token[1:])
                else:
                    graphemes.add(token)
            names.append(f"{g}:{'/'.join(group)}")
    return {"graphemes": graphemes, "rules": rules, "heart_words": hearts, "groups": names}


def _segment(word: str, scope: dict[str, Any], allow_multisyl: bool = False) -> tuple[list[str] | None, str]:
    """Split a word into taught graphemes. Returns (graphemes, error)."""
    taught: set[str] = scope["graphemes"]
    rules: set[str] = scope["rules"]
    out: list[str] = []
    i, n = 0, len(word)

    while i < n:
        matched = False
        for g in ATOMIC_GRAPHEMES:
            if word.startswith(g, i):
                if g in taught:
                    out.append(g)
                    i += len(g)
                    matched = True
                else:
                    # Letter pairs that double a consonant are only atomic when taught.
                    return None, f"untaught pattern '{g}'"
                break
        if matched:
            continue

        ch = word[i]
        nxt = word[i + 1] if i + 1 < n else ""

        if ch == "q":
            return None, "'q' without 'u'"
        if ch not in taught:
            return None, f"untaught letter '{ch}'"

        if ch in VOWEL_LETTERS and nxt in VOWEL_LETTERS and "vv_split" not in rules:
            return None, f"adjacent vowels '{ch}{nxt}' need a taught vowel team"

        if ch == "c" and nxt in ("e", "i", "y") and "soft_c" not in rules:
            return None, "soft c is not taught yet"
        if (
            ch == "g"
            and nxt in ("e", "i", "y")
            and "soft_g" not in rules
            and word not in HARD_G_EXCEPTIONS
        ):
            return None, "soft g is not taught yet"
        if ch == "y" and i > 0 and (nxt == "" or nxt not in VOWEL_LETTERS):
            if "y_vowel" not in rules:
                return None, "y as a vowel is not taught yet"

        # Doubled consonant letters spell one sound once doublets are taught.
        if (
            ch in CONSONANT_LETTERS
            and nxt == ch
            and "doublets" in rules
        ):
            out.append(ch * 2)
            i += 2
            continue

        out.append(ch)
        i += 1

    # Silent-e (VCe) and consonant+le endings.
    silent_e_index = None
    if len(out) >= 3 and out[-1] == "e":
        prev, before = out[-2], out[-3]
        is_vce = (
            before in VOWEL_LETTERS
            and (prev in CONSONANT_LETTERS or prev in ("th", "ch", "sh"))
        )
        if is_vce and "VCe" in rules:
            silent_e_index = len(out) - 1
        elif (
            "cle" in rules
            and prev in CONSONANT_LETTERS
            and out[-1] == "e"
            and len(out) >= 3
            and out[-2] == "l"
            and before in CONSONANT_LETTERS
        ):
            silent_e_index = len(out) - 1

    nuclei = 0
    for idx, g in enumerate(out):
        if idx == silent_e_index:
            continue
        if g in VOWEL_LETTERS or g in VOWEL_TEAMS or g in R_CONTROLLED:
            nuclei += 1
        elif g == "y" and idx > 0 and "y_vowel" in rules:
            prev_g = out[idx - 1]
            if prev_g not in VOWEL_LETTERS and prev_g not in VOWEL_TEAMS:
                nuclei += 1
        elif g in ("tion", "sion", "ture", "ous", "able", "ible"):
            nuclei += 1

    if nuclei == 0:
        return None, "no vowel sound"
    if nuclei > 1 and not (allow_multisyl or "multisyl" in rules):
        return None, "multisyllabic decoding is not taught yet"
    # Open syllables: a single consonant-vowel word like "go" or "he" needs the open-syllable pattern.
    if (
        len(out) >= 2
        and out[-1] in VOWEL_LETTERS
        and out[-2] not in VOWEL_LETTERS
        and nuclei == 1
        and silent_e_index is None
        and "open" not in rules
        and out[-1] != "a"
    ):
        return None, "open-syllable (long vowel) pattern is not taught yet"

    return out, ""


def _is_word_decodable(word: str, scope: dict[str, Any], allow_multisyl: bool = False) -> tuple[list[str] | None, str]:
    return _segment(word, scope, allow_multisyl=allow_multisyl)


def _stem_candidates(word: str) -> list[tuple[str, str]]:
    """Candidate (stem, inflection) splits for -es, -ed, -ing and -s."""
    cands: list[tuple[str, str]] = []
    for infl in INFLECTIONS:
        if len(word) > len(infl) + 1 and word.endswith(infl):
            stem = word[: -len(infl)]
            cands.append((stem, infl))
            if infl in ("ed", "ing") and len(stem) >= 2 and stem[-1] == stem[-2]:
                cands.append((stem[:-1], infl))          # hopping -> hop
            if infl in ("ed", "ing"):
                cands.append((stem + "e", infl))         # hiking -> hike
    return cands


def analyze_word(word: str, scope: dict[str, Any]) -> dict[str, Any]:
    """Classify one word as decodable, heart_word, or off_scope."""
    rules: set[str] = scope["rules"]
    hearts: set[str] = scope["heart_words"]
    base: dict[str, Any] = {"word": word}

    if word in hearts:
        return {**base, "status": "heart_word", "reason": "taught heart word"}

    if len(word) == 1:
        return {**base, "status": "decodable", "graphemes": [word], "reason": "single letter"}

    # Apostrophes: possessive 's always follows the stem; other contractions need @contractions.
    if "'" in word:
        stem, _, tail = word.partition("'")
        if tail == "s" and stem:
            sub = analyze_word(stem, scope)
            if sub["status"] != "off_scope" and "inflect" in rules:
                return {**base, "status": sub["status"], "graphemes": sub.get("graphemes", []) + ["'s"],
                        "reason": "possessive or contraction with 's"}
        elif "contractions" in rules and tail in ("ll", "m", "re", "ve", "d", "t"):
            stem = stem[:-1] if tail == "t" and stem.endswith("n") else stem
            sub = analyze_word(stem, scope) if stem else {"status": "off_scope"}
            if sub["status"] != "off_scope":
                return {**base, "status": sub["status"], "reason": "contraction"}
        return {**base, "status": "off_scope", "reason": "contraction not taught yet"}

    graphemes, err = _is_word_decodable(word, scope)
    if graphemes is not None:
        return {**base, "status": "decodable", "graphemes": graphemes, "reason": "all graphemes taught"}

    # Inflections: -es, -ed, -ing (plural -s needs no rule because s is a letter).
    if "inflect" in rules:
        for stem, infl in _stem_candidates(word):
            if stem in hearts:
                return {**base, "status": "decodable", "reason": f"heart word + -{infl}"}
            g, _ = _is_word_decodable(stem, scope)
            if g is not None:
                return {**base, "status": "decodable", "graphemes": g + [infl],
                        "reason": f"decodable stem '{stem}' + -{infl}"}

    # Prefixes and suffixes.
    if "affix" in rules:
        for pre in PREFIXES:
            if word.startswith(pre) and len(word) - len(pre) >= 3:
                rest = word[len(pre):]
                if rest in hearts:
                    return {**base, "status": "decodable", "reason": f"prefix {pre}- + heart word"}
                g, _ = _is_word_decodable(rest, scope)
                if g is not None:
                    return {**base, "status": "decodable", "graphemes": [pre] + g,
                            "reason": f"prefix {pre}- + decodable base"}
        for suf in SUFFIXES:
            if word.endswith(suf) and len(word) - len(suf) >= 3:
                rest = word[: -len(suf)]
                g, _ = _is_word_decodable(rest, scope)
                if g is not None:
                    return {**base, "status": "decodable", "graphemes": g + [suf],
                            "reason": f"decodable base + -{suf}"}

    # Compound words made of two decodable one-syllable words.
    if "compound" in rules and len(word) >= 5:
        for cut in range(2, len(word) - 1):
            left, right = word[:cut], word[cut:]
            if left not in COMPOUND_PARTS or right not in COMPOUND_PARTS:
                continue
            gl, _ = _is_word_decodable(left, scope)
            gr, _ = _is_word_decodable(right, scope)
            if gl is not None and gr is not None:
                return {**base, "status": "decodable", "graphemes": gl + ["|"] + gr,
                        "reason": f"compound '{left}' + '{right}'"}

    return {**base, "status": "off_scope", "reason": err}


def scope_for(grade: str, unit: int | None) -> dict[str, Any]:
    return taught_scope(grade, unit)


def all_heart_words() -> set[str]:
    return set().union(*HEART_WORDS_BY_GRADE.values())


def tokenize(text: str) -> list[str]:
    return re.findall(r"[a-zA-Z]+(?:'[a-zA-Z]+)?", text.lower())
