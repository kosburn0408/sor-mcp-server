"""Pydantic v2 models for decodability verification with anti-cueing guardrails.

Defines schemas for verify_decodable_text: input validation, word-level
classification, anti-cueing detection, and structured output.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, field_validator


class DecodabilityRequest(BaseModel):
    """Input for the verify_decodable_text tool."""

    text: str = Field(
        min_length=1,
        max_length=5000,
        description="The text passage to verify for decodability",
    )
    target_skill: str = Field(
        min_length=1,
        description="Target phonics skill being practiced (e.g., 'cvc_short_a', 'cvce_silent_e')",
    )
    scope_sequence: list[str] = Field(
        default_factory=list,
        description="List of mastered phonics patterns (cumulative scope and sequence)",
    )
    grade_level: str = Field(
        default="1",
        description="Grade level (K, 1, 2, 3, 4, 5)",
    )
    enable_anti_cueing: bool = Field(
        default=True,
        description="Enable anti-cueing (MSV/3-cueing) detection guardrails",
    )

    @field_validator("grade_level")
    @classmethod
    def validate_grade(cls, v: str) -> str:
        valid = {"K", "1", "2", "3", "4", "5"}
        if v not in valid:
            raise ValueError(f"Grade must be one of {sorted(valid)}, got '{v}'")
        return v

    model_config = {"extra": "forbid"}


class HeartWordEntry(BaseModel):
    """A word that contains temporarily irregular grapheme-phoneme correspondences."""

    word: str = Field(description="The heart word")
    regular_part: str = Field(
        description="The decodable part of the word (sound it out)"
    )
    heart_part: str = Field(
        description="The irregular part to learn 'by heart'"
    )
    heart_letters: str = Field(
        description="Specific letters that are irregular"
    )
    explanation: str = Field(
        description="Why this part is irregular at this stage"
    )


class OffScopeWord(BaseModel):
    """A word that contains phoneme patterns beyond current instruction."""

    word: str = Field(description="The off-scope word")
    untaught_pattern: str = Field(
        description="The specific pattern not yet taught"
    )
    suggestion: str = Field(
        description="Suggested replacement or pre-teaching strategy"
    )


class WarningEntry(BaseModel):
    """A warning or guardrail violation."""

    severity: Literal["info", "warning", "error"] = Field(
        description="Severity level"
    )
    code: str = Field(description="Error/warning code (e.g., ERR_CUEING_DETECTED)")
    message: str = Field(description="Human-readable warning")
    location: str | None = Field(
        default=None,
        description="Position or context in text where the issue was found",
    )


class DecodabilityResult(BaseModel):
    """Complete result from verify_decodable_text."""

    total_words: int = Field(description="Total word count in the passage")
    decodable_count: int = Field(description="Number of fully decodable words")
    decodable_pct: float = Field(
        ge=0.0, le=100.0,
        description="Percentage of words that are fully decodable",
    )
    target_skill_words: list[str] = Field(
        default_factory=list,
        description="Words that specifically practice the target skill",
    )
    heart_words: list[HeartWordEntry] = Field(
        default_factory=list,
        description="Heart words identified in the text",
    )
    off_scope_words: list[OffScopeWord] = Field(
        default_factory=list,
        description="Words with untaught patterns",
    )
    warnings: list[WarningEntry] = Field(
        default_factory=list,
        description="Anti-cueing and quality warnings",
    )
    recommendation: str = Field(
        description="Instructional recommendation based on results",
    )
    instructional_level: Literal["independent", "instructional", "frustration"] = Field(
        description="Independent (>95%), Instructional (90-95%), or Frustration (<90%) level",
    )
