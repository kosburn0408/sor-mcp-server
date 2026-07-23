"""Prompts for the Science of Reading MCP server.

MCP Prompt primitives for structured instructional routines:
  - explicit_phonics_routine: I Do / We Do / You Do script generator
  - decodable_passage_builder: Constrained passage using only mastered phonemes
  - multisyllabic_decoding_routine: Syllable-type division with orthographic mapping
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

__all__ = [
    "build_explicit_phonics_routine",
    "EXPLICIT_PHONICS_PROMPT",
    "build_decodable_passage",
    "DECODABLE_PASSAGE_PROMPT",
    "build_multisyllabic_routine",
    "MULTISYLLABIC_PROMPT",
]
