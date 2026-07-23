"""Pydantic models for Science of Reading MCP server.

Structured output schemas for instructional remediation, decodable resources,
and diagnostic-to-remediation pipeline.
"""
from __future__ import annotations

from pydantic import BaseModel, Field


# ── Remediation Models ──────────────────────────────────────────────────────


class MicroPD(BaseModel):
    """Two-sentence explainer of the orthographic/phonological principle."""
    principle: str = Field(description="Principle name, e.g. 'Silent-e Rule'")
    explanation: str = Field(description="Two sentences in plain teacher language")
    research_basis: str = Field(description="One-line citation, e.g. 'NRP Phonics (d=0.41)'")


class TeacherScript(BaseModel):
    """Explicit I Do / We Do / You Do script."""
    i_do: str = Field(description="Teacher models with think-aloud")
    we_do: str = Field(description="Teacher and student practice together")
    you_do: str = Field(description="Student practices independently")
    time_per_stage: str = Field(default="~1-2 min each")


class MultisensoryCue(BaseModel):
    """Physical/kinesthetic anchor for the skill."""
    name: str = Field(description="Technique name")
    materials: str = Field(description="Required materials (or 'none')")
    procedure: str = Field(description="Step-by-step physical routine")
    verbal_anchor: str = Field(description="What the teacher says while doing it")


class WordChain(BaseModel):
    """Sequence of 4-6 words contrasting the targeted pattern."""
    chain: list[str] = Field(description="Words where student changes one sound at a time")
    target_pattern: str = Field(description="The phonics pattern being practiced")
    non_example: str = Field(description="One word that does NOT follow the pattern")


class CorrectiveFeedback(BaseModel):
    """What to say when the student makes an error."""
    error_response: str = Field(description="Exact language for error correction")
    praise_response: str = Field(description="Exact language for success")


class RemediationCard(BaseModel):
    """Complete instructional remediation card for a deficit."""
    deficit_code: str
    skill_name: str
    grade_level: str
    micro_pd: MicroPD
    teacher_script: TeacherScript
    multisensory_cue: MultisensoryCue
    word_chain: WordChain
    corrective_feedback: CorrectiveFeedback
    connected_text: str = Field(description="One decodable sentence using the target pattern")

    def to_markdown(self) -> str:
        """Render as teacher-friendly Markdown."""
        return (
            f"## 🎯 Instructional Remediation Card: {self.skill_name}\n\n"
            f"**Deficit Code:** `{self.deficit_code}`  |  "
            f"**Grade:** {self.grade_level}\n\n"
            f"---\n\n"
            f"### 1. Pedagogy Brief (Micro-PD)\n\n"
            f"**Principle:** {self.micro_pd.principle}\n\n"
            f"{self.micro_pd.explanation}\n\n"
            f"> *Research basis: {self.micro_pd.research_basis}*\n\n"
            f"### 2. Explicit Teaching Routine (I Do / We Do / You Do)\n\n"
            f"**⏱ ~5 minutes | Small Group**\n\n"
            f"**🔵 I DO (Teacher Models):**\n{self.teacher_script.i_do}\n\n"
            f"**🟡 WE DO (Guided Practice):**\n{self.teacher_script.we_do}\n\n"
            f"**🟢 YOU DO (Independent Practice):**\n{self.teacher_script.you_do}\n\n"
            f"### 3. Word Chain & Practice\n\n"
            f"**Pattern:** _{self.word_chain.target_pattern}_\n\n"
            f'{" → ".join(self.word_chain.chain)}\n\n'
            f"**Watch for:** _{self.word_chain.non_example}_ "
            f"(this word breaks the pattern — use it to check understanding)\n\n"
            f"### 4. Corrective Feedback Cue\n\n"
            f"**Multisensory Anchor:** _{self.multisensory_cue.name}_\n\n"
            f"- **Materials:** {self.multisensory_cue.materials}\n"
            f"- **Procedure:** {self.multisensory_cue.procedure}\n"
            f'- **Say:** "{self.multisensory_cue.verbal_anchor}"\n\n'
            f'**❌ If incorrect:** "{self.corrective_feedback.error_response}"\n'
            f'**✅ If correct:** "{self.corrective_feedback.praise_response}"\n\n'
            f"**📖 Connected Text:**\n> {self.connected_text}\n"
        )


# ── Decodable Resources Models ──────────────────────────────────────────────


class DecodablePassage(BaseModel):
    """A short decodable passage constrained to mastered skills."""
    title: str
    text: str = Field(description="The decodable passage (2-4 sentences)")
    word_count: int
    target_phoneme: str
    mastered_skills_used: list[str] = Field(default_factory=list)
    high_frequency_words: list[str] = Field(default_factory=list)


class DecodableRecommendation(BaseModel):
    """A set of decodable resource recommendations."""
    student_profile: str
    passages: list[DecodablePassage] = Field(default_factory=list)
    teacher_notes: str = ""
    scope_warning: str = ""


# ── Diagnostic → Remediation Pipeline ───────────────────────────────────────


class SimpleViewResult(BaseModel):
    """Simple View of Reading evaluation result."""
    decoding_score: float = Field(ge=0.0, le=1.0)
    language_comprehension_score: float = Field(ge=0.0, le=1.0)
    reading_profile: str = Field(
        description="'typical', 'dyslexia', 'hyperlexic', or 'garden_variety'"
    )
    deficit_codes: list[str] = Field(default_factory=list)


class DiagnosticRemediationBundle(BaseModel):
    """Combined diagnostic result + remediation recommendations."""
    diagnostic: SimpleViewResult
    remediations: list[RemediationCard] = Field(default_factory=list)
    next_steps: str = ""
