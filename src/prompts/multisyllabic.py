"""Multisyllabic Decoding Routine — Syllable Division with Orthographic Mapping.

MCP Prompt primitive that generates step-by-step syllable division routines
for all six syllable types: closed, open, VCe, r-controlled, vowel team, C+le.

Based on Orton-Gillingham syllable division rules and orthographic mapping
(Kilpatrick, 2015).
"""

from __future__ import annotations

from typing import Any

from src.schemas.prompts import (
    MultisyllabicRoutine,
    SyllableDivisionStep,
)

# ── MCP Prompt Definition ───────────────────────────────────────────────────

MULTISYLLABIC_PROMPT = {
    "name": "multisyllabic_decoding_routine",
    "description": (
        "Generate a syllable-type division routine for multisyllabic words. "
        "Covers all six syllable types (closed, open, VCe, r-controlled, "
        "vowel team, C+le) with orthographic mapping. Uses VC/CV, V/CV, "
        "VC/V, and V/V division rules."
    ),
    "arguments": [
        {"name": "word", "description": "Multisyllabic word to decode", "required": True},
        {"name": "syllable_type_focus", "description": "Syllable type to focus on", "required": False},
        {"name": "grade_level", "description": "Target grade level", "required": False},
        {"name": "include_orthographic_mapping", "description": "Include orthographic mapping steps", "required": False},
    ],
}


# ── Syllable Division Rules ─────────────────────────────────────────────────


SYLLABLE_DIVISION_RULES: dict[str, dict[str, Any]] = {
    "VC/CV": {
        "rule": "Divide between two consonants (VC/CV) unless they form a digraph or blend.",
        "example": "rab/bit (VC/CV)", "signal": "Two consonants between vowels → split between them",
    },
    "V/CV": {
        "rule": "Divide after a long vowel (V/CV) — the first syllable is open.",
        "example": "ti/ger (V/CV)", "signal": "One consonant between vowels → try long vowel first",
    },
    "VC/V": {
        "rule": "Divide after the consonant if the first vowel is short (VC/V).",
        "example": "rob/in (VC/V)", "signal": "V/CV didn't work → try short vowel, divide after consonant",
    },
    "V/V": {
        "rule": "Divide between two vowels that are NOT a vowel team (V/V).",
        "example": "li/on (V/V)", "signal": "Two adjacent vowels, each in its own syllable",
    },
}


# ── Word Database ───────────────────────────────────────────────────────────

MULTISYLLABIC_WORD_DATA: dict[str, dict[str, Any]] = {
    "rabbit": {
        "syllables": ["rab", "bit"],
        "syllable_types": ["closed", "closed"],
        "division_rule": "VC/CV",
        "meaning": "A small animal with long ears",
        "sentence": "The rabbit hopped across the garden.",
        "connected": ["habit", "limit", "rapid"],
    },
    "fantastic": {
        "syllables": ["fan", "tas", "tic"],
        "syllable_types": ["closed", "closed", "closed"],
        "division_rule": "VC/CV",
        "meaning": "Extremely good or wonderful",
        "sentence": "You did a fantastic job on your reading test!",
        "connected": ["plastic", "drastic", "elastic"],
    },
    "tiger": {
        "syllables": ["ti", "ger"],
        "syllable_types": ["open", "r_controlled"],
        "division_rule": "V/CV",
        "meaning": "A large wild cat with stripes",
        "sentence": "The tiger prowled through the jungle at night.",
        "connected": ["paper", "pilot", "robot"],
    },
    "open": {
        "syllables": ["o", "pen"],
        "syllable_types": ["open", "closed"],
        "division_rule": "V/CV",
        "meaning": "Not closed or shut",
        "sentence": "Please open the book to page five.",
        "connected": ["over", "even", "item"],
    },
    "robin": {
        "syllables": ["rob", "in"],
        "syllable_types": ["closed", "closed"],
        "division_rule": "VC/V",
        "meaning": "A small bird with a red breast",
        "sentence": "A robin built a nest in our tree.",
        "connected": ["rapid", "valid", "solid"],
    },
    "table": {
        "syllables": ["ta", "ble"],
        "syllable_types": ["open", "c_le"],
        "division_rule": "C+le",
        "meaning": "A piece of furniture with a flat top",
        "sentence": "We sat at the table to eat dinner.",
        "connected": ["cable", "stable", "title"],
    },
    "complete": {
        "syllables": ["com", "plete"],
        "syllable_types": ["closed", "VCe"],
        "division_rule": "VC/CV",
        "meaning": "To finish or make whole",
        "sentence": "Please complete your work before recess.",
        "connected": ["compete", "concrete", "extreme"],
    },
    "sunset": {
        "syllables": ["sun", "set"],
        "syllable_types": ["closed", "closed"],
        "division_rule": "compound",
        "meaning": "The time when the sun goes down",
        "sentence": "The sky turned orange at sunset.",
        "connected": ["sunlight", "bathtub", "cupcake"],
    },
}


# ── Routine Builder ─────────────────────────────────────────────────────────


def build_multisyllabic_routine(
    word: str,
    syllable_type_focus: str = "mixed",
    grade_level: str = "3rd",
    include_orthographic_mapping: bool = True,
) -> dict[str, Any]:
    """Build a syllable division and decoding routine for a multisyllabic word.

    Args:
        word: The multisyllabic word to decode.
        syllable_type_focus: Syllable type to focus on.
        grade_level: Target grade level.
        include_orthographic_mapping: Include orthographic mapping steps.

    Returns:
        MultisyllabicRoutine with division steps, types, and orthographic mapping.
    """
    word_lower = word.lower().strip()

    # Look up word data
    word_data = MULTISYLLABIC_WORD_DATA.get(word_lower)
    if word_data is None:
        # Attempt auto-division
        word_data = _auto_divide(word_lower)

    # Build division steps
    division_steps: list[SyllableDivisionStep] = []
    syllables = word_data["syllables"]
    syllable_types = word_data["syllable_types"]
    division_rule = word_data["division_rule"]

    # Step 1: Spot the vowels
    vowels = "aeiouy"
    vowel_positions = [i for i, ch in enumerate(word_lower) if ch in vowels]
    visual_word = word_lower
    division_steps.append(SyllableDivisionStep(
        step_number=1,
        action="Spot the vowels — underline each vowel letter",
        visual=visual_word,
        teacher_language=f"I see {len(vowel_positions)} vowel letters in '{word}'. How many syllables do you think there are?",
    ))

    # Step 2: Identify syllable type
    division_steps.append(SyllableDivisionStep(
        step_number=2,
        action=f"Check consonants between vowels — division rule: {division_rule}",
        visual=".".join(syllables),
        teacher_language=f"Between those vowels, I see consonants. The rule is: {division_rule}. Let's divide: {' - '.join(syllables)}",
    ))

    # Step 3: Identify each syllable type
    for i, (syl, stype) in enumerate(zip(syllables, syllable_types)):
        division_steps.append(SyllableDivisionStep(
            step_number=3 + i,
            action=f"Syllable {i + 1}: '{syl}' is a {stype} syllable",
            visual=f"  {'  '.join('_' for _ in range(i))}{syl}",
            teacher_language=f"The syllable '{syl}' is a {stype} syllable. What sound does the vowel make in a {stype} syllable?",
        ))

    # Step 4: Blend
    division_steps.append(SyllableDivisionStep(
        step_number=len(division_steps) + 1,
        action="Blend syllables together",
        visual=" → ".join(syllables) + " → " + word_lower,
        teacher_language=f"Now blend: {'...'.join(syllables)}... {word}!",
    ))

    # Orthographic mapping
    ortho_mapping = None
    if include_orthographic_mapping:
        ortho_lines = []
        for i, syl in enumerate(syllables):
            ortho_lines.append(f"  Syllable {i + 1} ('{syl}'): {'-'.join(list(syl))}")
        ortho_mapping = (
            f"Orthographic Mapping: '{word}'\n" +
            "\n".join(ortho_lines) +
            f"\n  Full word: {word} — {len(word)} letters, {len(syllables)} syllables, " +
            f"{sum(len(s) for s in syllables)} graphemes mapped to sounds"
        )

    return {
        "word": word,
        "syllable_count": len(syllables),
        "syllable_breakdown": syllables,
        "syllable_types": syllable_types,
        "division_rule": division_rule,
        "division_rule_detail": SYLLABLE_DIVISION_RULES.get(division_rule, {}).get("rule", ""),
        "division_steps": [s.model_dump() for s in division_steps],
        "orthographic_mapping": ortho_mapping,
        "word_meaning": word_data.get("meaning", "Look up in dictionary"),
        "example_sentence": word_data.get("sentence", f"Can you use the word '{word}' in a sentence?"),
        "connected_words": word_data.get("connected", []),
        "framework_notes": (
            "Orton-Gillingham: syllable types provide a structured framework for "
            "decoding multisyllabic words. Kilpatrick (2015): orthographic mapping "
            "requires phoneme-level analysis of each syllable. NRP: systematic "
            "phonics instruction through the syllable level yields d=0.41-0.60."
        ),
    }


def _auto_divide(word: str) -> dict[str, Any]:
    """Attempt automatic syllable division for unknown words.

    Uses simple VC/CV heuristic as default for unfamiliar words.

    Args:
        word: The word to divide.

    Returns:
        Dictionary with syllables, types, and division rule.
    """
    vowels = set("aeiouy")
    vowel_pos = [i for i, c in enumerate(word) if c in vowels]

    if len(vowel_pos) <= 1:
        return {
            "syllables": [word],
            "syllable_types": ["closed"],
            "division_rule": "VC/CV",
            "meaning": "Single syllable word",
            "sentence": f"Can you use the word '{word}' in a sentence?",
            "connected": [],
        }

    # Try VC/CV division between first two vowels
    first = vowel_pos[0]
    second = vowel_pos[1]
    consonants_between = second - first - 1

    if consonants_between >= 2:
        # Split between the two consonants
        split = first + 2
    elif consonants_between == 1:
        # Try V/CV first (open syllable)
        split = first + 1
    else:
        # V/V — two adjacent vowels
        split = first + 1

    syllables = [word[:split], word[split:]]

    # Classify syllable types by heuristic
    types = []
    for syl in syllables:
        syl_lower = syl.lower()
        if syl_lower.endswith("le") and len(syl_lower) > 2:
            types.append("c_le")
        elif any(c in syl_lower for c in "aeiou") and syl_lower[-1] not in vowels:
            types.append("closed")
        elif any(c in syl_lower for c in "aeiou") and syl_lower[-1] in vowels and syl_lower[-1] != "e":
            types.append("open")
        else:
            types.append("closed")

    return {
        "syllables": syllables,
        "syllable_types": types,
        "division_rule": "VC/CV" if consonants_between >= 2 else "V/CV",
        "meaning": "Word divided by syllable rules",
        "sentence": f"Can you use the word '{word}' in a sentence?",
        "connected": [],
    }
