# Science of Reading MCP Server

[![MCP](https://img.shields.io/badge/MCP-1.26+-blue)](https://modelcontextprotocol.io)
[![Python](https://img.shields.io/badge/Python-3.11+-green)](https://python.org)
[![Docker](https://img.shields.io/badge/Docker-ready-blue)](https://docker.com)
[![Web App](https://img.shields.io/badge/Web%20App-sor.edtechlabs.dev-purple)](https://sor.edtechlabs.dev)
[![Standards](https://img.shields.io/badge/Standards-50%20States%20(CASE®)-orange)](https://rosetta.commongoodlt.com)

Production-grade **Science of Reading** Model Context Protocol (MCP) server & Material Design 3 Web Dashboard. Bridges LLMs and K-5 teachers to evidence-based literacy research (Simple View of Reading, Scarborough's Reading Rope, Five Pillars, WWC Practice Guides) via a hybrid execution engine (**Remote API + Local DuckDB OLAP database**).

🌐 **Live Web Application:** [https://sor.edtechlabs.dev](https://sor.edtechlabs.dev)

---

## Theoretical Frameworks & Key Capabilities

| Framework | Key Insight | Web & MCP Capability |
|---|---|---|
| **Simple View of Reading** (Gough & Tunmer, 1986) | Reading comprehension = Decoding × Linguistic Comprehension | `evaluate_simple_view` diagnostic + auto-generated printable I Do/We Do/You Do remediation cards |
| **Scarborough's Reading Rope** (2001) | Skilled reading weaves together Word Recognition and Language Comprehension strands | Interactive Scarborough Rope breakdown & MTSS Tier 1/2/3 framework guides |
| **Five Pillars** (NRP, 2000) | Phonemic Awareness, Phonics, Fluency, Vocabulary, Comprehension | Scope & sequence verification with `verify_decodable_text` and anti-cueing guardrails |
| **Three-Tier Vocabulary** (Beck, McKeown & Kucan, 2013) | Tier 1 (basic), Tier 2 (academic), Tier 3 (domain-specific) | `classify_vocabulary` tool + explicit Tier 2 pre-teaching routine prompt |
| **Standards Satchel CASE® Exchange** (Common Good Learning Tools) | Machine-readable standards across 50 state frameworks | `align_standards` with per-standard deep links (`rosetta.commongoodlt.com`) & CASE REST API URIs |
| **WWC & BEE Evidence Base** (IES / WWC Practice Guides) | Standardized effect sizes ($d$) across randomized controlled trials | `search_evidence` with direct publication links and DOI references (`https://doi.org/...`) |

---

## Exposed MCP Server API (14 Tools, 4 Prompts, 6 Resources)

### MCP Tools (14)

| Tool | Description |
|---|---|
| `get_phonics_scope` | Fetch target phonemes, taught graphemes, and heart words for grade/unit |
| `verify_decodable_text` | Verify text decodability against phonics scope with anti-cueing guardrails |
| `map_orthography` | Map words to phoneme/grapheme sequences and Orton-Gillingham syllable types |
| `lookup_competency` | Look up CASE framework and state academic standards for a phonics skill |
| `analyze_lexile` | Estimate Lexile score, word count, sentence complexity, and grade level |
| `classify_vocabulary` | Classify text into Beck Tier 1/2/3 with instructional recommendations |
| `match_word` | Single-word lookup in vocabulary corpus (tier, decodability, frequency) |
| `search_evidence` | Query WWC/BEE/NRP research database by topic with effect sizes and DOIs |
| `list_frameworks` | Enumerate theoretical frameworks and the 5 Pillars of Reading |
| `list_assessments` | Browse evidence-based assessment tools (screener, diagnostic, PM, outcome) |
| `align_standards` | Map skill descriptions to 50 U.S. state frameworks with CASE® deep links |
| `evaluate_simple_view` | Evaluate student profile using the Simple View of Reading diagnostic formula |
| `get_instructional_remediation` | Get structured I Do / We Do / You Do explicit remediation cards |
| `sanitize_pii` | FERPA-compliant PII anonymization before LLM processing |

### MCP Prompts (4)

| Prompt | Description |
|---|---|
| `generate_aligned_decodable` | Generate a Science of Reading-aligned decodable passage |
| `explicit_phonics_routine` | Generate an explicit phonics routine with I Do/We Do/You Do script |
| `vocabulary_tier_routine` | Generate an explicit Tier 2 vocabulary pre-teaching routine (Beck Model) |
| `standards_alignment_routine` | Generate a lesson plan alignment plan with Standards Satchel CASE URIs |

### MCP Resources (6)

| Resource URI | Description |
|---|---|
| `sor://frameworks` | Theoretical frameworks (Simple View, Scarborough's Rope, 5 Pillars) |
| `sor://frameworks/syllable-rules` | Orton-Gillingham 6 syllable types and division procedure rules |
| `sor://word-lists` | Grade-level decodable word lists and high-frequency heart words |
| `sor://assessments` | Categorized reading assessment instruments (DIBELS, Acadience, MAP) |
| `sor://standards-satchel` | Common Good Learning Tools Standards Satchel CASE network metadata |
| `sor://evidence/meta-analyses` | WWC/BEE research studies with effect sizes and publication DOIs |

---

## Quick Start

### Web Application (FastAPI + Material Design 3)

```bash
# Run FastAPI teacher web dashboard (Port 8093)
python3 webapp.py
```
Access locally at `http://localhost:8093` or live at `https://sor.edtechlabs.dev`.

### Local MCP Server (stdio mode)

```bash
# Install dependencies
pip install -r requirements.txt

# Verify / seed embedded database
python3 server.py --seed-only

# Run as MCP server (stdio transport)
python3 server.py

# Force local offline DuckDB mode
python3 server.py --offline
```

### Docker Deployment

```bash
# Build container
docker compose build

# Seed database
docker compose run --rm sor-seed

# Run HTTP/SSE server (Port 8080)
docker compose up sor-sse
```

---

## Architecture

```
MCP Client (Antigravity / Hermes Agent / Claude)
    ↓ stdio / SSE (JSON-RPC 2.0)
SoR MCP Server (FastMCP)
    ├── Hybrid Routing Engine
    │   ├── Primary: Upstream API (sor.edtechlabs.dev)
    │   └── Fallback: Local Embedded DuckDB (sor_evidence.duckdb)
    ├── 14 Tools Exposed
    ├── 4 MCP Prompts
    ├── 6 MCP Resources
    └── Privacy Layer (FERPA ZDR Anonymizer)
```

---

## License

Copyright © 2026 EdTech Labs. All rights reserved.
