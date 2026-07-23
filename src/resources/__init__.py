"""Resources for the Science of Reading MCP server.

MCP Resource primitives providing static reference content:
  - Frameworks (Scarborough's Rope, Simple View, Syllable Rules)
  - Word Lists (Heart words, Dolch, Fry by grade level)
"""

from src.resources.frameworks import (
    FRAMEWORKS,
    SYLLABLE_DIVISION_RULES,
    list_frameworks_resource,
    get_framework,
)
from src.resources.word_lists import (
    HEART_WORDS,
    DOLCH_LISTS,
    FRY_LISTS,
    HIGH_FREQUENCY_WORDS,
    get_word_list,
    list_word_lists,
)

__all__ = [
    "FRAMEWORKS",
    "SYLLABLE_DIVISION_RULES",
    "list_frameworks_resource",
    "get_framework",
    "HEART_WORDS",
    "DOLCH_LISTS",
    "FRY_LISTS",
    "HIGH_FREQUENCY_WORDS",
    "get_word_list",
    "list_word_lists",
]
