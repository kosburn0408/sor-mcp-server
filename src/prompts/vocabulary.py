"""Isabel Beck 3-Tier Vocabulary Pre-Teaching Prompt Builder.

Generates explicit Tier 2 academic vocabulary pre-teaching routines
grounded in Beck, McKeown & Kucan (2013) Bringing Words to Life.
"""
from __future__ import annotations

from typing import Any

VOCABULARY_TIER_PROMPT = """You are a Senior Reading Specialist and Vocabulary Expert.
Generate an explicit, 5-minute Tier 2 vocabulary pre-teaching routine for K-5 teachers.

Target Words: {words}
Grade Level: {grade}
Text Topic / Context: {topic}

Requirements (Beck 3-Tier Model):
1. **Student-Friendly Definition**: Use clear, accessible language without circular logic.
2. **Context Sentence**: Provide a sentence from a read-aloud or anchor text showing the word in context.
3. **Example Outside the Text**: Provide an everyday classroom example to broaden meaning.
4. **Active Student Engagement**: 2 quick turn-and-talk or thumbs-up/thumbs-down processing questions.
5. **Morphology / Word Family** (optional for 2nd-5th): Highlight roots, prefixes, or suffixes.

Formatting: Use GitHub-style markdown with bold terms and clear sections.
"""


def build_vocabulary_routine(words: list[str] | str, grade: str = "2nd", topic: str = "general reading") -> str:
    """Build formatted prompt string for Tier 2 vocabulary instruction."""
    if isinstance(words, list):
        word_str = ", ".join(words)
    else:
        word_str = words

    return VOCABULARY_TIER_PROMPT.format(words=word_str, grade=grade, topic=topic)
