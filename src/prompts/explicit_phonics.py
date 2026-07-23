"""Explicit Phonics Routine — I Do / We Do / You Do Script Generator.

MCP Prompt primitive that generates structured explicit instruction scripts
with timing, multisensory cues, and research-aligned teacher language.

Based on Explicit Instruction (Archer & Hughes, 2011) and the
Orton-Gillingham approach.
"""

from __future__ import annotations

from typing import Any

from src.schemas.prompts import (
    ExplicitPhonicsInput,
    IWeYouScript,
    RoutineScript,
)

# ── MCP Prompt Definition ───────────────────────────────────────────────────

EXPLICIT_PHONICS_PROMPT = {
    "name": "explicit_phonics_routine",
    "description": (
        "Generate a structured I Do / We Do / You Do explicit phonics "
        "instruction script with timing, multisensory cue, and corrective "
        "feedback language. All scripts are research-aligned and deterministic "
        "— no LLM generation at runtime."
    ),
    "arguments": [
        {"name": "skill_name", "description": "The phonics skill to teach", "required": True},
        {"name": "grade_level", "description": "Target grade level", "required": False},
        {"name": "phoneme_examples", "description": "Example words containing the target pattern", "required": False},
        {"name": "multisensory_cue", "description": "Multisensory technique to embed", "required": False},
    ],
}


# ── Routine Builder ─────────────────────────────────────────────────────────


def build_explicit_phonics_routine(
    skill_name: str,
    grade_level: str = "1st",
    phoneme_examples: list[str] | None = None,
    multisensory_cue: str | None = None,
) -> dict[str, Any]:
    """Build an I Do / We Do / You Do explicit phonics routine.

    Args:
        skill_name: The phonics skill to teach (e.g., 'Short Vowel /a/').
        grade_level: Target grade level (K, 1st, 2nd, 3rd, 4th, 5th).
        phoneme_examples: Example words containing the target pattern.
        multisensory_cue: Optional multisensory technique.

    Returns:
        Dictionary with I Do / We Do / You Do script and metadata.
    """
    if phoneme_examples is None:
        phoneme_examples = []

    # Normalize the skill name for template matching
    skill_lower = skill_name.lower()

    # Select the script template based on skill
    script = _select_script(skill_lower, phoneme_examples)

    total_time = "~5-7 minutes"

    return {
        "title": f"Explicit Phonics Routine: {skill_name}",
        "target_skill": skill_name,
        "grade_level": grade_level,
        "total_time": total_time,
        "i_do": script.i_do,
        "we_do": script.we_do,
        "you_do": script.you_do,
        "timing": script.timing,
        "multisensory_cue": multisensory_cue or "None specified",
        "examples": phoneme_examples,
        "framework_notes": (
            "Explicit Instruction (Archer & Hughes, 2011): I Do (modeling), "
            "We Do (guided practice), You Do (independent practice) yields "
            "effect sizes of d=0.57-0.69. NRP Phonics: systematic, explicit "
            "instruction is significantly more effective than incidental teaching."
        ),
        "corrective_feedback": _get_corrective_feedback(skill_lower),
    }


def _select_script(skill_lower: str, examples: list[str]) -> IWeYouScript:
    """Select the appropriate I Do / We Do / You Do script based on skill."""
    examples_str = ", ".join(examples) if examples else "your target words"

    # Short vowel CVC
    if any(kw in skill_lower for kw in ("short vowel", "cvc", "/a/", "/e/", "/i/", "/o/", "/u/")):
        return IWeYouScript(
            i_do=(
                f"Watch me read this word. I touch under each letter and say "
                f"its sound, then blend them together. [{examples_str}]. "
                f"See how the vowel is trapped between consonants? That means "
                f"it says its short sound."
            ),
            we_do=(
                f"Now let's do one together. Point to the word. Ready? "
                f"Sound it out... blend it... Great! Let's try another. "
                f"Your turn to lead — I'll follow."
            ),
            you_do=(
                f"Here are your words to read by yourself. Touch each letter, "
                f"say the sound, blend it. Go ahead."
            ),
            timing="~1-2 minutes per stage",
        )

    # Silent-e / CVCe
    if any(kw in skill_lower for kw in ("silent", "cvce", "magic e", "long vowel")):
        return IWeYouScript(
            i_do=(
                f"Watch what happens when I add a silent 'e' at the end. "
                f"The vowel was short. Now with silent 'e', it says its name! "
                f"['cap' → 'cape']. The 'e' is silent — it's the boss of the vowel."
            ),
            we_do=(
                f"Let's try some together. I'll write a short vowel word. "
                f"Read it... Now I add silent 'e'. Read the new word! "
                f"What changed? Let's do more."
            ),
            you_do=(
                f"Here are some short-vowel words. Add silent 'e' to each one "
                f"and read the new word. What changes? What stays the same?"
            ),
            timing="~1-2 minutes per stage",
        )

    # Consonant blends
    if "blend" in skill_lower:
        return IWeYouScript(
            i_do=(
                f"Watch my mouth. When I say this word, I make TWO sounds at "
                f"the beginning — each one counts! They slide together but you "
                f"hear both."
            ),
            we_do=(
                f"Let's use our fingers. Every time you hear a sound at the "
                f"beginning, hold up a finger. How many sounds? Let's do more!"
            ),
            you_do=(
                f"Here's a list of words. Read each one, holding up a finger "
                f"for every sound at the beginning. Go!"
            ),
            timing="~1-2 minutes per stage",
        )

    # Digraphs
    if "digraph" in skill_lower:
        return IWeYouScript(
            i_do=(
                f"When I see these two letters together, my brain says 'these "
                f"are a team — they make ONE new sound.' Watch my mouth. Two "
                f"letters, one sound."
            ),
            we_do=(
                f"Let's sort some words. I'll say a word and you tell me which "
                f"digraph you hear — beginning or end. Ready?"
            ),
            you_do=(
                f"Read these words and circle the digraph in each one. "
                f"Remember — if two letters make one sound, they're a team!"
            ),
            timing="~1-2 minutes per stage",
        )

    # Generic explicit instruction template (fallback)
    return IWeYouScript(
        i_do=(
            f"Watch me as I model {skill_lower}. Notice what I do step by "
            f"step. Pay attention to my thinking as I work through this."
        ),
        we_do=(
            f"Now let's do this together. I'll start, and you join in. "
            f"Ready? Together... Good! Let's try another one. This time "
            f"you lead and I'll follow."
        ),
        you_do=(
            f"Your turn to practice independently. Work through these "
            f"examples on your own. I'll check your work when you're done."
        ),
        timing="~1-2 minutes per stage",
    )


def _get_corrective_feedback(skill_lower: str) -> dict[str, str]:
    """Get corrective feedback language for the skill."""
    if any(kw in skill_lower for kw in ("short vowel", "cvc")):
        return {
            "error": "The vowel is closed in by a consonant. What sound does it make? Blend again.",
            "praise": "You blended that word perfectly! Your brain is mapping those sounds.",
        }
    elif any(kw in skill_lower for kw in ("silent", "cvce")):
        return {
            "error": "I see a silent 'e'. What does it tell the vowel to do? Say the vowel's name and try again.",
            "praise": "You spotted the silent 'e' and made the vowel say its name!",
        }
    elif "blend" in skill_lower:
        return {
            "error": "I heard one sound missing from that blend. Let's finger-tap it together. Try again.",
            "praise": "You got every sound in that blend! Your ears and mouth worked together.",
        }
    elif "digraph" in skill_lower:
        return {
            "error": "Those two letters are a team. What sound do they make together? Try again.",
            "praise": "You recognized that digraph! Two letters, one sound — you got it.",
        }
    return {
        "error": "That's not quite right. Let me show you again, then you try.",
        "praise": "Excellent work! You're making great progress.",
    }
