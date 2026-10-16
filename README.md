# Science of Reading MCP Server & Teacher Workspace

[![MCP](https://img.shields.io/badge/MCP-1.26%2B%20(%3C2)-blue)](https://modelcontextprotocol.io)
[![Python](https://img.shields.io/badge/Python-3.11+-green)](https://python.org)
[![Docker](https://img.shields.io/badge/Docker-ready-blue)](https://docker.com)
[![Web App](https://img.shields.io/badge/Web%20App-sor.edtechlabs.dev-purple)](https://sor.edtechlabs.dev)
[![Standards](https://img.shields.io/badge/Standards-50%20States%20(CASE®)-orange)](https://rosetta.commongoodlt.com)
[![Google Classroom](https://img.shields.io/badge/Google%20Classroom-OAuth2%20v1-yellow)](https://classroom.google.com)

Production-grade **Science of Reading** Model Context Protocol (MCP) server & Material Design 3 Web Dashboard. Bridges LLMs, K-3 teachers, and literacy specialists to evidence-based reading research (Simple View of Reading, Active View of Reading, Scarborough's Reading Rope, Five Pillars, IES/WWC Practice Guides) under Georgia HB 538 guidelines with direct **Google Classroom** coursework publishing.

🌐 **Live Web Application:** [https://sor.edtechlabs.dev](https://sor.edtechlabs.dev)  
📖 **Comprehensive Teacher Manual:** [USER_GUIDE.md](USER_GUIDE.md)

---

## Who It's For and How Teachers Use It

**The problem:** teachers are told to use decodable text and evidence-based routines, but have no quick way to check a passage against the phonics their class has actually been taught, or to see the research behind a practice.

**What it does:** paste a passage, choose a grade (K–3) and unit, and see which words are in scope, which are heart words to pre-teach, which are not taught yet, and what decodable words could replace them. Then pull a 5-day I Do / We Do / You Do routine for the gap, print a student sheet or publish to Google Classroom, and bring cited research to team meetings.

| Who | What they use it for |
|---|---|
| Classroom K–3 teachers | Check texts (including AI-written ones) before class; get ready-made routines |
| Interventionists and literacy coaches | Consistent scope check and routines across a team; MTSS screening profile and next steps |
| School and district leaders | Audit materials and vendor claims against the same cited sources |
| EdTech builders | Call the tools from any MCP-capable AI client so checks live where teachers already work |

**A week in practice:** Monday check the passage; Tuesday run the routine; Wednesday print or publish; Friday screen and plan for the team meeting.

**Honest positioning:** the screening profile is a starting point, not a diagnosis; decodability is judged from spelling patterns against a generic K–3 sequence (swap in your program's); privacy tools are designed to support FERPA-aligned workflows and are not a compliance certification. See Research Alignment & Limitations below.

---

## Key Features & Capabilities

- 📖 **Task-Based 4-Quadrant Workspace:** Goal-oriented task cards for Decodable Text Generation, Explicit Phonics Routines, MTSS Remediation, and Anti-Cueing Auditing.
- ⚡ **Dynamic Scope Fetching (< 200ms):** Grade (K–3) & Unit (1–10) scope controls query `/api/phonics_scope` to pre-fill target phonemes, taught graphemes, and irregular Heart Words.
- 🔬 **DecodableInspector Visual Auditor:** Cumulative grapheme-scope checking (a word is decodable only if every pattern in it has been taught by the selected grade/unit), anti-cueing flags and decodable substitutions. Color-coded word badges (🟢 Green Decodable, 🟡 Yellow Heart Word, 🔴 Red Untaught/Off-Scope) with interactive phonetic breakdown hover tooltips (e.g. `ch - a - t → /tʃ/ /æ/ /t/`).
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

#### 🟣 Hermes Agent / Antigravity / Cursor / VS Code / Cline Configuration (`mcp.json`)

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

##### 🤖 Hermes Server Deployment Configuration (`/root/agentic-edu/mcp-servers/science-of-reading/`)

```json
{
  "mcpServers": {
    "science-of-reading": {
      "command": "/root/sor-mcp-server/.venv/bin/python3",
      "args": ["/root/agentic-edu/mcp-servers/science-of-reading/server.py"],
      "cwd": "/root/agentic-edu/mcp-servers/science-of-reading",
      "env": {
        "SOR_API_BASE_URL": "http://localhost:8093/api/v1",
        "SOR_DB_PATH": "/root/agentic-edu/mcp-servers/science-of-reading/db/sor_evidence.duckdb"
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
| `verify_decodable_text` | Check text against the graphemes taught through a grade (K–3) and optional unit; reports off-scope words, heart words, cueing flags and decodable substitutions |
| `map_orthography` | Map words to phoneme/grapheme sequences and Orton-Gillingham syllable types |
| `lookup_competency` | Look up CASE framework and state academic standards for a phonics skill |
| `analyze_lexile` | Estimate Lexile score, word count, sentence complexity, and grade level |
| `classify_vocabulary` | Classify text into Beck Tier 1/2/3 with instructional recommendations |
| `match_word` | Single-word lookup in vocabulary corpus (tier, decodability, frequency) |
| `search_evidence` | Query the research database by topic; effect sizes appear only when checked against the source, with a verification status on every record |
| `list_frameworks` | Enumerate theoretical frameworks and the 5 Pillars of Reading |
| `list_assessments` | Browse evidence-based assessment tools (screener, diagnostic, PM, outcome) |
| `align_standards` | Map skill descriptions to 50 U.S. state frameworks with CASE® deep links |
| `evaluate_simple_view` | Screening profile from decoding and language-comprehension scores (`typical`, `decoding_weak`, `language_comprehension_weak`, `dual_weak`); not a diagnosis |
| `get_instructional_remediation` | Get structured I Do / We Do / You Do explicit remediation cards |
| `sanitize_pii` | PII anonymization of known name/ID/contact fields before LLM processing (designed to support FERPA; does not scan free text) |

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
# Run complete test suite (127 tests)
python3 -m pytest
```

---

## Standards Alignment (current status)

The `lookup_competency` / `align_standards` tools use a small seeded table of Georgia ELA codes in the older `ELAGSE…` format, with links that open a search on the CASE Network's Rosetta site. The server does **not** yet read live CASE data from Georgia's CASE server (`case.georgiastandards.org`), and the `identifier` values it generates are local placeholders, not official CASE GUIDs. Georgia's current K–12 ELA standards (full implementation 2025–26) use different codes (for example `1.F.P.2`, "Decoding with Phonics") published as CASE packages. Treat the standards output as a convenience pointer until it is connected to the official source.

---

## Research Alignment & Limitations

This project aims to stay faithful to the Science of Reading research base. The rules it follows:

- **Verified numbers only.** An effect size is stored only if it was checked against its source (`verification` column in `research_papers`). Currently these are Ehri et al. (2001) systematic phonics, d = 0.41; NRP phonemic awareness on reading, d = 0.53; and Marulis & Neuman (2010) vocabulary, d = 0.88. Averages use only verified values. WWC Practice Guides report evidence levels (strong, moderate, minimal), not effect sizes, and are recorded that way.
- **Frameworks.** Simple View of Reading (Gough & Tunmer, 1986), Active View of Reading (Duke & Cartwright, 2021), Scarborough's Reading Rope, and the NRP five pillars. The Simple View tool returns a screening profile, not a diagnosis, and recommends building language comprehension in parallel with decoding work.
- **Multisensory and Orton-Gillingham.** Treated as optional support, not a requirement. The meta-analysis by Stevens et al. (2021) found no statistically reliable advantage on most outcomes, and multisensory components were not tested separately.
- **Decodability.** Judged from spelling patterns against a cumulative scope. Default scope sequences (K–3) are a generic example; replace them with your program's sequence for real use. Because it reads spelling, it cannot tell that irregularly pronounced words (for example "yacht") are irregular. Grades 4–5 are not modeled and return a warning.
- **Privacy.** The tools are designed to support FERPA/COPPA-aligned workflows: known name, ID and contact fields are replaced with tokens, session mappings live in memory only, and nothing is written to disk. Free text is not scanned. This is not a compliance certification; check your district's requirements.

Known gaps: the Chard, Vaughn & Tyler (2002) DOI was not confirmed, and the Slavin et al. entry was checked against the technical report, not the journal version. Each record's `notes` field says exactly what was checked.

---

## License & Data Privacy

© 2026 EdTech Labs. All rights reserved. The web app anonymizes known name and ID patterns client-side before transmission, and the server keeps session mappings in memory only. See Research Alignment & Limitations above for what this does and does not cover.
