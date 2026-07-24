"""Prompts for the Science of Reading MCP server.

MCP Prompt primitives for structured instructional routines:
  - explicit_phonics_routine: I Do / We Do / You Do script generator
  - decodable_passage_builder: Constrained passage using only mastered phonemes
  - multisyllabic_decoding_routine: Syllable-type division with orthographic mapping
  - vocabulary_tier_routine: Beck Tier 2 academic vocabulary pre-teaching script
  - standards_alignment_prompt: Standards Satchel (Rosetta) CASE network alignment
"""

from src.prompts.explicit_phonics import (
    build_explicit_phonics_routine,
    EXPLICIT_PHONICS_PROMPT,
)
from src.prompts.decodable_passage import (
    build_decodable_passage,
    DECODABLE_PASSAGE_PROMPT,
)
from src.prompts.multisyllabic import (
    build_multisyllabic_routine,
    MULTISYLLABIC_PROMPT,
)
from src.prompts.vocabulary import (
    build_vocabulary_routine,
    VOCABULARY_TIER_PROMPT,
)
from src.prompts.standards import (
    build_standards_prompt,
    STANDARDS_ALIGNMENT_PROMPT,
)

__all__ = [
    "build_explicit_phonics_routine",
    "EXPLICIT_PHONICS_PROMPT",
    "build_decodable_passage",
    "DECODABLE_PASSAGE_PROMPT",
    "build_multisyllabic_routine",
    "MULTISYLLABIC_PROMPT",
    "build_vocabulary_routine",
    "VOCABULARY_TIER_PROMPT",
    "build_standards_prompt",
    "STANDARDS_ALIGNMENT_PROMPT",
]
