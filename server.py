#!/usr/bin/env python3
"""Science of Reading MCP Server — Production-Grade API Bridge.

A Model Context Protocol server bridging LLMs to the Science of Reading API
at sor.edtechlabs.dev. Provides tools for phonics scope queries, decodability
verification, orthographic mapping, and competency standards lookup.

Protocol: MCP (JSON-RPC 2.0 over stdio)
Transport: stdio (subprocess-based, secure by default — no network exposure)
API Client: async httpx with retry, caching, and exponential backoff

Architecture:
  src/config.py      — Pydantic BaseSettings (env-prefixed SOR_)
  src/client/        — Async httpx client with retry/cache/backoff
  src/schemas/       — Pydantic v2 models for API request/response
  src/tools/         — MCP tools bridging to API endpoints
  src/prompts/       — MCP prompt primitives
  src/resources/     — MCP resource primitives (frameworks, word lists)
  src/errors.py      — Structured MCP error codes

Four API tools:
  get_phonics_scope      — Phonics scope and sequence (cached)
  verify_decodable_text  — Decodability verification with anti-cueing
  map_orthography        — Phoneme-grapheme syllable mapping
  lookup_competency      — CASE/state standards competency lookup

Two MCP prompts:
  generate_aligned_decodable — LLM-instructed decodable passage generator
  explicit_phonics_routine   — I Do/We Do/You Do explicit phonics script

MCP resources:
  frameworks — Scarborough's Rope, Simple View, Syllable Rules
  word_lists — Heart words, Dolch, Fry by grade

Usage:
  python server.py              # stdio transport (production)
  python server.py --http 8080  # HTTP/SSE transport (dev)
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

# Ensure the package root is on sys.path
PKG_ROOT = Path(__file__).resolve().parent
if str(PKG_ROOT) not in sys.path:
    sys.path.insert(0, str(PKG_ROOT))

from mcp.server.fastmcp import FastMCP

from src.config import Settings
from src.client.sor_client import SoRClient

# ── Load settings ───────────────────────────────────────────────────────
settings = Settings()

# ── Create FastMCP server ───────────────────────────────────────────────
mcp = FastMCP(
    name="Science of Reading",
    instructions=(
        "The Science of Reading MCP server provides evidence-based literacy analysis "
        "tools grounded in reading research. It bridges to the sor.edtechlabs.dev API "
        "for phonics scope queries, decodability verification with anti-cueing guardrails, "
        "orthographic mapping (phoneme-grapheme-syllable), and CASE/state standards "
        "competency lookup.\n\n"
        "Theoretical frameworks: Simple View of Reading, Scarborough's Reading Rope, "
        "Five Pillars of Reading (Phonemic Awareness, Phonics, Fluency, Vocabulary, "
        "Comprehension).\n\n"
        "All tools use async httpx with retry, caching, and exponential backoff "
        "against the upstream API."
    ),
    website_url="https://github.com/kosburn0408/sor-mcp-server",
)

# ── Create API client (shared across tools) ─────────────────────────────
_client: SoRClient | None = None


def get_client() -> SoRClient:
    """Get or create the shared SoRClient instance."""
    global _client
    if _client is None:
        _client = SoRClient(settings)
    return _client


# ── Tool Registration ───────────────────────────────────────────────────


@mcp.tool(
    name="get_phonics_scope",
    description=(
        "Fetch the phonics scope and sequence for a given grade and unit from "
        "sor.edtechlabs.dev. Returns target phonemes, taught graphemes, heart words, "
        "and unit objectives. Results are cached for 5 minutes.\n\n"
        "Parameters: grade_level (K-5), unit (default '1')."
    ),
)
async def get_phonics_scope_tool(
    grade_level: str,
    unit: str = "1",
) -> dict[str, Any]:
    """Fetch phonics scope from the API."""
    from src.tools.phonics import get_phonics_scope
    return await get_phonics_scope(
        grade_level=grade_level,
        unit=unit,
        client=get_client(),
        settings=settings,
    )


@mcp.tool(
    name="verify_decodable_text",
    description=(
        "Verify text decodability against a phonics scope with anti-cueing guardrails. "
        "Checks every word against the cumulative phonics scope, identifies heart words, "
        "flags off-scope patterns, detects 3-cueing/MSV strategies, and suggests "
        "decodable substitutions. Returns structured error codes.\n\n"
        "Parameters: text (passage), grade_level (K-5), unit (default '1')."
    ),
)
async def verify_decodable_text_tool(
    text: str,
    grade_level: str,
    unit: str = "1",
) -> dict[str, Any]:
    """Verify text decodability via the API."""
    from src.tools.decodability import verify_decodable_text
    return await verify_decodable_text(
        text=text,
        grade_level=grade_level,
        unit=unit,
        client=get_client(),
        settings=settings,
    )


@mcp.tool(
    name="map_orthography",
    description=(
        "Map words to their orthographic structure: phoneme sequence, grapheme "
        "sequence, syllable breaks, and syllable types (closed, open, VCe, "
        "r-controlled, vowel team, C+le). Based on structured literacy and "
        "Orton-Gillingham syllable division rules.\n\n"
        "Parameters: words (list of up to 50 words)."
    ),
)
async def map_orthography_tool(
    words: list[str],
) -> dict[str, Any]:
    """Map words to orthographic structure via the API."""
    from src.tools.orthography import map_orthography
    return await map_orthography(
        words=words,
        client=get_client(),
        settings=settings,
    )


@mcp.tool(
    name="lookup_competency",
    description=(
        "Look up CASE framework and state academic standards for a phonics skill. "
        "Returns CASE GUIDs, state standard codes, grade levels, and full descriptions. "
        "Results are cached for 5 minutes.\n\n"
        "Parameters: skill (e.g., 'consonant_blends', 'silent_e', 'digraphs'), "
        "state (GA, CCSS, TX, FL, NY; default 'GA')."
    ),
)
async def lookup_competency_tool(
    skill: str,
    state: str = "GA",
) -> dict[str, Any]:
    """Look up competency standards via the API."""
    from src.tools.standards import lookup_competency
    return await lookup_competency(
        skill=skill,
        state=state,
        client=get_client(),
        settings=settings,
    )


# ── Prompt Registration ─────────────────────────────────────────────────


@mcp.prompt(
    name="generate_aligned_decodable",
    description=(
        "Generate a Science of Reading-aligned decodable passage. Instructs the LLM "
        "to: (1) fetch the phonics scope, (2) draft a 4-6 sentence story using only "
        "taught graphemes and heart words, (3) verify decodability, (4) self-correct "
        "off-scope words, (5) return the final passage with decodability score."
    ),
)
async def generate_aligned_decodable_prompt(
    grade: str,
    unit: str,
    topic: str = "reading",
) -> str:
    """Generate a decodable passage prompt."""
    from src.prompts.decodable import generate_aligned_decodable
    return await generate_aligned_decodable(
        grade=grade,
        unit=unit,
        topic=topic,
    )


@mcp.prompt(
    name="explicit_phonics_routine",
    description=(
        "Generate an explicit phonics routine with I Do/We Do/You Do script and "
        "multisensory cues. Aligned to National Reading Panel recommendations for "
        "systematic, explicit phonics instruction (effect size 0.41)."
    ),
)
async def explicit_phonics_routine_prompt(
    target_phoneme: str,
    grade: str = "1",
    multisensory: str = "finger tapping",
) -> str:
    """Generate an explicit phonics routine prompt."""
    from src.prompts.phonics import explicit_phonics_routine
    return await explicit_phonics_routine(
        target_phoneme=target_phoneme,
        grade=grade,
        multisensory=multisensory,
    )


# ── Resource Registration ───────────────────────────────────────────────


@mcp.resource("sor://frameworks")
def get_frameworks_resource() -> str:
    """Return SoR theoretical frameworks (Scarborough's Rope, Simple View, etc.)."""
    from src.resources.frameworks import list_frameworks_resource
    import json
    return json.dumps(list_frameworks_resource(), indent=2)


@mcp.resource("sor://frameworks/syllable-rules")
def get_syllable_rules_resource() -> str:
    """Return syllable division rules (VC/CV, V/CV, VC/V, V/V, C+le)."""
    from src.resources.frameworks import SYLLABLE_DIVISION_RULES, DIVISION_PROCEDURE_RULES
    import json
    return json.dumps({
        "syllable_types": SYLLABLE_DIVISION_RULES,
        "division_rules": DIVISION_PROCEDURE_RULES,
    }, indent=2)


@mcp.resource("sor://word-lists")
def get_word_lists_resource() -> str:
    """Return heart words, Dolch, Fry, and high-frequency word lists."""
    from src.resources.word_lists import list_word_lists
    import json
    return json.dumps(list_word_lists(), indent=2)


# ── Main ───────────────────────────────────────────────────────────────────


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Science of Reading MCP Server",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""Examples:
  python server.py              # stdio transport (production)
  python server.py --http 8080  # HTTP/SSE transport (dev)
        """,
    )
    parser.add_argument("--http", type=int, metavar="PORT", help="Run with HTTP/SSE transport")
    return parser.parse_args()


def main() -> None:
    """Entry point."""
    args = parse_args()

    if args.http:
        global mcp
        mcp = FastMCP(
            name="Science of Reading",
            host="0.0.0.0",
            port=args.http,
            instructions=(
                "Evidence-based literacy analysis tools bridging to sor.edtechlabs.dev API. "
                "Tools: get_phonics_scope, verify_decodable_text, map_orthography, "
                "lookup_competency. Prompts: generate_aligned_decodable, "
                "explicit_phonics_routine."
            ),
        )
        # Re-register tools on the new instance
        _register_all(mcp)
        mcp.run(transport="sse")
    else:
        mcp.run(transport="stdio")


def _register_all(server: FastMCP) -> None:
    """Re-register all tools/prompts/resources on a given server instance."""
    server.tool(name="get_phonics_scope")(get_phonics_scope_tool)
    server.tool(name="verify_decodable_text")(verify_decodable_text_tool)
    server.tool(name="map_orthography")(map_orthography_tool)
    server.tool(name="lookup_competency")(lookup_competency_tool)
    server.prompt(name="generate_aligned_decodable")(generate_aligned_decodable_prompt)
    server.prompt(name="explicit_phonics_routine")(explicit_phonics_routine_prompt)
    server.resource("sor://frameworks")(get_frameworks_resource)
    server.resource("sor://frameworks/syllable-rules")(get_syllable_rules_resource)
    server.resource("sor://word-lists")(get_word_lists_resource)


if __name__ == "__main__":
    main()
