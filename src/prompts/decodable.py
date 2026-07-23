"""MCP Prompt: generate_aligned_decodable — decodable passage generator.

Returns an MCP prompt message that instructs the LLM to:
1. Fetch the phonics scope from get_phonics_scope
2. Draft a 4-6 sentence story using only taught graphemes + heart words
3. Run verify_decodable_text to check decodability
4. Self-correct any off-scope words
5. Return the final passage
"""

from __future__ import annotations


DECODABLE_PASSAGE_PROMPT = """You are a Science of Reading-aligned decodable passage generator.

Your task is to create a 4-6 sentence story that is FULLY decodable for students
at grade {grade}, unit {unit}. The passage should be on the topic of "{topic}".

Follow these steps EXACTLY:

STEP 1 — FETCH SCOPE:
Call get_phonics_scope(grade_level="{grade}", unit="{unit}") to retrieve:
- target_phonemes (sounds students are learning)
- taught_graphemes (letter patterns mastered)
- heart_words (irregular words to include sparingly)

STEP 2 — DRAFT PASSAGE:
Write a 4-6 sentence story using ONLY:
- Words built from the taught_graphemes
- Up to 2-3 heart_words from the scope (no more)
- CVC, CVCC, CCVC patterns appropriate for the grade level
- NO off-scope words or untaught patterns

CRITICAL RULES:
- No multisyllabic words unless all syllable types are taught
- No words with silent letters unless explicitly taught
- No words ending in -ing, -ed unless that suffix is taught
- Keep sentences short (5-8 words max for K-1, 8-12 for 2-3)

STEP 3 — VERIFY:
Call verify_decodable_text(text=<your passage>, grade_level="{grade}", unit="{unit}")
to check:
- decodable_pct (must be ≥ 95%)
- off_scope_words (must be empty)
- cueing_flags (must be empty — NO 3-cueing language)

STEP 4 — SELF-CORRECT:
If decodable_pct < 95% OR off_scope_words is not empty:
- Replace off-scope words using the substitutions from the verification result
- If no substitution is provided, rephrase the sentence to avoid that word
- Re-verify until decodable_pct ≥ 95%

STEP 5 — RETURN:
Output only the final passage text with:
- The passage title: "Decodable Story: Grade {grade}, Unit {unit}"
- The passage text (4-6 sentences)
- A teacher note listing any heart words used
- The final decodability percentage

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
