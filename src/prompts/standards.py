"""Standards Satchel CASE® Academic Alignment Prompt Builder.

Generates explicit state standards alignment plans integrated with
Common Good Learning Tools' Standards Satchel (Rosetta) CASE Network.
"""
from __future__ import annotations

STANDARDS_ALIGNMENT_PROMPT = """You are a District Literacy Specialist and CASE Interoperability Lead.
Generate a Standards-Aligned Lesson Integration Plan grounded in state academic frameworks.

Learning Goal / Skill: {skill}
State Framework: {state}
Grade Level: {grade}

Requirements:
1. **Target Standard Match**: Identify the exact state standard code (e.g. GSE ELAGSE1RF3, TEKS 110.3.b.2, B.E.S.T. ELA.1.F.1.3).
2. **Standards Satchel Deep-Link**: Reference the interactive portal link at `https://rosetta.commongoodlt.com/#/search?q={{code}}`.
3. **CASE v1.1 REST API Endpoint**: Reference the machine-readable endpoint at `https://rosetta.commongoodlt.com/ims/case/v1p1/CFItems/{{code}}`.
4. **Learning Objective Alignment**: Provide a clear SWBAT ("Students Will Be Able To...") statement aligned to the standard.
5. **Formative Assessment Check**: Provide a 1-minute exit ticket or observation check to measure mastery.
"""


def build_standards_prompt(skill: str, state: str = "GA", grade: str = "1st") -> str:
    """Build formatted prompt string for state standards alignment."""
    return STANDARDS_ALIGNMENT_PROMPT.format(skill=skill, state=state, grade=grade)
