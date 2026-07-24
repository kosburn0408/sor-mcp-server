# Science of Reading MCP Server

[![MCP](https://img.shields.io/badge/MCP-1.26+-blue)](https://modelcontextprotocol.io)
[![Python](https://img.shields.io/badge/Python-3.11+-green)](https://python.org)
[![Docker](https://img.shields.io/badge/Docker-ready-blue)](https://docker.com)
[![License](https://img.shields.io/badge/License-All%20Rights%20Reserved-lightgrey)](LICENSE)

Production-grade **Science of Reading** Model Context Protocol (MCP) server. Bridges LLMs to evidence-based literacy research (Simple View of Reading, Scarborough's Reading Rope, Five Pillars, WWC Practice Guides) via a hybrid execution engine (**Remote API + Local DuckDB OLAP database**).

---

## Theoretical Frameworks

| Framework | Key Insight |
|---|---|
| **Simple View of Reading** (Gough & Tunmer, 1986) | Reading comprehension = Decoding × Linguistic Comprehension |
| **Scarborough's Reading Rope** (2001) | Skilled reading weaves together Word Recognition and Language Comprehension strands |
| **Five Pillars** (NRP, 2000) | Phonemic Awareness, Phonics, Fluency, Vocabulary, Comprehension |
| **WWC Practice Guides** (2010, 2016) | Evidence-based recommendations for K-3 foundational skills and comprehension |
| **Three-Tier Vocabulary** (Beck, McKeown & Kucan, 2013) | Tier 1 (basic), Tier 2 (academic), Tier 3 (domain-specific) |

---

## Exposed MCP Tools (14 Tools)

| Tool | Description |
|---|---|
| `get_phonics_scope` | Fetch target phonemes, taught graphemes, and heart words for grade/unit |
| `verify_decodable_text` | Verify text decodability against phonics scope with anti-cueing guardrails |
| `map_orthography` | Map words to phoneme/grapheme sequences and Orton-Gillingham syllable types |
| `lookup_competency` | Look up CASE framework and state academic standards for a phonics skill |
| `analyze_lexile` | Estimate Lexile score, word count, sentence complexity, and grade level |
| `classify_vocabulary` | Classify text into Beck Tier 1/2/3 with instructional recommendations |
| `match_word` | Single-word lookup in vocabulary corpus (tier, decodability, frequency) |
| `search_evidence` | Query WWC/BEE/NRP research database by topic with effect sizes |
| `list_frameworks` | Enumerate theoretical frameworks and the 5 Pillars of Reading |
| `list_assessments` | Browse evidence-based assessment tools (screener, diagnostic, PM, outcome) |
| `align_standards` | Map text/skill description to CCSS, TEKS, B.E.S.T., NY, or GA standards |
| `evaluate_simple_view` | Evaluate student profile using the Simple View of Reading diagnostic formula |
| `get_instructional_remediation` | Get structured I Do / We Do / You Do explicit remediation cards |
| `sanitize_pii` | FERPA-compliant PII anonymization before LLM processing |

---

## Quick Start

### Local (Python)

```bash
# Install dependencies
pip install -r requirements.txt

# Verify / seed embedded database
python3 server.py --seed-only

# Run as MCP server (stdio mode)
python3 server.py

# Force local offline DuckDB mode
python3 server.py --offline
```

### Docker

```bash
# Build container
docker compose build

# Seed database
docker compose run --rm sor-seed

# Run HTTP/SSE server (Port 8080)
docker compose up sor-sse
```

### Web Dashboard

```bash
# Run FastAPI teacher web dashboard (Port 8093)
python3 webapp.py
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
    ├── 4 MCP Resources (sor://frameworks, sor://word-lists, etc.)
    └── 2 MCP Prompts (generate_aligned_decodable, explicit_phonics_routine)
```

---

## Directory Structure

```
sor-mcp-server/
├── server.py              # Main FastMCP server (14 tools, prompts, resources)
├── webapp.py              # FastAPI teacher web dashboard
├── pyproject.toml         # Package definition and build configuration
├── requirements.txt       # Unified Python dependencies
├── src/
│   ├── client/            # Async httpx API client with caching & retries
│   ├── config.py          # Pydantic environment configuration
│   ├── core/              # Meta-tool router & error definitions
│   ├── prompts/           # Decodable & phonics prompt builders
│   ├── resources/         # Framework & word list resources
│   ├── schemas/           # Pydantic v2 data models
│   └── tools/             # Consolidated SoR analysis tools
│       ├── decodability.py
│       ├── diagnostics.py
│       ├── evidence.py
│       ├── orthography.py
│       ├── phonics.py
│       ├── privacy.py
│       ├── remediation.py
│       └── vocabulary.py
├── db/
│   ├── database.py        # Connection manager for DuckDB
│   ├── schema.sql         # DuckDB schema
│   └── seed.py            # Evidence & standards seed data
└── tests/                 # Full Pytest test suite (67 tests)
```

---

## License

Copyright © 2026 EdTech Labs. All rights reserved.
