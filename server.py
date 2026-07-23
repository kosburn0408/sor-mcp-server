#!/usr/bin/env python3
"""Science of Reading MCP Server.

A Model Context Protocol server providing evidence-based literacy analysis
tools aligned to the Science of Reading research base.

Protocol: MCP (JSON-RPC 2.0 over stdio)
Transport: stdio (subprocess-based, secure by default — no network exposure)
Database: DuckDB (embedded analytical database, no separate server needed)

Theoretical frameworks embedded:
  - Simple View of Reading (Gough & Tunmer, 1986)
  - Scarborough's Reading Rope (2001)
  - National Reading Panel Five Pillars (2000)
  - What Works Clearinghouse Foundational Skills Practice Guide (2016)
  - Beck, McKeown & Kucan Three-Tier Vocabulary (2013)

Tools exposed:
  - analyze_lexile          — Text complexity and Lexile scoring
  - check_decodability      — Decodable text percentage by grade
  - classify_vocabulary     — Tier 1/2/3 word classification
  - search_evidence         — WWC/BEE research paper lookup
  - list_frameworks         — Theoretical framework reference
  - list_assessments        — Evidence-based assessment lookup
  - align_standards         — CASE framework standards alignment
  - match_word              — Single-word tier lookup
  - evaluate_simple_view    — Simple View of Reading diagnostic
  - get_instructional_remediation — Remediation card for a reading deficit
  - recommend_decodable_resources — Decodable text constrained to mastered skills
  - list_remediations       — List all available remediation deficit codes

Usage:
  python server.py                          # stdio (for MCP clients)
  python server.py --seed-only              # seed database and exit
  python server.py --http 8080              # HTTP/SSE transport (dev/debug)
"""

import argparse
import json
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
        "(Lexile), decodability checking, vocabulary tier classification, research "
        "evidence lookup, and standards alignment — all backed by DuckDB-embedded "
        "data from What Works Clearinghouse, Best Evidence Encyclopedia, and the "
        "National Reading Panel.\n\n"
        "Theoretical frameworks: Simple View of Reading, Scarborough's Reading Rope, "
        "Five Pillars of Reading (Phonemic Awareness, Phonics, Fluency, Vocabulary, "
        "Comprehension)."
    ),
    website_url="https://github.com/nousresearch/agentic-edu",
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
    """Register all tools on the given FastMCP server instance."""

    @server.tool(
        name="analyze_lexile",
        description=(
            "Analyze text complexity and estimate Lexile score. "
            "Computes word count, sentence length, rare word ratio, and maps to "
            "approximate grade level. Based on the Simple View of Reading — text "
            "complexity (linguistic comprehension demand) interacts with decoding "
            "ability to determine reading success."
        ),
    )
    async def analyze_lexile(text: str) -> dict[str, Any]:
        from tools.lexile import compute_lexile
        return compute_lexile(text)

    @server.tool(
        name="check_decodability",
        description=(
            "Check what percentage of words in a text are decodable at a given "
            "grade level (K, 1, 2, 3). Uses cumulative phonics patterns and sight "
            "word knowledge expected at each grade. Grounded in NRP phonics findings "
            "(d=0.41) and Scarborough's Rope decoding strand."
        ),
    )
    async def check_decodability_tool(
        text: str,
        grade: str = "1",
    ) -> dict[str, Any]:
        from tools.decodability import check_decodability
        return check_decodability(text, grade)

    @server.tool(
        name="classify_vocabulary",
        description=(
            "Classify all words in a text into Beck, McKeown & Kucan's three-tier "
            "framework: Tier 1 (basic conversation), Tier 2 (high-utility academic), "
            "Tier 3 (domain-specific). Returns breakdown with instructional "
            "recommendations. Aligned to NRP vocabulary findings (d=0.47-0.52)."
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

    @server.tool(
        name="search_evidence",
        description=(
            "Search the evidence database for WWC, BEE, and NRP research papers "
            "related to a reading topic (phonics, fluency, comprehension, phonemic "
            "awareness, vocabulary, simple view, Scarborough's rope). Returns "
            "findings with effect sizes."
        ),
    )
    async def search_evidence_tool(topic: str) -> dict[str, Any]:
        from tools.evidence import search_evidence
        return search_evidence(topic)

    @server.tool(
        name="list_frameworks",
        description=(
            "List all theoretical frameworks in the database: Simple View of Reading, "
            "Scarborough's Reading Rope, National Reading Panel, WWC Practice Guides, "
            "Four-Part Processing Model. Includes descriptions, components, and "
            "references."
        ),
    )
    async def list_frameworks_tool() -> dict[str, Any]:
        from tools.evidence import list_frameworks
        return list_frameworks()

    @server.tool(
        name="list_assessments",
        description=(
            "List evidence-based reading assessments by type (screener, diagnostic, "
            "progress_monitoring, outcome). Includes DIBELS, Acadience, MAP Reading "
            "Fluency, CORE Phonics Survey, PAST, QRI-6, and more."
        ),
    )
    async def list_assessments_tool(
        assessment_type: str | None = None,
    ) -> dict[str, Any]:
        from tools.evidence import list_assessments
        return list_assessments(assessment_type)

    @server.tool(
        name="align_standards",
        description=(
            "Find academic standards that align with a text or skill description. "
            "Supports CCSS, Texas TEKS, Florida B.E.S.T., and New York standards "
            "across grades K-5. Maps to the five pillars framework."
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
        name="assess_comprehension",
        description=(
            "Assess comprehension by analyzing question types against text complexity. "
            "Evaluates whether questions target appropriate comprehension levels "
            "(literal, inferential, evaluative) based on Simple View of Reading and "
            "Scarborough's Rope comprehension strands."
        ),
    )
    async def assess_comprehension_tool(
        text: str,
        questions: str,
        grade: str = "3",
    ) -> dict[str, Any]:
        from tools.lexile import compute_lexile

        text_analysis = compute_lexile(text)

        question_list = [q.strip() for q in questions.split("\n") if q.strip()]
        if not question_list:
            question_list = [q.strip() for q in questions.split("?") if q.strip()]
            question_list = [q + "?" for q in question_list]

        question_analysis = []
        literal_keywords = {"who", "what", "when", "where", "which", "how many", "how much", "list", "name", "identify", "find", "locate"}
        inferential_keywords = {"why", "how", "because", "cause", "compare", "contrast", "explain", "infer", "predict", "conclude", "determine"}
        evaluative_keywords = {"evaluate", "judge", "opinion", "do you think", "would you", "should", "best", "worst", "most important", "agree", "disagree", "justify", "defend"}

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
            target_literal, target_inferential, target_evaluative = 60, 30, 10
        elif grade in ("3", "4"):
            target_literal, target_inferential, target_evaluative = 40, 40, 20
        else:
            target_literal, target_inferential, target_evaluative = 30, 40, 30

        recommendation_parts = []
        if literal_pct < target_literal - 10:
            recommendation_parts.append(
                f"Increase literal questions (currently {literal_pct}%, target ~{target_literal}%) "
                "to ensure basic comprehension before higher-order thinking."
            )
        if inferential_pct < target_inferential - 10:
            recommendation_parts.append(
                f"Add more inferential questions (currently {inferential_pct}%, target ~{target_inferential}%) "
                "to build deeper comprehension."
            )
        if evaluative_pct < target_evaluative - 10:
            recommendation_parts.append(
                f"Consider adding evaluative questions (currently {evaluative_pct}%, target ~{target_evaluative}%) "
                "for critical thinking practice."
            )
        if not recommendation_parts:
            recommendation_parts.append(
                "Question distribution is well-balanced for the target grade level."
            )

        return {
            "text_complexity": {
                "lexile": text_analysis.get("lexile_score"),
                "grade_level": text_analysis.get("grade_level"),
                "word_count": text_analysis.get("word_count"),
                "mean_sentence_length": text_analysis.get("mean_sentence_length"),
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
            "grade_targets": {
                "literal": target_literal,
                "inferential": target_inferential,
                "evaluative": target_evaluative,
            },
            "recommendation": " ".join(recommendation_parts),
            "framework_note": (
                "Simple View of Reading: comprehension questions should assess both "
                "decoding accuracy and linguistic understanding. Scarborough's Rope: "
                "comprehension depends on background knowledge, vocabulary, language "
                "structures, verbal reasoning, and literacy knowledge. WWC Practice Guide "
                "(Shanahan et al., 2010): teach students to generate and answer questions "
                "across comprehension levels."
            ),
        }

    # ── NEW: Instructional Remediation Tools ──────────────────────────────────

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
        from .remediation import get_bulk_remediations
        from .schemas import SimpleViewResult

        if decoding >= 0.60 and language_comprehension >= 0.60:
            profile = "typical"
        elif decoding < 0.60 and language_comprehension >= 0.60:
            profile = "dyslexia"
        elif decoding >= 0.60 and language_comprehension < 0.60:
            profile = "hyperlexic"
        else:
            profile = "garden_variety"

        deficit_codes: list[str] = []
        if decoding < 0.60:
            if decoding < 0.30:
                deficit_codes = ["phoneme_segmentation", "cvc_mixed", "cvc_short_a"]
            elif decoding < 0.45:
                deficit_codes = ["cvc_mixed", "consonant_blends", "consonant_digraphs"]
            else:
                deficit_codes = ["cvce_silent_e", "vowel_teams", "r_controlled"]

        diagnostic = SimpleViewResult(
            decoding_score=decoding,
            language_comprehension_score=language_comprehension,
            reading_profile=profile,
            deficit_codes=deficit_codes,
        )

        remediations = []
        if decoding < 0.60:
            remediations = get_bulk_remediations(deficit_codes, grade)

        if profile == "typical":
            next_steps = "Student is on track. Continue grade-level instruction."
        elif profile == "dyslexia":
            next_steps = (
                f"Decoding deficit (score={decoding:.2f}). Use attached "
                f"{len(remediations)} remediation cards 4-5x/week. "
                "Administer CORE Phonics Survey. Consider Tier 2."
            )
        elif profile == "hyperlexic":
            next_steps = (
                "Strong decoder, weak comprehender. Focus on vocabulary, "
                "background knowledge, and read-alouds with discussion."
            )
        else:
            next_steps = (
                "Dual deficit. Prioritize decoding, layer comprehension. "
                "Tier 2 or Tier 3 intervention recommended."
            )

        return {
            "diagnostic": diagnostic.model_dump(),
            "remediations": [r.to_markdown() for r in remediations],
            "next_steps": next_steps,
        }

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
        from .remediation import get_instructional_remediation as get_card
        card = get_card(deficit_code, grade_level)
        return {"card": card.model_dump(), "markdown": card.to_markdown()}

    @server.tool(
        name="recommend_decodable_resources",
        description=(
            "Recommend decodable passages constrained to mastered skills. "
            "Passages are pre-written templates with no untaught patterns."
        ),
    )
    async def recommend_resources(
        mastered_skills: str,
        target_phoneme: str,
        topic_interest: str = "",
    ) -> dict[str, Any]:
        from .decodable_resources import recommend_decodable_resources as rec
        skills = [s.strip() for s in mastered_skills.split(",") if s.strip()]
        topic = topic_interest.strip() or None
        return rec(skills, target_phoneme, topic).model_dump()

    @server.tool(
        name="list_remediations",
        description="List all available remediation deficit codes and skill names.",
    )
    async def list_remediations() -> dict[str, Any]:
        from .remediation import list_available_remediations as list_r
        return list_r()

    # ── Privacy & FERPA Compliance Tools ─────────────────────────────────────

    @server.tool(
        name="verify_privacy_status",
        description=(
            "Verify FERPA compliance: confirms ZDR mode is active, "
            "PII sanitization is operational, and no raw PII is exposed "
            "in tool schemas or logs."
        ),
    )
    async def verify_privacy_status() -> dict[str, Any]:
        from .privacy_sanitizer import get_pii_manager
        return get_pii_manager().get_status()

    @server.tool(
        name="create_privacy_session",
        description=(
            "Create a new FERPA-compliant privacy session for student data. "
            "Returns a session_id. All student records processed in this "
            "session use synthetic tokens — real names never reach the LLM."
        ),
    )
    async def create_privacy_session(label: str = "") -> dict[str, Any]:
        from .privacy_sanitizer import get_pii_manager
        sid = get_pii_manager().create_session(label)
        return {"session_id": sid, "zdr": True}

    @server.tool(
        name="anonymize_student_data",
        description=(
            "Strip PII from student records and replace with synthetic tokens. "
            "Provide a JSON array of student objects and a privacy_session_id. "
            "Returns PII-free academic data safe for LLM processing."
        ),
    )
    async def anonymize_student_data(
        students_json: str,
        privacy_session_id: str,
    ) -> dict[str, Any]:
        import json as _json
        from .privacy_sanitizer import get_pii_manager

        records = _json.loads(students_json)
        if isinstance(records, dict):
            records = [records]

        # Attach session ID to each record
        for r in records:
            r["_session_id"] = privacy_session_id

        mgr = get_pii_manager()
        cleaned = mgr.anonymize_batch(records)

        return {
            "students": cleaned,
            "session_id": privacy_session_id,
            "total_sanitized": len(cleaned),
        }

    @server.tool(
        name="destroy_privacy_session",
        description=(
            "Destroy a privacy session and ALL PII mappings (Zero Data "
            "Retention). Call this when you're done with student data. "
            "No PII survives on any storage medium."
        ),
    )
    async def destroy_privacy_session(session_id: str) -> dict[str, Any]:
        from .privacy_sanitizer import get_pii_manager
        get_pii_manager().destroy_session(session_id)
        return {"session_id": session_id, "destroyed": True, "zdr_enforced": True}


# Register tools on the default stdio server
register_tools(mcp)


# ── Main ─────────────────────────────────────────────────────────────────────


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
    parser.add_argument(
        "--http",
        type=int,
        metavar="PORT",
        help="Run with HTTP/SSE transport on given port (for dev/debug)",
    )
    parser.add_argument(
        "--seed-only",
        action="store_true",
        help="Seed the database and exit without starting the server",
    )
    parser.add_argument(
        "--db-path",
        type=str,
        default=None,
        help="Path to DuckDB database file (default: db/sor_evidence.duckdb)",
    )
    return parser.parse_args()


def main() -> None:
    """Entry point."""
    args = parse_args()

    # Set custom DB path if provided
    if args.db_path:
        os.environ["SOR_DB_PATH"] = args.db_path

    # Ensure database is ready
    _ensure_db()

    if args.seed_only:
        print("Database seeded. Exiting.")
        return

    # Start MCP server
    if args.http:
        # Re-create server with HTTP transport settings
        global mcp
        mcp = FastMCP(
            name="Science of Reading",
            host="0.0.0.0",
            port=args.http,
            instructions=(
                "The Science of Reading MCP server provides evidence-based literacy analysis "
                "tools grounded in reading research."
            ),
        )
        # Re-register all tools
        register_tools(mcp)
        mcp.run(transport="sse")
    else:
        mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
