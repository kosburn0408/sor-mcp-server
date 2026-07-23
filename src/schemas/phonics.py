"""Pydantic v2 schemas for phonics scope and decodability (API bridge).

Alias/extension of api.py schemas for tool-facing use.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class PhonicsScope(BaseModel):
    """A phonics scope and sequence for a specific grade/unit.

    Sourced from sor.edtechlabs.dev API.
    """

    grade_level: str = Field(description="Grade level (K-5)")
    unit: str = Field(description="Unit number")
    target_phonemes: list[str] = Field(
        default_factory=list,
        description="Target phonemes for this unit",
    )
    taught_graphemes: list[str] = Field(
        default_factory=list,
        description="Graphemes explicitly taught",
    )
    heart_words: list[dict[str, str]] = Field(
        default_factory=list,
        description="Heart words with regular/irregular parts",
    )
    unit_objectives: list[str] = Field(
        default_factory=list,
        description="Learning objectives",
    )
    prerequisite_skills: list[str] = Field(
        default_factory=list,
        description="Prerequisite skills",
    )

    model_config = {"extra": "allow"}


class DecodabilityResult(BaseModel):
    """Decodability verification result from the API."""

    decodable_pct: float = Field(ge=0.0, le=100.0)
    total_words: int = Field(ge=0)
    off_scope_words: list[str] = Field(default_factory=list)
    heart_words: list[str] = Field(default_factory=list)
    substitutions: dict[str, str] = Field(default_factory=dict)
    cueing_flags: list[str] = Field(default_factory=list)

    model_config = {"extra": "allow"}


class OrthographyMap(BaseModel):
    """Orthographic mapping for a single word."""

    word: str = Field(description="The word")
    phonemes: list[str] = Field(default_factory=list)
    graphemes: list[str] = Field(default_factory=list)
    syllable_breaks: list[int] = Field(default_factory=list)
    syllable_types: list[str] = Field(default_factory=list)

    model_config = {"extra": "allow"}


class StandardMatch(BaseModel):
    """A matched academic standard."""

    case_guid: str = Field(description="CASE GUID")
    state_code: str = Field(description="State standard code")
    grade: str = Field(description="Grade level")
    description: str = Field(description="Standard description")
    strand: str | None = Field(default=None)

    model_config = {"extra": "allow"}
