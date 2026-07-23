"""Pydantic v2 models for MCP Prompt primitives.

Defines structured inputs/outputs for explicit phonics routines,
decodable passage building, and multisyllabic decoding routines.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, field_validator


# ── Prompt Template Models ──────────────────────────────────────────────


class PromptTemplate(BaseModel):
    """An MCP Prompt template definition."""

    name: str = Field(description="Unique prompt name")
    description: str = Field(description="What the prompt generates")
    required_arguments: list[str] = Field(
        default_factory=list,
        description="Arguments that must be provided",
    )
    optional_arguments: list[str] = Field(
        default_factory=list,
        description="Optional arguments with defaults",
    )


class RoutineScript(BaseModel):
    """Base model for a generated instructional routine."""

    title: str = Field(description="Routine title")
    target_skill: str = Field(description="Skill being taught")
    grade_level: str = Field(description="Target grade level")
    total_time: str = Field(description="Estimated total routine duration")
    framework_notes: str = Field(
        default="",
        description="SoR framework alignment notes",
    )


# ── Explicit Phonics (I Do / We Do / You Do) Models ────────────────────


class IWeYouScript(BaseModel):
    """I Do / We Do / You Do explicit instruction script."""

    i_do: str = Field(
        description="Teacher model: 'Watch me...' — explicit think-aloud modeling"
    )
    we_do: str = Field(
        description="Guided practice: 'Let's do this together...'"
    )
    you_do: str = Field(
        description="Independent practice: 'Your turn...'"
    )
    timing: str = Field(
        default="~1-2 minutes per stage",
        description="Suggested timing for each stage",
    )


class ExplicitPhonicsInput(BaseModel):
    """Input for the explicit_phonics_routine prompt."""

    skill_name: str = Field(
        min_length=1,
        description="The phonics skill to teach (e.g., 'Short Vowel /a/', 'Silent-e Pattern')",
    )
    grade_level: str = Field(
        default="1st",
        description="Target grade level",
    )
    phoneme_examples: list[str] = Field(
        default_factory=list,
        description="Example words containing the target phoneme/grapheme",
    )
    multisensory_cue: str | None = Field(
        default=None,
        description="Optional multisensory technique (e.g., 'Elkonin boxes', 'finger tapping')",
    )

    @field_validator("grade_level")
    @classmethod
    def validate_grade(cls, v: str) -> str:
        valid = {"K", "1st", "2nd", "3rd", "4th", "5th"}
        if v not in valid:
            raise ValueError(f"Grade must be one of {sorted(valid)}")
        return v

    model_config = {"extra": "forbid"}


# ── Decodable Passage Builder Models ───────────────────────────────────


class DecodablePassageInput(BaseModel):
    """Input for the decodable_passage_builder prompt."""

    target_phoneme: str = Field(
        min_length=1,
        description="The phoneme/grapheme pattern to practice (e.g., 'short_a', 'silent_e')",
    )
    mastered_patterns: list[str] = Field(
        default_factory=list,
        description="All phonics patterns the student has mastered (cumulative)",
    )
    grade_level: str = Field(
        default="1st",
        description="Target grade level",
    )
    topic: str | None = Field(
        default=None,
        description="Optional thematic topic (e.g., 'animals', 'space')",
    )
    sentence_count: int = Field(
        default=3,
        ge=2,
        le=8,
        description="Number of sentences in the passage (2-8)",
    )
    include_heart_words: list[str] = Field(
        default_factory=list,
        description="Heart words to explicitly include and mark",
    )

    @field_validator("grade_level")
    @classmethod
    def validate_grade(cls, v: str) -> str:
        valid = {"K", "1st", "2nd", "3rd", "4th", "5th"}
        if v not in valid:
            raise ValueError(f"Grade must be one of {sorted(valid)}")
        return v

    model_config = {"extra": "forbid"}


class DecodablePassageOutput(BaseModel):
    """Generated decodable passage with metadata."""

    title: str = Field(description="Passage title")
    passage: str = Field(description="The decodable text passage")
    word_count: int = Field(description="Total word count")
    decodability_pct: float = Field(
        ge=0.0, le=100.0,
        description="Percentage of fully decodable words",
    )
    patterns_used: list[str] = Field(
        default_factory=list,
        description="Phonics patterns used in the passage",
    )
    heart_words_marked: list[dict[str, str]] = Field(
        default_factory=list,
        description="Heart words with irregular parts noted",
    )
    off_scope_words: list[str] = Field(
        default_factory=list,
        description="Any words containing untaught patterns (should be empty)",
    )
    comprehension_question: str = Field(
        default="",
        description="One literal comprehension question about the passage",
    )
    teacher_notes: str = Field(
        default="",
        description="Pre-reading and during-reading guidance",
    )


# ── Multisyllabic Decoding Models ──────────────────────────────────────


class MultisyllabicInput(BaseModel):
    """Input for the multisyllabic_decoding_routine prompt."""

    word: str = Field(
        min_length=2,
        max_length=30,
        description="The multisyllabic word to decode",
    )
    syllable_type_focus: str = Field(
        default="mixed",
        description="Syllable type to focus on (closed, open, VCe, r_controlled, vowel_team, c_le, mixed)",
    )
    grade_level: str = Field(
        default="3rd",
        description="Target grade level (typically 2nd+)",
    )
    include_orthographic_mapping: bool = Field(
        default=True,
        description="Include orthographic mapping steps",
    )

    @field_validator("grade_level")
    @classmethod
    def validate_grade(cls, v: str) -> str:
        valid = {"K", "1st", "2nd", "3rd", "4th", "5th"}
        if v not in valid:
            raise ValueError(f"Grade must be one of {sorted(valid)}")
        return v

    model_config = {"extra": "forbid"}


class SyllableDivisionStep(BaseModel):
    """A single step in syllable division."""

    step_number: int = Field(description="Step sequence number")
    action: str = Field(description="What the teacher/student does")
    visual: str = Field(description="Visual representation of the word at this step")
    teacher_language: str = Field(description="What the teacher says")


class MultisyllabicRoutine(BaseModel):
    """Complete multisyllabic decoding routine."""

    word: str = Field(description="Target multisyllabic word")
    syllable_count: int = Field(description="Number of syllables")
    syllable_breakdown: list[str] = Field(
        default_factory=list,
        description="Word broken into syllables (e.g., ['fan', 'tas', 'tic'])",
    )
    syllable_types: list[str] = Field(
        default_factory=list,
        description="Syllable type for each part",
    )
    division_rule: str = Field(
        description="Applied division rule (e.g., 'VC/CV', 'V/CV')",
    )
    division_steps: list[SyllableDivisionStep] = Field(
        default_factory=list,
        description="Step-by-step division process",
    )
    orthographic_mapping: str | None = Field(
        default=None,
        description="Orthographic mapping visual if requested",
    )
    word_meaning: str = Field(
        description="Student-friendly definition",
    )
    example_sentence: str = Field(
        description="Sentence using the word in context",
    )
    connected_words: list[str] = Field(
        default_factory=list,
        description="Related words with the same pattern",
    )
