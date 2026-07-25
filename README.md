# Science of Reading MCP Server & Teacher Workspace

[![MCP](https://img.shields.io/badge/MCP-1.26+-blue)](https://modelcontextprotocol.io)
[![Python](https://img.shields.io/badge/Python-3.11+-green)](https://python.org)
[![Docker](https://img.shields.io/badge/Docker-ready-blue)](https://docker.com)
[![Web App](https://img.shields.io/badge/Web%20App-sor.edtechlabs.dev-purple)](https://sor.edtechlabs.dev)
[![Standards](https://img.shields.io/badge/Standards-50%20States%20(CASE®)-orange)](https://rosetta.commongoodlt.com)
[![Google Classroom](https://img.shields.io/badge/Google%20Classroom-OAuth2%20v1-yellow)](https://classroom.google.com)

Production-grade **Science of Reading** Model Context Protocol (MCP) server & Material Design 3 Web Dashboard. Bridges LLMs, K-3 teachers, and literacy specialists to evidence-based reading research (Simple View of Reading, Scarborough's Reading Rope, Five Pillars, IES/WWC Practice Guides) under Georgia HB 538 guidelines with direct **Google Classroom** coursework publishing.

🌐 **Live Web Application:** [https://sor.edtechlabs.dev](https://sor.edtechlabs.dev)  
📖 **Comprehensive Teacher Manual:** [USER_GUIDE.md](USER_GUIDE.md)

---

## Key Features & Capabilities

- 📖 **Task-Based 4-Quadrant Workspace:** Goal-oriented task cards for Decodable Text Generation, Explicit Phonics Routines, MTSS Remediation, and Anti-Cueing Auditing.
- ⚡ **Dynamic Scope Fetching (< 200ms):** Grade (K–3) & Unit (1–10) scope controls query `/api/phonics_scope` to pre-fill target phonemes, taught graphemes, and irregular Heart Words.
- 🔬 **DecodableInspector Visual Auditor:** Color-coded word badges (🟢 Green Decodable, 🟡 Yellow Heart Word, 🔴 Red Untaught/Off-Scope) with interactive phonetic breakdown hover tooltips (e.g. `ch - a - t → /tʃ/ /æ/ /t/`).
- 🎯 **Georgia HB 538 MTSS Remediation:** Screener deficit selector (Nonsense Word Fluency, Phoneme Segmentation, Vowel Teams, Consonant Blends) outputs 5-day I Do / We Do / You Do intervention cards with direct 1EdTech CASE® Rosetta deep links (`https://rosetta.commongoodlt.com/#/search?q={code}`).
- 🖨️ **Print-First CSS (@media print):** Automatic printable student worksheet formatting using `Atkinson Hyperlegible` font (18pt–24pt, 1.6 line-spacing) with student headers (`Name: ____________ Date: ________`).
- 🎓 **Google Classroom OAuth & Coursework Export:** Export decodable reading assignments directly to active Google Classroom streams via `GET /v1/courses` and `POST /v1/courses/{courseId}/courseWork`.
- 🔒 **FERPA Privacy Shield:** Client-side pre-flight `sanitizeClientPII` auto-anonymizes student names (`[STUDENT_1]`) and student IDs before API transmission.

---

## MCP Server Installation & AI Setup Guide

You can connect the Science of Reading MCP server to **Claude Desktop**, **Antigravity CLI/IDE**, **VS Code**, **Cursor**, or **Cline**.

### Step 1: Clone Repository & Install Dependencies

```bash
# Clone the repository
git clone https://github.com/kosburn0408/sor-mcp-server.git
cd sor-mcp-server

# Create virtual environment and install dependencies
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Verify / seed local embedded DuckDB database
python3 server.py --seed-only
```

### Step 2: Add MCP Server Config to Your AI Client

#### 🟢 Claude Desktop Configuration (`claude_desktop_config.json`)
- **macOS:** `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Windows:** `%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "science-of-reading": {
      "command": "/path/to/sor-mcp-server/.venv/bin/python3",
      "args": ["/path/to/sor-mcp-server/server.py"],
      "env": {
        "SOR_API_BASE_URL": "https://sor.edtechlabs.dev/api/v1",
        "SOR_DB_PATH": "/path/to/sor-mcp-server/db/sor_evidence.duckdb"
      }
    }
  }
}
```

#### 🟣 Antigravity / Cursor / VS Code / Cline Configuration (`mcp.json`)

```json
{
  "mcpServers": {
    "science-of-reading": {
      "command": "python3",
      "args": ["server.py"],
      "cwd": "/path/to/sor-mcp-server",
      "env": {
        "SOR_API_BASE_URL": "https://sor.edtechlabs.dev/api/v1",
        "SOR_DB_PATH": "db/sor_evidence.duckdb"
      }
    }
  }
}
```

### Step 3: Test MCP Server Connection

```bash
# Test stdio transport locally
python3 server.py
```

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

### Running Unit Tests

```bash
# Run complete test suite (77 tests)
python3 -m pytest
```

---

## License & Data Privacy

© 2026 EdTech Labs. All rights reserved. Student data is auto-anonymized client-side before transmission and never retained on disk.
