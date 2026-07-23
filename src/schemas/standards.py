"""Pydantic v2 models for CASE/JSON-LD standards alignment.

Implements 1EdTech CASE CFItem model with JSON-LD context for
interoperable academic standards metadata.
"""

from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field, HttpUrl


class StateCode(str, Enum):
    """Supported state/national standard code sets."""

    CCSS = "CCSS"
    TEXAS = "TEXAS"
    FLORIDA = "FLORIDA"
    NY = "NY"
    GEORGIA = "GEORGIA"


class CaseAssociationType(str, Enum):
    """CASE framework association types (1EdTech CFAssociation)."""

    IS_CHILD_OF = "isChildOf"
    IS_RELATED_TO = "isRelatedTo"
    EXACT_MATCH_OF = "exactMatchOf"
    PRECEDES = "precedes"
    IS_PEER_OF = "isPeerOf"


class CaseCFItem(BaseModel):
    """A single CASE Competency Framework Item (CFItem).

    Models a standard statement in the CASE JSON-LD format compatible
    with 1EdTech CASE Network v1.0.
    """

    identifier: str = Field(
        description="CASE GUID for this CFItem (e.g., 'https://case.example/items/abc-123')",
    )
    uri: str = Field(
        description="Canonical URI for this standard item",
    )
    full_statement: str = Field(
        description="Complete standard statement text",
    )
    human_coding_scheme: str = Field(
        description="Human-readable code (e.g., 'RF.K.2', 'ELAGSE1RF3')",
    )
    grade: str = Field(
        description="Target grade level (K-5)",
    )
    subject: str = Field(
        default="ELA",
        description="Subject area",
    )
    pillar: str | None = Field(
        default=None,
        description="NRP Five Pillars mapping for this standard",
    )
    strand: str | None = Field(
        default=None,
        description="Standard strand (e.g., 'Reading Foundational', 'Language')",
    )
    list_enumeration: str | None = Field(
        default=None,
        description="Enumeration label in standard set (e.g., 'Standard 2')",
    )
    notes: str | None = Field(
        default=None,
        description="Optional implementation or differentiation notes",
    )

    model_config = {"extra": "allow"}


class CaseAssociation(BaseModel):
    """A relationship between two CASE CFItems."""

    origin_node_uri: str = Field(description="Source CFItem URI")
    destination_node_uri: str = Field(
        description="Target CFItem URI"
    )
    association_type: CaseAssociationType = Field(
        description="Type of relationship between the two items"
    )


class CaseStandardsBundle(BaseModel):
    """A complete CASE standards bundle with JSON-LD context."""

    json_ld_context: str = Field(
        default="https://purl.imsglobal.org/spec/case/v1p0/context/imscasev1p0_context_v1p0.jsonld",
        description="JSON-LD context URI for CASE v1.0",
    )
    cf_items: list[CaseCFItem] = Field(
        default_factory=list,
        description="Competency Framework Items in this bundle",
    )
    cf_associations: list[CaseAssociation] = Field(
        default_factory=list,
        description="Relationships between CFItems",
    )
    title: str = Field(
        default="Science of Reading Standards Alignment",
        description="Bundle title",
    )
    description: str = Field(
        default="CASE standards aligned to Science of Reading frameworks",
        description="Bundle description",
    )
    creator: str = Field(
        default="SoR MCP Server",
        description="Bundle creator",
    )
    license_url: str = Field(
        default="https://creativecommons.org/licenses/by/4.0/",
        description="License for the standards data",
    )


class StandardsAlignmentRequest(BaseModel):
    """Input for CASE standards alignment."""

    text_description: str = Field(
        min_length=3,
        description="Natural language description of text or skill",
    )
    state: StateCode = Field(
        default=StateCode.CCSS,
        description="Target state standards set",
    )
    grade: str | None = Field(
        default=None,
        description="Optional grade-level filter (K-5)",
    )
    output_format: str = Field(
        default="case_jsonld",
        description="Output format: 'case_jsonld' or 'summary'",
    )

    model_config = {"extra": "forbid"}


class StandardsAlignmentResult(BaseModel):
    """Result of standards alignment lookup."""

    request_grade: str | None = Field(description="Requested grade filter")
    request_state: str = Field(description="State standards set used")
    total_matches: int = Field(description="Number of matching standards")
    matches: list[dict[str, Any]] = Field(
        default_factory=list,
        description="List of matching standard records",
    )
    case_bundle: CaseStandardsBundle | None = Field(
        default=None,
        description="CASE JSON-LD bundle (when output_format='case_jsonld')",
    )
    framework_note: str = Field(
        default="",
        description="SoR framework context",
    )
