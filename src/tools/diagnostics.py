"""Diagnostics tools: readability estimate and Simple View screening profile.

Moved from tools/lexile.py and server.py inline evaluation logic.
Now uses Pydantic v2 models for routing.
"""

from __future__ import annotations

import math
import re
import statistics
from typing import Any

from src.schemas.curriculum import CurriculumResult


# ── Readability Estimate ─────────────────────────────────────────────────────
#
# Uses the public Flesch-Kincaid Grade Level formula. This is NOT a Lexile
# measure (Lexile is a proprietary MetaMetrics framework). Readability formulas
# are unreliable for very short or early-reader texts, where decodability
# (verify_decodable_text) is the more meaningful measure.

_VOWEL_PHONEMES = {"AA", "AE", "AH", "AO", "AW", "AY", "EH", "ER", "EY", "IH", "IY", "OW", "OY", "UH", "UW"}


def _syllables(word: str) -> int:
    try:
        from src.engine.decoder import _cmu

        prons = _cmu().get(word.lower())
        if prons:
            return max(1, sum(1 for p in prons[0] if re.sub(r"\d", "", p) in _VOWEL_PHONEMES))
    except Exception:
        pass
    groups = re.findall(r"[aeiouy]+", word.lower())
    count = len(groups)
    if word.lower().endswith("e") and count > 1 and not word.lower().endswith(("le", "ee")):
        count -= 1
    return max(1, count)


def estimate_readability(text: str) -> dict[str, Any]:
    """Estimate text difficulty with the Flesch-Kincaid Grade Level formula.

    FK grade = 0.39 x (words / sentences) + 11.8 x (syllables / words) - 15.59
    """
    if not text or not text.strip():
        return {"error": "No text provided for analysis", "flesch_kincaid_grade": None}

    words = re.findall(r"[a-zA-Z]+(?:'[a-zA-Z]+)?", text)
    if not words:
        return {"error": "No recognizable words found in text", "flesch_kincaid_grade": None}

    sentences = [s for s in re.split(r"[.!?]+", text) if re.search(r"[A-Za-z]", s)]
    sentence_count = max(1, len(sentences))
    word_count = len(words)
    syllable_count = sum(_syllables(w) for w in words)

    words_per_sentence = word_count / sentence_count
    syllables_per_word = syllable_count / word_count
    fk_grade = 0.39 * words_per_sentence + 11.8 * syllables_per_word - 15.59

    warnings = []
    if word_count < 100:
        warnings.append("Fewer than 100 words: readability formulas are unreliable for short passages.")
    if fk_grade < 2:
        warnings.append(
            "Early-reader range: formulas say little about whether a K-2 student can read this text. "
            "Use verify_decodable_text to check it against taught phonics patterns."
        )

    return {
        "flesch_kincaid_grade": round(fk_grade, 1),
        "word_count": word_count,
        "sentence_count": sentence_count,
        "syllable_count": syllable_count,
        "mean_sentence_length": round(words_per_sentence, 1),
        "mean_syllables_per_word": round(syllables_per_word, 2),
        "unique_words": len({w.lower() for w in words}),
        "method": "Flesch-Kincaid Grade Level (public formula); syllables from the CMU Pronouncing Dictionary. Not a Lexile measure.",
        "warnings": warnings,
    }


# ── Simple View of Reading ──────────────────────────────────────────────────


DEFAULT_CUTOFF = 0.60

PROFILE_LABELS = {
    "on_track": "On track: word recognition and language comprehension both at or above the cutoff",
    "word_recognition_difficulty": "Specific word-recognition difficulty: decoding below the cutoff, language comprehension at or above it",
    "language_comprehension_difficulty": "Specific language-comprehension difficulty: language comprehension below the cutoff, decoding at or above it",
    "mixed_difficulty": "Mixed difficulty: both decoding and language comprehension below the cutoff",
}

SCREENING_CAVEAT = (
    "This is a screening profile based on the Simple View of Reading (Gough & Tunmer, 1986), "
    "not a diagnosis. It cannot identify dyslexia or any other disability; that requires a "
    "comprehensive evaluation by qualified professionals. Profiles near the cutoff are uncertain "
    "and should be confirmed with additional assessment."
)


def evaluate_simple_view(
    decoding: float,
    language_comprehension: float,
    grade: str = "1st",
    cutoff: float | None = None,
    diagnosed_skills: list[str] | None = None,
) -> dict[str, Any]:
    """Place a student in a Simple View of Reading screening quadrant.

    Args:
        decoding: Word-recognition/decoding score on a 0.0-1.0 scale.
        language_comprehension: Language/listening comprehension score, 0.0-1.0.
        grade: Grade level string (e.g., '1st').
        cutoff: At-risk threshold on the same 0-1 scale. Set this to your
            screener's benchmark. Defaults to 0.60, which is a placeholder,
            not a research-established value.
        diagnosed_skills: Specific skills identified by a phonics or phonological
            diagnostic (e.g. ['vowel_teams']). Intervention cards are only
            attached for skills that have actually been diagnosed; a single
            screening score cannot tell you which phonics skill to teach.

    Returns:
        Dictionary with diagnostic, caveat, remediations and next_steps.
    """
    from src.tools.remediation import (
        DEFICIT_TO_REMEDIATION,
        REMEDIATION_TABLE,
        get_bulk_remediations,
        list_available_remediations,
    )

    for name, value in (("Decoding", decoding), ("Language comprehension", language_comprehension)):
        if not 0.0 <= value <= 1.0:
            return {
                "error_code": "ERR_INVALID_SCORE_RANGE",
                "error": f"{name} score {value} is outside valid range [0.0, 1.0]",
            }

    cutoff_is_default = cutoff is None
    cut = DEFAULT_CUTOFF if cutoff is None else float(cutoff)
    if not 0.0 < cut < 1.0:
        return {"error_code": "ERR_INVALID_SCORE_RANGE", "error": f"cutoff {cut} must be between 0 and 1"}

    low_d = decoding < cut
    low_lc = language_comprehension < cut
    if not low_d and not low_lc:
        profile = "on_track"
    elif low_d and not low_lc:
        profile = "word_recognition_difficulty"
    elif low_lc and not low_d:
        profile = "language_comprehension_difficulty"
    else:
        profile = "mixed_difficulty"

    near_cutoff = abs(decoding - cut) < 0.05 or abs(language_comprehension - cut) < 0.05

    skills = [s for s in (diagnosed_skills or []) if DEFICIT_TO_REMEDIATION.get(s, s) in REMEDIATION_TABLE]
    unknown_skills = [s for s in (diagnosed_skills or []) if s not in skills]
    remediations = get_bulk_remediations(skills, grade) if skills else []

    if profile == "on_track":
        next_steps = "On track at this screening. Continue core instruction and keep screening on schedule."
    elif profile == "word_recognition_difficulty":
        next_steps = (
            "Give a phonics and phonological awareness diagnostic to pinpoint which skills to teach, "
            "then provide explicit, systematic small-group intervention on those skills and monitor progress. "
            "If word-reading difficulty persists despite good intervention, refer for evaluation; "
            "this tool cannot identify dyslexia."
        )
    elif profile == "language_comprehension_difficulty":
        next_steps = (
            "Assess oral language: vocabulary, listening comprehension and background knowledge. "
            "Build these through explicit vocabulary instruction and interactive read-alouds with discussion."
        )
    else:
        next_steps = (
            "Assess both word reading and oral language. Provide intensive intervention on diagnosed "
            "decoding skills while also building vocabulary and listening comprehension, and monitor progress closely."
        )
    if low_d and not skills:
        next_steps += " Once a diagnostic identifies specific skills, pass them as diagnosed_skills to attach intervention cards."

    result: dict[str, Any] = {
        "diagnostic": {
            "decoding_score": decoding,
            "language_comprehension_score": language_comprehension,
            "reading_profile": profile,
            "profile_label": PROFILE_LABELS[profile],
            "cutoff": cut,
            "cutoff_is_default": cutoff_is_default,
            "near_cutoff": near_cutoff,
            "deficit_codes": skills,
        },
        "caveat": SCREENING_CAVEAT,
        "remediations": [r.to_markdown() for r in remediations],
        "next_steps": next_steps,
    }
    if cutoff_is_default:
        result["warnings"] = [
            "Using placeholder cutoff 0.60. Set 'cutoff' to your screener's benchmark on the same 0-1 scale."
        ]
    if unknown_skills:
        result.setdefault("warnings", []).append(f"Unrecognized skills ignored: {', '.join(unknown_skills)}")
    if low_d and not skills:
        result["available_skills"] = list_available_remediations()["remediations"]
    return result


# ── Scope Sequence Lookup (used by router) ──────────────────────────────────


SCOPE_SEQUENCE: dict[str, dict[str, list[str]]] = {
    "K": {
        "phonology": {
            "concepts": [
                "Rhyming words", "Syllable counting", "Initial/final sound identification",
                "Phoneme blending (2-3 sounds)", "Phoneme segmentation (2-3 sounds)",
            ],
            "phonemes": ["/a/", "/e/", "/i/", "/o/", "/u/", "/m/", "/s/", "/t/", "/p/", "/n/", "/d/", "/k/", "/g/", "/b/", "/f/"],
            "syllable_types": ["closed"],
            "prerequisites": ["Print concepts", "Letter recognition"],
            "next_steps": ["CVC words", "Digraph introduction"],
        },
        "morphology": {
            "concepts": ["Plural -s (spoken)"],
            "phonemes": [],
            "syllable_types": [],
            "prerequisites": ["Oral language development"],
            "next_steps": ["Inflectional endings", "Compound words"],
        },
    },
    "1": {
        "phonology": {
            "concepts": [
                "CVC blending/segmenting", "Consonant digraphs (sh, ch, th, wh, ck)",
                "Consonant blends (l-blends, r-blends, s-blends)",
                "CVCe silent-e pattern", "Open syllables (CV)",
            ],
            "phonemes": ["/sh/", "/ch/", "/th/", "/wh/", "/ng/", "/qu/", "/ā/", "/ē/", "/ī/", "/ō/", "/ū/"],
            "syllable_types": ["closed", "VCe", "open"],
            "prerequisites": ["K phoneme awareness", "CVC decoding"],
            "next_steps": ["Vowel teams", "R-controlled vowels", "Multisyllabic words"],
        },
        "morphology": {
            "concepts": ["Inflectional endings (-s, -es, -ed, -ing)", "Compound words"],
            "phonemes": [],
            "syllable_types": [],
            "prerequisites": ["K oral language"],
            "next_steps": ["Prefix un-/re-", "Suffix -er/-est"],
        },
    },
    "2": {
        "phonology": {
            "concepts": [
                "Vowel teams (ai, ay, ee, ea, oa, oe, ue, ui)",
                "R-controlled vowels (ar, or, er, ir, ur)",
                "Diphthongs (oi, oy, ou, ow)", "Silent letters (wr, kn, gn, mb)",
                "Three-letter blends (scr, str, spr, spl)",
                "Multisyllabic decoding (VC/CV)",
            ],
            "phonemes": ["/oi/", "/oy/", "/ou/", "/ow/", "/ar/", "/or/", "/er/", "/ir/", "/ur/"],
            "syllable_types": ["closed", "VCe", "open", "vowel_team", "r_controlled"],
            "prerequisites": ["Grade 1 phonics", "Silent-e mastery"],
            "next_steps": ["C+le syllables", "Advanced vowel teams"],
        },
        "morphology": {
            "concepts": [
                "Prefix un-/re-/pre-/mis-/dis-", "Suffix -er/-est/-ly/-ful/-less",
                "Past tense -ed (3 sounds)", "Plural rules",
            ],
            "phonemes": [],
            "syllable_types": [],
            "prerequisites": ["Grade 1 morphology"],
            "next_steps": ["Greek/Latin roots", "Advanced affixes"],
        },
    },
    "3": {
        "phonology": {
            "concepts": [
                "Advanced vowel teams (au, aw, ei, ey, eu, ew)",
                "Consonant+le syllables", "Schwa sound",
                "Multisyllabic decoding (all 6 types)",
            ],
            "phonemes": ["/aw/", "/au/", "/schwa/"],
            "syllable_types": ["closed", "VCe", "open", "vowel_team", "r_controlled", "c_le"],
            "prerequisites": ["Grade 2 phonics", "Basic syllable division"],
            "next_steps": ["Complex morphology", "Content-area vocabulary"],
        },
        "morphology": {
            "concepts": [
                "Greek roots (bio, graph, phon, scope)",
                "Latin roots (dict, port, struct, tract)",
                "Prefixes (sub-, inter-, super-, trans-)",
                "Suffixes (-able, -ible, -ance, -ence, -ify, -ize)",
            ],
            "phonemes": [],
            "syllable_types": [],
            "prerequisites": ["Grade 2 morphology"],
            "next_steps": ["Advanced Greek/Latin roots", "Content-specific morphology"],
        },
    },
    "4": {
        "phonology": {
            "concepts": [
                "Advanced multisyllabic decoding", "Stress and accent patterns",
                "Schwa in unstressed syllables",
            ],
            "phonemes": [],
            "syllable_types": ["all"],
            "prerequisites": ["Grade 3 phonics"],
            "next_steps": ["Grade 5 fluency"],
        },
        "morphology": {
            "concepts": [
                "Advanced affixes (anti-, semi-, mid-, -ous, -al, -ic, -ive)",
                "Greek combining forms", "Syllable stress patterns",
            ],
            "phonemes": [],
            "syllable_types": [],
            "prerequisites": ["Grade 3 morphology"],
            "next_steps": ["Grade 5 advanced morphology"],
        },
    },
    "5": {
        "phonology": {
            "concepts": [
                "Fluent multisyllabic decoding", "Irregular spelling patterns",
                "Content-area vocabulary decoding",
            ],
            "phonemes": [],
            "syllable_types": ["all"],
            "prerequisites": ["Grade 4 phonics", "All syllable types"],
            "next_steps": ["Middle school literacy"],
        },
        "morphology": {
            "concepts": [
                "Full affix system", "Academic word families",
                "Etymology patterns across content areas",
            ],
            "phonemes": [],
            "syllable_types": [],
            "prerequisites": ["Grade 4 morphology"],
            "next_steps": ["Middle school content literacy"],
        },
    },
}

# Vocabulary and fluency scope data (simplified)
_VOCAB_FLUENCY: dict[str, dict[str, dict[str, list[str]]]] = {
    "K": {
        "vocabulary": {
            "concepts": ["Tier 1 oral vocabulary", "Category sorting", "Story vocabulary"],
            "prerequisites": ["Oral language"],
            "next_steps": ["Tier 2 introduction", "Text-based vocabulary"],
        },
        "fluency": {
            "concepts": ["Letter naming fluency", "Initial sound fluency"],
            "prerequisites": ["Letter knowledge"],
            "next_steps": ["CVC word reading fluency"],
        },
    },
    "1": {
        "vocabulary": {
            "concepts": ["Tier 2 oral vocabulary", "Multiple meaning words", "Shades of meaning"],
            "prerequisites": ["K vocabulary"],
            "next_steps": ["Context clues", "Academic vocabulary"],
        },
        "fluency": {
            "concepts": ["CVC word automaticity", "Sight word fluency", "Phrased reading"],
            "prerequisites": ["K fluency"],
            "next_steps": ["Silent-e fluency", "Digraph fluency"],
        },
    },
}


def get_scope_sequence(grade: str, strand: str) -> dict[str, Any]:
    """Retrieve scope and sequence data for a grade and strand.

    Args:
        grade: Grade level (K, 1, 2, 3, 4, 5).
        strand: Literacy strand (phonology, morphology, vocabulary, fluency, comprehension).

    Returns:
        Dictionary with concepts, prerequisites, and next_steps.
    """
    if strand in ("phonology", "morphology"):
        entry = SCOPE_SEQUENCE.get(grade, {}).get(strand)
        if entry:
            return dict(entry)
    if strand in ("vocabulary", "fluency"):
        entry = _VOCAB_FLUENCY.get(grade, {}).get(strand)
        if entry:
            return dict(entry)
    if strand == "comprehension":
        return {
            "concepts": [
                f"Grade {grade} comprehension strategies",
                "Literal and inferential questioning",
            ],
            "prerequisites": ["Decoding fluency", "Vocabulary knowledge"],
            "next_steps": ["Higher-order thinking", "Cross-text synthesis"],
        }

    return {"concepts": [], "prerequisites": [], "next_steps": []}
