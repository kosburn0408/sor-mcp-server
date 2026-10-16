"""MCP Resource — Theoretical Frameworks and Syllable Division Rules.

Static reference content for Science of Reading frameworks:
- Scarborough's Reading Rope
- Simple View of Reading
- Five Pillars of Reading (NRP)
- Active View of Reading
- Four-Part Processing Model
- Syllable Division Rules (all six types)
"""

from __future__ import annotations

from typing import Any

# ── Framework Reference Data ────────────────────────────────────────────────


FRAMEWORKS: list[dict[str, Any]] = [
    {
        "name": "Simple View of Reading",
        "authors": "Gough & Tunmer",
        "year": 1986,
        "description": (
            "Reading comprehension is the product of decoding (word recognition) "
            "and linguistic comprehension. D × LC = RC. Neither skill alone is "
            "sufficient — both must be developed."
        ),
        "strands": ["decoding", "linguistic_comprehension"],
        "formula": "Decoding × Language Comprehension = Reading Comprehension",
        "implications": [
            "Assessment must measure both decoding and comprehension separately",
            "Intervention targets depend on which component is weak",
            "A student with strong decoding but weak comprehension needs language intervention",
            "A student with weak decoding but strong comprehension needs phonics intervention",
        ],
        "url": "https://doi.org/10.1177/074193258600700104",
    },
    {
        "name": "Scarborough's Reading Rope",
        "authors": "Scarborough, H.S.",
        "year": 2001,
        "description": (
            "Reading is composed of interconnected strands across two domains: "
            "Language Comprehension (background knowledge, vocabulary, language "
            "structures, verbal reasoning, literacy knowledge) and Word Recognition "
            "(phonological awareness, decoding, sight recognition). These strands "
            "become increasingly intertwined and automatic as skilled reading develops."
        ),
        "strands": {
            "language_comprehension": [
                "background_knowledge", "vocabulary", "language_structures",
                "verbal_reasoning", "literacy_knowledge",
            ],
            "word_recognition": [
                "phonological_awareness", "decoding", "sight_recognition",
            ],
        },
        "implications": [
            "Reading difficulties can arise from weakness in any strand",
            "Intervention must target the specific weak strand(s)",
            "Strands develop interactively — progress in one supports others",
        ],
        "url": "https://www.readingrockets.org/topics/about-reading/articles/scarboroughs-reading-rope",
    },
    {
        "name": "National Reading Panel — Five Pillars",
        "authors": "National Reading Panel",
        "year": 2000,
        "description": (
            "Identified five essential, research-based components of effective "
            "reading instruction through meta-analysis of empirical studies."
        ),
        "pillars": [
            {"name": "Phonemic Awareness",
             "description": "Ability to hear, identify, and manipulate individual sounds in spoken words."},
            {"name": "Phonics",
             "description": "Relationship between letters (graphemes) and sounds (phonemes) in written language."},
            {"name": "Fluency",
             "description": "Ability to read text accurately, quickly, and with proper expression."},
            {"name": "Vocabulary",
             "description": "Knowledge of word meanings needed for comprehension."},
            {"name": "Comprehension",
             "description": "Ability to understand, remember, and communicate meaning from text."},
        ],
        "evidence_note": (
            "The Panel ran meta-analyses for phonemic awareness, phonics and guided oral "
            "reading only. It ran none for vocabulary or text comprehension, so there is no "
            "single pooled effect size per pillar. Verified figures: phonics d = 0.41 "
            "(Ehri et al., 2001); phonemic awareness d = 0.53 on reading and 0.59 on spelling."
        ),
        "url": "https://www.nichd.nih.gov/publications/pubs/nrp/findings",
    },
    {
        "name": "Active View of Reading",
        "authors": "Duke & Cartwright",
        "year": 2021,
        "description": (
            "Extends the Simple View by adding active self-regulation and bridging processes "
            "(for example reading fluency and vocabulary knowledge used in reading) that "
            "connect word recognition and language comprehension."
        ),
        "strands": ["word_recognition", "language_comprehension", "active_self_regulation", "bridging_processes"],
        "implications": [
            "Language comprehension work (vocabulary, knowledge, read-alouds) should run alongside decoding instruction, not wait for it",
            "Motivation, attention and strategy use shape comprehension and are worth teaching and monitoring",
        ],
        "url": "https://readingrockets.org/resources/resource-library/science-reading-progresses-communicating-advances-beyond-simple-view",
    },
    {
        "name": "Four-Part Processing Model",
        "authors": "Seidenberg & McClelland",
        "year": 1989,
        "description": (
            "Word recognition involves four interconnected processors: phonological "
            "(sound), orthographic (spelling), meaning (semantics), and context "
            "(syntax/pragmatics). Fluent reading requires all four processors "
            "working in parallel."
        ),
        "processors": ["phonological", "orthographic", "meaning", "context"],
        "implications": [
            "Phonics instruction builds the phonological-orthographic connection",
            "Vocabulary instruction builds the orthographic-meaning connection",
            "Fluency practice automates all processor connections",
        ],
        "url": "https://doi.org/10.1037/0033-295X.96.4.523",
    },
]


# ── Syllable Division Rules ─────────────────────────────────────────────────


SYLLABLE_DIVISION_RULES: dict[str, str] = {
    "closed": (
        "A closed syllable ends in a consonant. The vowel makes its short sound. "
        "Examples: cat, rabbit, napkin."
    ),
    "open": (
        "An open syllable ends in a vowel. The vowel makes its long sound (says its name). "
        "Examples: go, tiger, paper."
    ),
    "VCe": (
        "A vowel-consonant-e syllable has a silent 'e' at the end that makes the "
        "vowel say its long sound. Examples: cake, complete, inside."
    ),
    "r_controlled": (
        "An r-controlled syllable has a vowel followed by 'r'. The 'r' controls "
        "the vowel and changes its sound. Examples: car, bird, turn, fork."
    ),
    "vowel_team": (
        "A vowel team syllable has two vowels working together to make one sound. "
        "Usually the first vowel does the talking. Examples: rain, boat, see, play."
    ),
    "c_le": (
        "A consonant-le syllable is an unaccented final syllable containing a "
        "consonant + 'le'. Examples: table, little, candle."
    ),
}


# ── Division Procedure Rules ────────────────────────────────────────────────


DIVISION_PROCEDURE_RULES: list[dict[str, Any]] = [
    {
        "rule_id": "VC/CV",
        "description": "Divide between two consonants (unless they form a digraph or blend).",
        "example": "rab/bit, nap/kin",
        "signal": "Two consonants between vowels",
        "procedure": [
            "Locate the vowels",
            "Count consonants between them",
            "If 2+ consonants: divide between them",
            "If they form a digraph: keep together",
        ],
    },
    {
        "rule_id": "V/CV",
        "description": "Divide after a long vowel — first syllable is open.",
        "example": "ti/ger, pa/per",
        "signal": "One consonant between vowels — try long vowel first",
        "procedure": [
            "Locate the vowels",
            "One consonant between: try V/CV (open first syllable)",
            "If it sounds right: keep the division",
            "If not: try VC/V",
        ],
    },
    {
        "rule_id": "VC/V",
        "description": "Divide after the consonant if the first vowel is short.",
        "example": "rob/in, cab/in",
        "signal": "V/CV didn't work — try short vowel",
        "procedure": [
            "If V/CV didn't sound right",
            "Move the consonant to the first syllable",
            "The first syllable is now closed (short vowel)",
        ],
    },
    {
        "rule_id": "V/V",
        "description": "Divide between two vowels that are NOT a vowel team.",
        "example": "li/on, di/et",
        "signal": "Two adjacent vowels, each in its own syllable",
        "procedure": [
            "Check: are the two vowels a known vowel team?",
            "If not a team: divide between them",
            "Each vowel is in its own syllable",
        ],
    },
    {
        "rule_id": "C+le",
        "description": "Consonant + le forms its own syllable at the end of a word.",
        "example": "ta/ble, bub/ble",
        "signal": "Word ends in consonant + le",
        "procedure": [
            "Count back 3 letters from the end: the consonant + le is one syllable",
            "Divide before that consonant",
            "The first syllable type determines the vowel sound",
        ],
    },
    {
        "rule_id": "compound",
        "description": "Divide compound words between the two base words.",
        "example": "sun/set, bath/tub",
        "signal": "The word is made of two smaller words",
        "procedure": [
            "Identify the two base words in the compound",
            "Divide between them",
            "Decode each base word separately",
            "Blend together",
        ],
    },
]


# ── Resource API ────────────────────────────────────────────────────────────


def list_frameworks_resource() -> dict[str, Any]:
    """Return all theoretical frameworks as an MCP Resource."""
    return {
        "total": len(FRAMEWORKS),
        "frameworks": FRAMEWORKS,
        "syllable_types": [
            {"type": k, "description": v} for k, v in SYLLABLE_DIVISION_RULES.items()
        ],
        "division_rules": DIVISION_PROCEDURE_RULES,
    }


def get_framework(name: str) -> dict[str, Any] | None:
    """Get a specific framework by name.

    Args:
        name: Framework name (e.g., 'Simple View of Reading').

    Returns:
        Framework dictionary or None if not found.
    """
    for fw in FRAMEWORKS:
        if fw["name"].lower() == name.lower():
            return fw
    return None
