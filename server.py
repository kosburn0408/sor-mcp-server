#!/usr/bin/env python3
"""Science of Reading MCP Server — Production-Grade Hybrid API & Analytical Engine.

A Model Context Protocol server bridging LLMs to evidence-based literacy analysis tools,
grounded in the Science of Reading research (Simple View, Scarborough's Rope, NRP Five Pillars).
Supports both sor.edtechlabs.dev remote API and embedded DuckDB OLAP database fallback.

Protocol: MCP (JSON-RPC 2.0 over stdio or SSE)
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path
from typing import Any

PKG_ROOT = Path(__file__).resolve().parent
if str(PKG_ROOT) not in sys.path:
    sys.path.insert(0, str(PKG_ROOT))

from mcp.server.fastmcp import FastMCP

from src.config import Settings
from src.client.sor_client import SoRClient
from db.database import ensure_database

settings = Settings()

mcp = FastMCP(
    name="Science of Reading",
    instructions=(
        "The Science of Reading MCP server provides evidence-based literacy analysis "
        "tools grounded in reading research (Simple View of Reading, Scarborough's Reading Rope, "
        "Five Pillars). Provides tools for decodability checking, Lexile estimation, vocabulary "
        "tier classification, research evidence lookup, standards alignment, diagnostics, "
        "remediation, orthographic mapping, and PII anonymization."
    ),
    website_url="https://github.com/kosburn0408/sor-mcp-server",
)

_client: SoRClient | None = None


def get_client() -> SoRClient:
    """Get shared SoRClient instance."""
    global _client
    if _client is None:
        _client = SoRClient(settings)
    return _client


# ── Tool Definitions ───────────────────────────────────────────────────


@mcp.tool(
    name="get_phonics_scope",
    description="Fetch phonics scope & sequence for a given grade and unit. Returns target phonemes, taught graphemes, and heart words.",
)
async def get_phonics_scope_tool(grade_level: str, unit: str = "1") -> dict[str, Any]:
    from src.tools.phonics import get_phonics_scope
    return await get_phonics_scope(grade_level=grade_level, unit=unit, client=get_client(), settings=settings)


@mcp.tool(
    name="verify_decodable_text",
    description=(
        "Verify text decodability against a cumulative grapheme-phoneme scope. Pass unit (1-10) to "
        "restrict to patterns taught so far; omit it to use the whole grade. Returns per-word "
        "analysis, taught heart words, off-scope words, cueing risk flags and decodable substitutions."
    ),
)
async def verify_decodable_text_tool(text: str, grade_level: str, unit: str | None = None) -> dict[str, Any]:
    from src.tools.decodability import verify_decodable_text
    return await verify_decodable_text(text=text, grade_level=grade_level, unit=unit, client=get_client(), settings=settings)


@mcp.tool(
    name="map_orthography",
    description="Map words to their orthographic structure: phonemes, graphemes, syllable breaks, and syllable types.",
)
async def map_orthography_tool(words: list[str]) -> dict[str, Any]:
    from src.tools.orthography import map_orthography
    return await map_orthography(words=words, client=get_client(), settings=settings)


@mcp.tool(
    name="lookup_competency",
    description="Look up CASE framework and state academic standards for a phonics skill.",
)
async def lookup_competency_tool(skill: str, state: str = "GA") -> dict[str, Any]:
    from src.tools.standards import lookup_competency
    return await lookup_competency(skill=skill, state=state, client=get_client(), settings=settings)


@mcp.tool(
    name="analyze_lexile",
    description="Estimate Lexile score, word count, sentence complexity, and grade level for a text.",
)
def analyze_lexile_tool(text: str) -> dict[str, Any]:
    from src.tools.diagnostics import analyze_lexile
    return analyze_lexile(text=text)


@mcp.tool(
    name="classify_vocabulary",
    description="Classify text into Beck's Tier 1/2/3 vocabulary with instructional recommendations.",
)
def classify_vocabulary_tool(text: str, domain: str | None = None) -> dict[str, Any]:
    from src.tools.vocabulary import classify_vocabulary
    return classify_vocabulary(text=text, domain=domain)


@mcp.tool(
    name="match_word",
    description="Single-word lookup in the vocabulary corpus (tier, frequency, decodability, grade level).",
)
def match_word_tool(word: str, grade: str | None = None) -> dict[str, Any]:
    from src.tools.vocabulary import match_word
    return match_word(word=word, grade=grade)


@mcp.tool(
    name="search_evidence",
    description="Query WWC/BEE/NRP research database by topic with effect sizes, findings, and publication links.",
)
def search_evidence_tool(topic: str) -> dict[str, Any]:
    from src.tools.evidence import search_evidence
    return search_evidence(topic=topic)


@mcp.tool(
    name="list_frameworks",
    description="Enumerate all theoretical frameworks (Simple View, Scarborough's Rope, Five Pillars) with descriptions.",
)
def list_frameworks_tool() -> dict[str, Any]:
    from src.tools.evidence import list_frameworks
    return list_frameworks()


@mcp.tool(
    name="list_assessments",
    description="Browse evidence-based assessment tools (screener, diagnostic, progress monitoring, outcome).",
)
def list_assessments_tool(tool_type: str | None = None) -> dict[str, Any]:
    from src.tools.evidence import list_assessments
    return list_assessments(tool_type=tool_type)


@mcp.tool(
    name="align_standards",
    description="Map text/skills description to academic standards across 50 state frameworks with Standards Satchel (CASE®) deep links.",
)
def align_standards_tool(description: str, state: str = "GA", grade: str | None = None) -> dict[str, Any]:
    from src.tools.evidence import align_standards
    return align_standards(description=description, state=state, grade=grade)


@mcp.tool(
    name="evaluate_simple_view",
    description=(
        "Screening-level profile based on the Simple View of Reading (Decoding x Language "
        "Comprehension = Reading Comprehension). Scores are proportions (0-1) of a grade-level "
        "benchmark, not norms. Not a diagnosis; confirm with a diagnostic phonics survey."
    ),
)
def evaluate_simple_view_tool(
    decoding_score: float,
    language_comp_score: float,
    student_grade: str = "1",
    threshold: float = 0.60,
) -> dict[str, Any]:
    from src.tools.diagnostics import evaluate_simple_view
    return evaluate_simple_view(
        decoding=decoding_score,
        language_comprehension=language_comp_score,
        grade=student_grade,
        threshold=threshold,
    )


@mcp.tool(
    name="get_instructional_remediation",
    description="Get evidence-based instructional remediation routine based on student deficit profile.",
)
def get_instructional_remediation_tool(deficit_code: str, grade_level: str = "1") -> dict[str, Any]:
    from src.tools.remediation import (
        get_instructional_remediation,
        list_available_remediations,
    )
    try:
        card = get_instructional_remediation(deficit_code=deficit_code, grade_level=grade_level)
    except ValueError as exc:
        return {
            "error_code": "ERR_UNKNOWN_DEFICIT_CODE",
            "error": str(exc),
            "available": list_available_remediations()["remediations"],
        }
    return {"status": "ok", "card": card.model_dump(), "markdown": card.to_markdown()}


@mcp.tool(
    name="sanitize_pii",
    description="Student PII anonymizer designed to support FERPA obligations. Strips known name, ID, email, phone and address fields before LLM processing. It does not scan free-text values for names."
)
def sanitize_pii_tool(data: dict[str, Any]) -> dict[str, Any]:
    from src.tools.privacy import sanitize_pii
    return sanitize_pii(data)


# ── Prompts ────────────────────────────────────────────────────────────


@mcp.prompt(
    name="generate_aligned_decodable",
    description="Generate a Science of Reading-aligned decodable passage.",
)
async def generate_aligned_decodable_prompt(grade: str, unit: str, topic: str = "reading") -> str:
    from src.prompts.decodable import generate_aligned_decodable
    return await generate_aligned_decodable(grade=grade, unit=unit, topic=topic)


@mcp.prompt(
    name="explicit_phonics_routine",
    description="Generate an explicit phonics routine with I Do/We Do/You Do script and multisensory cues.",
)
async def explicit_phonics_routine_prompt(
    target_phoneme: str,
    grade: str = "1",
    multisensory: str = "finger tapping",
) -> str:
    from src.prompts.phonics import explicit_phonics_routine
    return await explicit_phonics_routine(target_phoneme=target_phoneme, grade=grade, multisensory=multisensory)


@mcp.prompt(
    name="vocabulary_tier_routine",
    description="Generate an explicit Tier 2 vocabulary pre-teaching routine based on Isabel Beck's 3-Tier model.",
)
def vocabulary_tier_routine_prompt(
    words: str,
    grade: str = "2nd",
    topic: str = "general reading",
) -> str:
    from src.prompts.vocabulary import build_vocabulary_routine
    return build_vocabulary_routine(words=words, grade=grade, topic=topic)


@mcp.prompt(
    name="standards_alignment_routine",
    description="Generate a lesson plan alignment plan integrated with Standards Satchel (Rosetta) CASE network deep links.",
)
def standards_alignment_routine_prompt(
    skill: str,
    state: str = "GA",
    grade: str = "1st",
) -> str:
    from src.prompts.standards import build_standards_prompt
    return build_standards_prompt(skill=skill, state=state, grade=grade)


# ── Resources ──────────────────────────────────────────────────────────


@mcp.resource("sor://frameworks")
def get_frameworks_resource() -> str:
    from src.tools.evidence import list_frameworks
    import json
    return json.dumps(list_frameworks(), indent=2)


@mcp.resource("sor://frameworks/syllable-rules")
def get_syllable_rules_resource() -> str:
    from src.resources.frameworks import SYLLABLE_DIVISION_RULES, DIVISION_PROCEDURE_RULES
    import json
    return json.dumps({
        "syllable_types": SYLLABLE_DIVISION_RULES,
        "division_rules": DIVISION_PROCEDURE_RULES,
    }, indent=2)


@mcp.resource("sor://word-lists")
def get_word_lists_resource() -> str:
    from src.resources.word_lists import list_word_lists
    import json
    return json.dumps(list_word_lists(), indent=2)


@mcp.resource("sor://assessments")
def get_assessments_resource() -> str:
    from src.tools.evidence import list_assessments
    import json
    return json.dumps(list_assessments(), indent=2)


@mcp.resource("sor://standards-satchel")
def get_standards_satchel_resource() -> str:
    import json
    return json.dumps({
        "portal_url": "https://rosetta.commongoodlt.com/",
        "provider": "Common Good Learning Tools",
        "specification": "1EdTech CASE® (Competencies and Academic Standards Exchange)",
        "supported_states": 50,
        "deep_link_pattern": "https://rosetta.commongoodlt.com/#/search?q={code}",
        "case_api_pattern": "https://rosetta.commongoodlt.com/ims/case/v1p1/CFItems/{code}",
    }, indent=2)


@mcp.resource("sor://evidence/meta-analyses")
def get_meta_analyses_resource() -> str:
    from src.tools.evidence import search_evidence
    import json
    return json.dumps(search_evidence("phonics"), indent=2)


# ── CLI & Main ─────────────────────────────────────────────────────────


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Science of Reading MCP Server",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--http", type=int, metavar="PORT", help="Run with HTTP/SSE transport")
    parser.add_argument(
        "--host",
        default="127.0.0.1",
        help="Bind address for --http (default 127.0.0.1; use 0.0.0.0 inside a container)",
    )
    parser.add_argument("--seed-only", action="store_true", help="Seed DuckDB database and exit")
    parser.add_argument("--offline", action="store_true", help="Force local DuckDB mode")
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    if args.seed_only:
        db_path, is_new = ensure_database()
        print(f"DuckDB database successfully verified/seeded at: {db_path}")
        sys.exit(0)

    if args.offline:
        os.environ["SOR_OFFLINE_MODE"] = "true"

    if args.http:
        # Reuse the fully configured server (tool descriptions, prompts, resources)
        # rather than rebuilding a second instance with fewer details.
        mcp.settings.host = args.host
        mcp.settings.port = args.http
        mcp.run(transport="sse")
    else:
        mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
