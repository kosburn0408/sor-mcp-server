#!/usr/bin/env python3
"""Science of Reading MCP Server — Production-Grade Architecture.

A Model Context Protocol server providing evidence-based literacy analysis
tools aligned to the Science of Reading research base.

Protocol: MCP (JSON-RPC 2.0 over stdio)
Transport: stdio (subprocess-based, secure by default — no network exposure)
Database: DuckDB (embedded analytical database, no separate server needed)

Architecture:
  src/core/       — Meta-tool router, structured error codes
  src/tools/      — Domain tools (diagnostics, remediation, decodability, standards, privacy)
  src/prompts/    — MCP Prompt primitives (I Do/We Do/You Do, decodable passage, multisyllabic)
  src/resources/  — MCP Resource primitives (frameworks, word lists)
  src/schemas/    — Pydantic v2 models for all I/O

Tools exposed:
  query_sor_curriculum        — Dynamic meta-tool router
  analyze_lexile              — Text complexity and Lexile scoring
  check_decodability          — Decodable text percentage by grade
  verify_decodable_text       — Anti-cueing decodability verifier (NEW)
  classify_vocabulary         — Tier 1/2/3 word classification
  search_evidence             — WWC/BEE research paper lookup
  list_frameworks             — Theoretical framework reference
  list_assessments            — Evidence-based assessment lookup
  align_standards             — CASE framework standards alignment
  align_standards_case        — CASE/JSON-LD standards (NEW)
  match_word                  — Single-word tier lookup
  evaluate_simple_view        — Simple View of Reading diagnostic
  get_instructional_remediation — Remediation card for a reading deficit
  recommend_decodable_resources — Decodable text constrained to mastered skills
  list_remediations           — List all available remediation deficit codes

Theoretical frameworks embedded:
  - Simple View of Reading (Gough & Tunmer, 1986)
  - Scarborough's Reading Rope (2001)
  - National Reading Panel Five Pillars (2000)
  - What Works Clearinghouse Foundational Skills Practice Guide (2016)
  - Beck, McKeown & Kucan Three-Tier Vocabulary (2013)

Usage:
  python server.py                          # stdio (for MCP clients)
  python server.py --seed-only              # seed database and exit
  python server.py --http 8080              # HTTP/SSE transport (dev/debug)
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path
from typing import Any

# Ensure the package root is on sys.path
PKG_ROOT = Path(__file__).resolve().parent
if str(PKG_ROOT) not in sys.path:
    sys.path.insert(0, str(PKG_ROOT))

from mcp.server.fastmcp import FastMCP

# Initialize server (stdio by default)
mcp = FastMCP(
    name="Science of Reading",
    instructions=(
        "The Science of Reading MCP server provides evidence-based literacy analysis "
        "tools grounded in reading research. It supports text complexity analysis "
        "(Lexile), decodability checking with anti-cueing guardrails, vocabulary tier "
        "classification, research evidence lookup, standards alignment (CASE/JSON-LD), "
        "and explicit phonics routine generation — all backed by DuckDB-embedded "
        "data from What Works Clearinghouse, Best Evidence Encyclopedia, and the "
        "National Reading Panel.\n\n"
        "Theoretical frameworks: Simple View of Reading, Scarborough's Reading Rope, "
        "Five Pillars of Reading (Phonemic Awareness, Phonics, Fluency, Vocabulary, "
        "Comprehension).\n\n"
        "Meta-tool: use query_sor_curriculum as the primary entry point for "
        "curriculum routing — it dispatches to the appropriate tool internally."
    ),
    website_url="https://github.com/kosburn0408/sor-mcp-server",
)


def _ensure_db() -> None:
    """Ensure the DuckDB database exists and is seeded."""
    from db.database import ensure_database
    db_path, is_new = ensure_database()
    if is_new:
        sys.stderr.write(f"[SoR] Database created and seeded at {db_path}\n")
    else:
        sys.stderr.write(f"[SoR] Database loaded from {db_path}\n")


def register_tools(server: FastMCP) -> None:
    """Register all tools on the given FastMCP server instance.

    Tools are registered from src/tools/ modules with thin wrappers.
    The meta-tool router is registered as the primary entry point.
    """

    # ── Meta-Tool Router ─────────────────────────────────────────────────
    @server.tool(
        name="query_sor_curriculum",
        description=(
            "Dynamic meta-tool router for Science of Reading curriculum queries. "
            "Single entry point that routes to the appropriate internal tool. "
            "Returns compact JSON with strand, grade, concepts, prerequisites, "
            "and next steps — designed to keep system prompt context lean.\n\n"
            "Parameters: grade_level (K-5), strand (phonology|morphology|vocabulary|"
            "fluency|comprehension), target_phoneme (optional), syllable_type "
            "(optional), standard_state (optional for CASE alignment)."
        ),
    )
    async def query_sor_curriculum_tool(
        grade_level: str,
        strand: str | None = None,
        target_phoneme: str | None = None,
        syllable_type: str | None = None,
        standard_state: str | None = None,
    ) -> dict[str, Any]:
        from src.core.router import query_sor_curriculum
        return query_sor_curriculum(
            grade_level=grade_level,
            strand=strand,
            target_phoneme=target_phoneme,
            syllable_type=syllable_type,
            standard_state=standard_state,
        )

    # ── Diagnostics ─────────────────────────────────────────────────────
    @server.tool(
        name="analyze_lexile",
        description=(
            "Analyze text complexity and estimate Lexile score. "
            "Computes word count, sentence length, rare word ratio, and maps to "
            "approximate grade level. Based on the Simple View of Reading."
        ),
    )
    async def analyze_lexile(text: str) -> dict[str, Any]:
        from src.tools.diagnostics import analyze_lexile as _analyze
        return _analyze(text)

    @server.tool(
        name="evaluate_simple_view",
        description=(
            "Evaluate a student using the Simple View of Reading. "
            "Returns reading profile (typical/dyslexia/hyperlexic/garden_variety), "
            "deficit codes, and auto-attached remediation cards when decoding < 0.60."
        ),
    )
    async def evaluate_simple_view(
        decoding: float,
        language_comprehension: float,
        grade: str = "1st",
    ) -> dict[str, Any]:
        from src.tools.diagnostics import evaluate_simple_view as _eval
        return _eval(decoding, language_comprehension, grade)

    # ── Decodability ────────────────────────────────────────────────────
    @server.tool(
        name="check_decodability",
        description=(
            "Check what percentage of words in a text are decodable at a given "
            "grade level (K, 1, 2, 3). Uses cumulative phonics patterns and sight "
            "word knowledge expected at each grade."
        ),
    )
    async def check_decodability_tool(
        text: str,
        grade: str = "1",
    ) -> dict[str, Any]:
        from tools.decodability import check_decodability
        return check_decodability(text, grade)

    @server.tool(
        name="verify_decodable_text",
        description=(
            "Production-grade decodability verifier with anti-cueing guardrails. "
            "Checks every word against a cumulative phonics scope, identifies heart "
            "words, flags off-scope patterns, and detects 3-cueing/MSV strategies. "
            "Returns structured error codes (ERR_CUEING_DETECTED, ERR_OFF_SCOPE_PHONEME, "
            "ERR_UNTAUGHT_PATTERN)."
        ),
    )
    async def verify_decodable_text_tool(
        text: str,
        target_skill: str,
        scope_sequence: str = "[]",
        grade_level: str = "1",
        enable_anti_cueing: bool = True,
    ) -> dict[str, Any]:
        import json
        from src.tools.decodability import verify_decodable_text

        try:
            scope = json.loads(scope_sequence) if scope_sequence else []
        except (json.JSONDecodeError, TypeError):
            scope = scope_sequence.split(",") if scope_sequence else []

        return verify_decodable_text(
            text=text,
            target_skill=target_skill,
            scope_sequence=scope if isinstance(scope, list) else [],
            grade_level=grade_level,
            enable_anti_cueing=enable_anti_cueing,
        )

    # ── Vocabulary ──────────────────────────────────────────────────────
    @server.tool(
        name="classify_vocabulary",
        description=(
            "Classify all words in a text into Beck, McKeown & Kucan's three-tier "
            "framework: Tier 1 (basic), Tier 2 (high-utility academic), Tier 3 "
            "(domain-specific)."
        ),
    )
    async def classify_vocabulary(
        text: str,
        domain: str = "literacy",
    ) -> dict[str, Any]:
        from tools.vocabulary import classify_text
        return classify_text(text, domain)

    @server.tool(
        name="match_word",
        description=(
            "Look up a single word's vocabulary tier, grade-level frequency, and "
            "decodability status in the corpus database."
        ),
    )
    async def match_word(
        word: str,
        grade: int | None = None,
    ) -> dict[str, Any]:
        from tools.vocabulary import match_word_vocabulary
        return match_word_vocabulary(word, grade)

    # ── Evidence ────────────────────────────────────────────────────────
    @server.tool(
        name="search_evidence",
        description=(
            "Search the evidence database for WWC, BEE, and NRP research papers "
            "related to a reading topic."
        ),
    )
    async def search_evidence_tool(topic: str) -> dict[str, Any]:
        from tools.evidence import search_evidence
        return search_evidence(topic)

    @server.tool(
        name="list_frameworks",
        description="List all theoretical frameworks in the database.",
    )
    async def list_frameworks_tool() -> dict[str, Any]:
        from tools.evidence import list_frameworks
        return list_frameworks()

    @server.tool(
        name="list_assessments",
        description="List evidence-based reading assessments by type.",
    )
    async def list_assessments_tool(
        assessment_type: str | None = None,
    ) -> dict[str, Any]:
        from tools.evidence import list_assessments
        return list_assessments(assessment_type)

    # ── Standards ───────────────────────────────────────────────────────
    @server.tool(
        name="align_standards",
        description=(
            "Find academic standards that align with a text or skill description. "
            "Supports CCSS, TEXAS, FLORIDA, NY, GEORGIA."
        ),
    )
    async def align_standards_tool(
        description: str,
        state: str = "CCSS",
        grade: str | None = None,
    ) -> dict[str, Any]:
        from tools.evidence import align_standards
        return align_standards(description, state, grade)

    @server.tool(
        name="align_standards_case",
        description=(
            "CASE/JSON-LD standards alignment with 1EdTech CASE CFItem GUIDs. "
            "Outputs interoperable JSON-LD metadata blocks mapped to state "
            "competency codes (CCSS, TEXAS, FLORIDA, NY, GEORGIA)."
        ),
    )
    async def align_standards_case_tool(
        text_description: str,
        state: str = "CCSS",
        grade: str | None = None,
        output_format: str = "summary",
    ) -> dict[str, Any]:
        from src.tools.standards import align_standards_case
        return align_standards_case(text_description, state, grade, output_format)

    # ── Comprehension ──────────────────────────────────────────────────
    @server.tool(
        name="assess_comprehension",
        description="Assess comprehension by analyzing question types against text complexity.",
    )
    async def assess_comprehension_tool(
        text: str,
        questions: str,
        grade: str = "3",
    ) -> dict[str, Any]:
        from src.tools.diagnostics import analyze_lexile
        text_analysis = analyze_lexile(text)

        question_list = [q.strip() for q in questions.split("\n") if q.strip()]
        if not question_list:
            question_list = [q.strip() for q in questions.split("?") if q.strip()]
            question_list = [q + "?" for q in question_list]

        literal_keywords = {"who", "what", "when", "where", "which", "list", "name", "identify", "find"}
        inferential_keywords = {"why", "how", "because", "compare", "contrast", "explain", "infer", "predict"}
        evaluative_keywords = {"evaluate", "judge", "opinion", "do you think", "should", "best", "agree"}

        question_analysis = []
        for i, q in enumerate(question_list):
            q_lower = q.lower()
            if any(kw in q_lower for kw in evaluative_keywords):
                q_type = "evaluative"
            elif any(kw in q_lower for kw in inferential_keywords):
                q_type = "inferential"
            elif any(kw in q_lower for kw in literal_keywords):
                q_type = "literal"
            else:
                q_type = "inferential"
            question_analysis.append({"index": i + 1, "question": q, "type": q_type})

        type_counts = {"literal": 0, "inferential": 0, "evaluative": 0}
        for qa in question_analysis:
            type_counts[qa["type"]] += 1

        total_q = len(question_list)
        literal_pct = round(type_counts["literal"] / total_q * 100) if total_q else 0
        inferential_pct = round(type_counts["inferential"] / total_q * 100) if total_q else 0
        evaluative_pct = round(type_counts["evaluative"] / total_q * 100) if total_q else 0

        if grade in ("K", "1", "2"):
            target_lit, target_inf, target_eval = 60, 30, 10
        elif grade in ("3", "4"):
            target_lit, target_inf, target_eval = 40, 40, 20
        else:
            target_lit, target_inf, target_eval = 30, 40, 30

        return {
            "text_complexity": {
                "lexile": text_analysis.get("lexile_score"),
                "grade_level": text_analysis.get("grade_level"),
                "word_count": text_analysis.get("word_count"),
            },
            "questions": {
                "total": total_q,
                "breakdown": {
                    "literal": {"count": type_counts["literal"], "percentage": literal_pct},
                    "inferential": {"count": type_counts["inferential"], "percentage": inferential_pct},
                    "evaluative": {"count": type_counts["evaluative"], "percentage": evaluative_pct},
                },
                "analysis": question_analysis,
            },
            "grade_targets": {"literal": target_lit, "inferential": target_inf, "evaluative": target_eval},
            "recommendation": "See question type breakdown above for analysis.",
            "framework_note": (
                "Simple View of Reading: comprehension questions should assess both "
                "decoding accuracy and linguistic understanding."
            ),
        }

    # ── Remediation ────────────────────────────────────────────────────
    @server.tool(
        name="get_instructional_remediation",
        description=(
            "Generate a complete instructional remediation card. Returns: "
            "Micro-PD, I Do/We Do/You Do script, multisensory cue, word chain, "
            "corrective feedback. Deterministic — no LLM hallucinations."
        ),
    )
    async def get_remediation(
        deficit_code: str,
        grade_level: str = "1st",
    ) -> dict[str, Any]:
        from src.tools.remediation import get_instructional_remediation as get_card
        card = get_card(deficit_code, grade_level)
        return {"card": card.model_dump(), "markdown": card.to_markdown()}

    @server.tool(
        name="recommend_decodable_resources",
        description="Recommend decodable passages constrained to mastered skills.",
    )
    async def recommend_resources(
        mastered_skills: str,
        target_phoneme: str,
        topic_interest: str = "",
    ) -> dict[str, Any]:
        from tools.decodable_resources import recommend_decodable_resources as rec
        skills = [s.strip() for s in mastered_skills.split(",") if s.strip()]
        topic = topic_interest.strip() or None
        return rec(skills, target_phoneme, topic).model_dump()

    @server.tool(
        name="list_remediations",
        description="List all available remediation deficit codes and skill names.",
    )
    async def list_remediations() -> dict[str, Any]:
        from src.tools.remediation import list_available_remediations as list_r
        return list_r()

    # ── Privacy / FERPA ────────────────────────────────────────────────
    @server.tool(
        name="verify_privacy_status",
        description="Verify FERPA compliance: confirms ZDR mode is active.",
    )
    async def verify_privacy_status() -> dict[str, Any]:
        from tools.privacy_sanitizer import get_pii_manager
        return get_pii_manager().get_status()

    @server.tool(
        name="create_privacy_session",
        description="Create a new FERPA-compliant privacy session for student data.",
    )
    async def create_privacy_session(label: str = "") -> dict[str, Any]:
        from tools.privacy_sanitizer import get_pii_manager
        sid = get_pii_manager().create_session(label)
        return {"session_id": sid, "zdr": True}

    @server.tool(
        name="anonymize_student_data",
        description="Strip PII from student records and replace with synthetic tokens.",
    )
    async def anonymize_student_data(
        students_json: str,
        privacy_session_id: str,
    ) -> dict[str, Any]:
        import json as _json
        from tools.privacy_sanitizer import get_pii_manager
        records = _json.loads(students_json)
        if isinstance(records, dict):
            records = [records]
        for r in records:
            r["_session_id"] = privacy_session_id
        mgr = get_pii_manager()
        cleaned = mgr.anonymize_batch(records)
        return {"students": cleaned, "session_id": privacy_session_id, "total_sanitized": len(cleaned)}

    @server.tool(
        name="destroy_privacy_session",
        description="Destroy a privacy session and ALL PII mappings (Zero Data Retention).",
    )
    async def destroy_privacy_session(session_id: str) -> dict[str, Any]:
        from tools.privacy_sanitizer import get_pii_manager
        get_pii_manager().destroy_session(session_id)
        return {"session_id": session_id, "destroyed": True, "zdr_enforced": True}


# Register tools on the default stdio server
register_tools(mcp)


# ── Main ─────────────────────────────────────────────────────────────────


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Science of Reading MCP Server",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  server.py                          # stdio transport (production)
  server.py --http 8080              # HTTP/SSE transport (dev)
  server.py --seed-only              # seed database and exit
        """,
    )
    parser.add_argument("--http", type=int, metavar="PORT", help="Run with HTTP/SSE transport")
    parser.add_argument("--seed-only", action="store_true", help="Seed DB and exit")
    parser.add_argument("--db-path", type=str, default=None, help="Path to DuckDB file")
    return parser.parse_args()


def main() -> None:
    """Entry point."""
    args = parse_args()

    if args.db_path:
        os.environ["SOR_DB_PATH"] = args.db_path

    _ensure_db()

    if args.seed_only:
        print("Database seeded. Exiting.")
        return

    if args.http:
        global mcp
        mcp = FastMCP(
            name="Science of Reading",
            host="0.0.0.0",
            port=args.http,
            instructions="Evidence-based literacy analysis tools grounded in Science of Reading research.",
        )
        register_tools(mcp)
        mcp.run(transport="sse")
    else:
        mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
