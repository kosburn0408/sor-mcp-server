"""Grapheme-phoneme correspondence (GPC) catalog.

Each entry says: this spelling (grapheme) can represent this sound (phoneme
sequence). Phonemes use ARPAbet, as in the CMU Pronouncing Dictionary, with
these normalizations (see ``decoder.normalize_pron``):

- Stress digits are removed, except an unstressed ``AH0`` becomes ``AX``
  (schwa), so a schwa can only be decoded once schwa has been taught.
- ``ER0`` / ``ER1`` / ``ER2`` become ``ER``.

Positional rules (word-final only, VCe, open syllables, soft c/g) are
enforced in ``decoder.py``; the ``position`` field documents them.

An entry is "taught" when its ``id`` appears in the active scope & sequence.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class GPC:
    id: str
    grapheme: str
    phonemes: tuple[tuple[str, ...], ...]
    label: str
    example: str
    # "any" | "final" (must end the word) | "initial" (must start the word)
    position: str = "any"
    # Optional letters that must follow the grapheme (soft c/g before e, i, y).
    before: tuple[str, ...] = field(default_factory=tuple)


def _p(*seqs: str) -> tuple[tuple[str, ...], ...]:
    return tuple(tuple(s.split()) for s in seqs)


SHORT_VOWELS = {"a": "AE", "e": "EH", "i": "IH", "o": "AA", "u": "AH"}
LONG_VOWELS = {
    "a": _p("EY"),
    "e": _p("IY"),
    "i": _p("AY"),
    "o": _p("OW"),
    "u": _p("UW", "Y UW"),
}
VOWEL_LETTERS = set("aeiou")

# Ordinary, position-free correspondences.
_CATALOG: list[GPC] = [
    # ── Single consonants ────────────────────────────────────────────────
    GPC("m", "m", _p("M"), "m → /m/", "map"),
    GPC("s", "s", _p("S"), "s → /s/", "sat"),
    GPC("s_z", "s", _p("Z"), "s → /z/", "is, has, dogs"),
    GPC("t", "t", _p("T"), "t → /t/", "top"),
    GPC("p", "p", _p("P"), "p → /p/", "pig"),
    GPC("n", "n", _p("N"), "n → /n/", "nap"),
    GPC("c", "c", _p("K"), "c → /k/ (hard c)", "cat"),
    GPC("d", "d", _p("D"), "d → /d/", "dig"),
    GPC("f", "f", _p("F"), "f → /f/", "fan"),
    GPC("h", "h", _p("HH"), "h → /h/", "hat"),
    GPC("g", "g", _p("G"), "g → /g/ (hard g)", "got"),
    GPC("b", "b", _p("B"), "b → /b/", "bed"),
    GPC("l", "l", _p("L"), "l → /l/", "lip"),
    GPC("r", "r", _p("R"), "r → /r/", "rug"),
    GPC("k", "k", _p("K"), "k → /k/", "kid"),
    GPC("j", "j", _p("JH"), "j → /j/", "jam"),
    GPC("w", "w", _p("W"), "w → /w/", "wet"),
    GPC("v", "v", _p("V"), "v → /v/", "van"),
    GPC("y", "y", _p("Y"), "y → /y/ (consonant)", "yes", position="initial"),
    GPC("x", "x", _p("K S"), "x → /ks/", "box"),
    GPC("qu", "qu", _p("K W"), "qu → /kw/", "quit"),
    GPC("z", "z", _p("Z"), "z → /z/", "zip"),
    # ── Short vowels ─────────────────────────────────────────────────────
    GPC("short_a", "a", _p("AE"), "short a → /ă/", "cat"),
    GPC("short_e", "e", _p("EH"), "short e → /ĕ/", "bed"),
    GPC("short_i", "i", _p("IH"), "short i → /ĭ/", "sit"),
    # Many US dialects merge short o with /ô/ (CMU: dog = D AO G).
    GPC("short_o", "o", _p("AA", "AO"), "short o → /ŏ/", "hot, dog"),
    GPC("short_u", "u", _p("AH"), "short u → /ŭ/", "cup"),
    # ── FLOSS doubling and ck ────────────────────────────────────────────
    GPC("floss", "ff", _p("F"), "FLOSS rule: ff", "off", position="final"),
    GPC("floss", "ll", _p("L"), "FLOSS rule: ll", "bell", position="final"),
    GPC("floss", "ss", _p("S"), "FLOSS rule: ss", "miss", position="final"),
    GPC("floss", "zz", _p("Z"), "FLOSS rule: zz", "buzz", position="final"),
    GPC("ck", "ck", _p("K"), "ck → /k/", "duck"),
    # ── Consonant digraphs & trigraphs ───────────────────────────────────
    GPC("sh", "sh", _p("SH"), "sh → /sh/", "ship"),
    GPC("th", "th", _p("TH", "DH"), "th → /th/ (voiced & unvoiced)", "thin, this"),
    GPC("ch", "ch", _p("CH"), "ch → /ch/", "chip"),
    GPC("wh", "wh", _p("W", "HH W"), "wh → /w/", "when"),
    GPC("ng", "ng", _p("NG"), "ng → /ng/ (welded sounds: ang, ing, ong, ung)", "sing"),
    GPC("nk", "nk", _p("NG K"), "nk → /ngk/ (welded sounds: ank, ink, onk, unk)", "pink"),
    GPC("tch", "tch", _p("CH"), "tch → /ch/", "match"),
    GPC("dge", "dge", _p("JH"), "dge → /j/", "badge", position="final"),
    GPC("ph", "ph", _p("F"), "ph → /f/", "phone"),
    # ── Soft c / g ───────────────────────────────────────────────────────
    GPC("soft_c", "c", _p("S"), "soft c → /s/ (before e, i, y)", "city", before=("e", "i", "y")),
    GPC("soft_g", "g", _p("JH"), "soft g → /j/ (before e, i, y)", "gem", before=("e", "i", "y")),
    GPC("soft_c", "ce", _p("S"), "final ce → /s/", "dance", position="final"),
    GPC("soft_g", "ge", _p("JH"), "final ge → /j/", "hinge", position="final"),
    # ── Inflectional endings ─────────────────────────────────────────────
    GPC("suffix_ed", "ed", _p("T", "D", "IH D", "AX D"), "-ed → /t/, /d/, /ĭd/", "jumped, played, wanted", position="final"),
    GPC("suffix_es", "es", _p("IH Z", "AX Z"), "-es → /ĭz/", "boxes", position="final"),
    # ── R-controlled vowels ──────────────────────────────────────────────
    GPC("r_ar", "ar", _p("AA R"), "ar → /ar/", "car"),
    GPC("r_or", "or", _p("AO R"), "or → /or/", "fork"),
    GPC("r_or", "ore", _p("AO R"), "ore → /or/", "more", position="final"),
    GPC("r_er", "er", _p("ER"), "er → /er/", "her"),
    GPC("r_er", "ir", _p("ER"), "ir → /er/", "bird"),
    GPC("r_er", "ur", _p("ER"), "ur → /er/", "fur"),
    # ── Vowel teams ──────────────────────────────────────────────────────
    GPC("vt_ai", "ai", _p("EY"), "ai → /ā/", "rain"),
    GPC("vt_ai", "ay", _p("EY"), "ay → /ā/", "play"),
    GPC("vt_ee", "ee", _p("IY"), "ee → /ē/", "feet"),
    GPC("vt_ee", "ea", _p("IY"), "ea → /ē/", "seat"),
    GPC("vt_oa", "oa", _p("OW"), "oa → /ō/", "boat"),
    GPC("vt_oa", "ow", _p("OW"), "ow → /ō/", "snow"),
    GPC("vt_oa", "oe", _p("OW"), "oe → /ō/", "toe", position="final"),
    GPC("vt_igh", "igh", _p("AY"), "igh → /ī/", "night"),
    GPC("vt_igh", "ie", _p("AY"), "ie → /ī/", "pie"),
    GPC("vt_oo", "oo", _p("UW", "UH"), "oo → /oo/ (moon, book)", "moon, book"),
    GPC("vt_ew", "ew", _p("UW", "Y UW"), "ew → /ū/", "new"),
    GPC("vt_ew", "ue", _p("UW", "Y UW"), "ue → /ū/", "blue", position="final"),
    GPC("diph_ou", "ou", _p("AW"), "ou → /ow/", "out"),
    GPC("diph_ou", "ow", _p("AW"), "ow → /ow/", "cow"),
    GPC("diph_oi", "oi", _p("OY"), "oi → /oi/", "coin"),
    GPC("diph_oi", "oy", _p("OY"), "oy → /oi/", "boy"),
    GPC("vt_au", "au", _p("AO", "AA"), "au → /aw/", "haul"),
    GPC("vt_au", "aw", _p("AO", "AA"), "aw → /aw/", "saw"),
    GPC("vt_au", "all", _p("AO L", "AA L"), "all → /awl/", "ball"),
    GPC("ea_short", "ea", _p("EH"), "ea → /ĕ/", "head"),
    GPC("ou_oo", "ou", _p("UW"), "ou → /oo/", "soup"),
    GPC("ie_ee", "ie", _p("IY"), "ie → /ē/", "field"),
    # ── Vowel y ──────────────────────────────────────────────────────────
    GPC("y_vowel", "y", _p("IY", "AY", "IH"), "y as a vowel → /ē/ or /ī/", "happy, my"),
    # ── Silent letters ───────────────────────────────────────────────────
    GPC("silent_kn", "kn", _p("N"), "kn → /n/", "knot", position="initial"),
    GPC("silent_wr", "wr", _p("R"), "wr → /r/", "wrap", position="initial"),
    GPC("silent_gn", "gn", _p("N"), "gn → /n/", "gnat"),
    GPC("silent_mb", "mb", _p("M"), "mb → /m/", "lamb", position="final"),
    GPC("final_ve", "ve", _p("V"), "final ve → /v/ (English words don't end in v)", "have, give", position="final"),
    GPC("final_se", "se", _p("S", "Z"), "final se → /s/ or /z/ (silent e)", "sense, cheese", position="final"),
    # ── Multisyllabic ────────────────────────────────────────────────────
    GPC("c_le", "le", _p("AX L", "L"), "consonant-le → /ul/", "little", position="final"),
    GPC("suffix_tion", "tion", _p("SH AX N"), "tion → /shun/", "nation"),
    GPC("suffix_tion", "sion", _p("SH AX N", "ZH AX N"), "sion → /shun/ or /zhun/", "mission, vision"),
    GPC("suffix_ture", "ture", _p("CH ER"), "ture → /cher/", "picture", position="final"),
]

# Doubled consonants in multisyllabic words (rab-bit, kit-ten) map to one sound.
for _c in "bdfglmnprstz":
    _CATALOG.append(
        GPC("double_consonant", _c * 2, _p({"b": "B", "d": "D", "f": "F", "g": "G", "l": "L",
                                             "m": "M", "n": "N", "p": "P", "r": "R", "s": "S",
                                             "t": "T", "z": "Z"}[_c]),
            "doubled consonant → one sound", "rabbit")
    )

# Special GPCs handled by positional logic in the decoder (no plain grapheme entry).
SPECIAL_GPCS: dict[str, tuple[str, str]] = {
    "vce_a": ("a_e → /ā/ (silent-e)", "cake"),
    "vce_i": ("i_e → /ī/ (silent-e)", "bike"),
    "vce_o": ("o_e → /ō/ (silent-e)", "home"),
    "vce_u": ("u_e → /ū/ (silent-e)", "cute"),
    "vce_e": ("e_e → /ē/ (silent-e)", "these"),
    "open_syllable": ("open syllable: vowel at syllable end says its name", "go, me, ro-bot"),
    "schwa": ("schwa: unstressed vowel → /ə/", "a-bout, ba-sket"),
}

CATALOG: tuple[GPC, ...] = tuple(_CATALOG)

ALL_GPC_IDS: frozenset[str] = frozenset({g.id for g in CATALOG} | set(SPECIAL_GPCS))


def gpc_label(gpc_id: str) -> str:
    """Human-readable label for a GPC id (for teacher-facing explanations)."""
    if gpc_id in SPECIAL_GPCS:
        return SPECIAL_GPCS[gpc_id][0]
    labels = [g.label for g in CATALOG if g.id == gpc_id]
    if not labels:
        return gpc_id
    if len(labels) == 1:
        return labels[0]
    return "; ".join(dict.fromkeys(labels))


def gpcs_by_first_letter() -> dict[str, list[GPC]]:
    index: dict[str, list[GPC]] = {}
    for g in CATALOG:
        index.setdefault(g.grapheme[0], []).append(g)
    for lst in index.values():
        lst.sort(key=lambda g: -len(g.grapheme))
    return index
