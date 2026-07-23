"""Pydantic v2 models for Science of Reading MCP server.

All models use Pydantic v2 with strict validation, field descriptions,
and type annotations for production-grade reliability.
"""

from .curriculum import (
    CurriculumQuery,
    ScopeSequence,
    CurriculumResult,
)
from .decodability import (
    HeartWordEntry,
    OffScopeWord,
    WarningEntry,
)
from .standards import (
    CaseCFItem,
    CaseStandardsBundle,
    CaseAssociation,
    CaseAssociationType,
    StandardsAlignmentRequest,
    StandardsAlignmentResult,
    StateCode,
)
from .prompts import (
    PromptTemplate,
    RoutineScript,
    ExplicitPhonicsInput,
    DecodablePassageInput,
    MultisyllabicInput,
    IWeYouScript,
    DecodablePassageOutput,
    MultisyllabicRoutine,
    SyllableDivisionStep,
)

__all__ = [
    # curriculum
    "CurriculumQuery",
    "ScopeSequence",
    "CurriculumResult",
    # decodability
    "HeartWordEntry",
    "OffScopeWord",
    "WarningEntry",
    # standards
    "CaseCFItem",
    "CaseStandardsBundle",
    "CaseAssociation",
    "CaseAssociationType",
    "StandardsAlignmentRequest",
    "StandardsAlignmentResult",
    "StateCode",
    # prompts
    "PromptTemplate",
    "RoutineScript",
    "ExplicitPhonicsInput",
    "DecodablePassageInput",
    "MultisyllabicInput",
    "IWeYouScript",
    "DecodablePassageOutput",
    "MultisyllabicRoutine",
    "SyllableDivisionStep",
]
