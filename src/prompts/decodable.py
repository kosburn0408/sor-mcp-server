"""MCP Prompt: generate_aligned_decodable — decodable passage generator.

Returns an MCP prompt message that instructs the LLM to:
1. Fetch the phonics scope from get_phonics_scope
2. Draft a 4-6 sentence story using only taught graphemes + heart words
3. Run verify_decodable_text to check decodability
4. Revise any words the verifier flags, re-verifying until it passes
5. Return the final passage
"""

from __future__ import annotations


DECODABLE_PASSAGE_PROMPT = """You are a Science of Reading-aligned decodable passage generator.

Your task is to create a 4-6 sentence story that is FULLY decodable for students
at grade {grade}, unit {unit}. The passage should be on the topic of "{topic}".

Follow these steps EXACTLY:

STEP 1 — FETCH SCOPE:
Call get_phonics_scope(grade_level="{grade}", unit="{unit}") to retrieve:
- new_patterns (what this unit adds) and taught_graphemes (everything taught so far)
- heart_words (irregular words already taught; use sparingly)

STEP 2 — DRAFT PASSAGE:
Write a 4-6 sentence story that practices the new_patterns, using ONLY:
- Words built from the taught patterns
- Up to 2-3 of the taught heart_words (no others)
- Short sentences (5-8 words for K-1, 8-12 for 2-3)

STEP 3 — VERIFY:
Call verify_decodable_text(text=<your passage>, grade_level="{grade}", unit="{unit}").
The tool aligns every word to its dictionary pronunciation using only taught patterns. Check:
- meets_target (accessible_pct must reach target_pct)
- not_yet_decodable_words and missing_patterns (which untaught pattern blocks each word)
- irregular_words (irregular words not yet taught as heart words)
- not_in_dictionary_words (only character names are acceptable here)
- cueing_flags (must be empty)

STEP 4 — REVISE:
Replace every word listed in not_yet_decodable_words or irregular_words with a word
built only from taught patterns, or rephrase the sentence. Call verify_decodable_text
again. Repeat until meets_target is true and those lists are empty.
Never claim a passage is decodable without a passing verification result.

STEP 5 — RETURN:
- Title: "Decodable Story: Grade {grade}, Unit {unit}"
- The passage text (4-6 sentences)
- Teacher note: heart words used, and the new_patterns the story practices
- The final decodable_pct and accessible_pct from the last verification

DO NOT include cueing language like "look at the picture", "does it make sense",
"guess the word", or "skip and go on". Every word must be sounded out."""


async def generate_aligned_decodable(
    grade: str,
    unit: str,
    topic: str = "reading",
) -> str:
    """Generate a structured MCP prompt for creating a decodable passage.

    This is an MCP Prompt — it returns a message to the LLM that instructs
    it to use the tools to build and verify a decodable text.

    Args:
        grade: Grade level (K, 1, 2, 3, 4, 5).
        unit: Curriculum unit number.
        topic: Thematic topic for the passage (default: 'reading').

    Returns:
        MCP prompt message string that the LLM should follow.
    """
    return DECODABLE_PASSAGE_PROMPT.format(
        grade=grade,
        unit=unit,
        topic=topic,
    )
