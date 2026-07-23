"""Pydantic v2 models for curriculum routing and scope sequence.

Defines the validation schemas for query_sor_curriculum meta-tool
inputs and curriculum lookup results.
"""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field


class Strand(str, Enum):
    """Five pillars + morphology strand from NRP and current SoR research."""

    PHONOLOGY = "phonology"
    MORPHOLOGY = "morphology"
    VOCABULARY = "vocabulary"
    FLUENCY = "fluency"
    COMPREHENSION = "comprehension"


class GradeLevel(str, Enum):
    """Supported grade levels K-5."""

    K = "K"
    G1 = "1"
    G2 = "2"
    G3 = "3"
    G4 = "4"
    G5 = "5"


class SyllableType(str, Enum):
    """Six syllable types (Orton-Gillingham / Wilson)."""

    CLOSED = "closed"
    OPEN = "open"
    VCE = "VCe"
    R_CONTROLLED = "r_controlled"
    VOWEL_TEAM = "vowel_team"
    C_LE = "c_le"


class CurriculumQuery(BaseModel):
    """Input for the query_sor_curriculum meta-tool.

    All fields except grade_level are optional — the router resolves
    the best tool based on which parameters are populated.
    """

    grade_level: GradeLevel = Field(
        description="Target grade level (K-5)",
    )
    strand: Strand | None = Field(
        default=None,
        description="Literacy strand to query (phonology, morphology, vocabulary, fluency, comprehension)",
    )
    target_phoneme: str | None = Field(
        default=None,
        description="Specific phoneme to look up (e.g., /a/, /sh/, /ā/)",
    )
    syllable_type: SyllableType | None = Field(
        default=None,
        description="Syllable type for explicit instruction (closed, open, VCe, r_controlled, vowel_team, c_le)",
    )
    standard_state: str | None = Field(
        default=None,
        max_length=20,
        description="State standards code for alignment (CCSS, TEXAS, FLORIDA, NY, GEORGIA)",
    )

    model_config = {"extra": "forbid"}


class ScopeSequence(BaseModel):
    """A scope and sequence entry for a grade level."""

    grade: str = Field(description="Grade level (K-5)")
    strand: str = Field(description="Literacy strand")
    concepts: list[str] = Field(
        default_factory=list,
        description="Concepts taught at this grade/strand level",
    )
    phonemes: list[str] = Field(
        default_factory=list,
        description="Phoneme-grapheme correspondences taught",
    )
    syllable_types: list[str] = Field(
        default_factory=list,
        description="Syllable types addressed",
    )
    prerequisites: list[str] = Field(
        default_factory=list,
        description="Skills required before this level",
    )
    next_steps: list[str] = Field(
        default_factory=list,
        description="Next skills in the progression",
    )
    standards: list[str] = Field(
        default_factory=list,
        description="Associated state/national standards codes",
    )


class CurriculumResult(BaseModel):
    """Compact result from query_sor_curriculum meta-tool.

    Designed to keep system prompt context lean — no verbose descriptions.
    """

    strand: str = Field(description="Matched literacy strand")
    grade: str = Field(description="Target grade level")
    concepts: list[str] = Field(
        default_factory=list,
        description="Core concepts at this level",
    )
    prerequisites: list[str] = Field(
        default_factory=list,
        description="Skills that must precede this level",
    )
    next_steps: list[str] = Field(
        default_factory=list,
        description="Recommended next instructional steps",
    )
    matched_standards: list[str] = Field(
        default_factory=list,
        description="Matching state/national standard codes",
    )
    remediation_code: str | None = Field(
        default=None,
        description="Suggested remediation deficit code if applicable",
    )
    tool_routed_to: str = Field(
        description="Internal tool that handled the query (for diagnostics)",
    )
