"""Pydantic v2 schemas for sor.edtechlabs.dev API request/response models.

Defines the wire format for all four API endpoints plus shared types.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


# ── Phonics Scope ───────────────────────────────────────────────────────────


class PhonicsScopeRequest(BaseModel):
    """Request for GET /api/v1/phonics/scope."""

    grade: str = Field(
        description="Grade level (K, 1, 2, 3, 4, 5)",
        min_length=1,
        max_length=1,
    )
    unit: str = Field(
        default="1",
        description="Curriculum unit number",
    )


class PhonicsScope(BaseModel):
    """Response from GET /api/v1/phonics/scope."""

    grade_level: str = Field(description="Grade level")
    unit: str = Field(description="Unit number")
    target_phonemes: list[str] = Field(
        default_factory=list,
        description="Phonemes targeted in this unit",
    )
    taught_graphemes: list[str] = Field(
        default_factory=list,
        description="Graphemes taught in this unit",
    )
    heart_words: list[dict[str, str]] = Field(
        default_factory=list,
        description="Heart words with regular/irregular parts noted",
    )
    unit_objectives: list[str] = Field(
        default_factory=list,
        description="Instructional objectives for this unit",
    )
    prerequisite_skills: list[str] = Field(
        default_factory=list,
        description="Skills that should be mastered before this unit",
    )

    model_config = {"extra": "allow"}


# ── Decodability ────────────────────────────────────────────────────────────


class DecodabilityRequest(BaseModel):
    """Request for POST /api/v1/decodability/verify."""

    text: str = Field(
        min_length=1,
        max_length=5000,
        description="Text passage to verify",
    )
    grade: str = Field(
        min_length=1,
        max_length=1,
        description="Grade level (K-5)",
    )
    unit: str = Field(
        default="1",
        description="Curriculum unit for scope reference",
    )


class DecodabilityResult(BaseModel):
    """Response from POST /api/v1/decodability/verify."""

    decodable_pct: float = Field(
        ge=0.0,
        le=100.0,
        description="Percentage of words that are fully decodable",
    )
    total_words: int = Field(description="Total word count")
    off_scope_words: list[str] = Field(
        default_factory=list,
        description="Words containing untaught patterns",
    )
    heart_words: list[str] = Field(
        default_factory=list,
        description="Heart words found in text",
    )
    substitutions: dict[str, str] = Field(
        default_factory=dict,
        description="Suggested decodable alternatives for off-scope words",
    )
    cueing_flags: list[str] = Field(
        default_factory=list,
        description="MSV/3-cueing language detected in text",
    )

    model_config = {"extra": "allow"}


# ── Orthography Mapping ─────────────────────────────────────────────────────


class OrthographyRequest(BaseModel):
    """Request for GET /api/v1/orthography/map."""

    words: list[str] = Field(
        min_length=1,
        max_length=50,
        description="List of words to map (up to 50)",
    )


class OrthographyMap(BaseModel):
    """Response entry for GET /api/v1/orthography/map."""

    word: str = Field(description="The target word")
    phonemes: list[str] = Field(
        default_factory=list,
        description="Phoneme sequence (e.g., ['/k/', '/a/', '/t/'])",
    )
    graphemes: list[str] = Field(
        default_factory=list,
        description="Grapheme sequence (e.g., ['c', 'a', 't'])",
    )
    syllable_breaks: list[int] = Field(
        default_factory=list,
        description="Indices where syllable breaks occur",
    )
    syllable_types: list[str] = Field(
        default_factory=list,
        description="Syllable type for each syllable (closed, open, VCe, etc.)",
    )

    model_config = {"extra": "allow"}


# ── Competency Lookup ───────────────────────────────────────────────────────


class CompetencyRequest(BaseModel):
    """Request for GET /api/v1/standards/competency."""

    skill: str = Field(
        min_length=1,
        description="Skill to lookup (e.g., 'consonant_blends', 'silent_e')",
    )
    state: str = Field(
        default="GA",
        description="State abbreviation (GA, CCSS, TX, FL, NY)",
    )


class StandardMatch(BaseModel):
    """A matched competency standard from GET /api/v1/standards/competency."""

    case_guid: str = Field(
        description="CASE framework GUID (e.g., 'https://case.example/items/abc-123')",
    )
    state_code: str = Field(description="State standard code (e.g., 'ELAGSE1RF3')")
    grade: str = Field(description="Grade level (K-5)")
    description: str = Field(description="Full standard description")
    strand: str | None = Field(
        default=None,
        description="Standard strand (e.g., 'Reading Foundational')",
    )

    model_config = {"extra": "allow"}
