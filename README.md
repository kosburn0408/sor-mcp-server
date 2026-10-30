# Science of Reading MCP Server & Teacher Workspace

[![MCP](https://img.shields.io/badge/MCP-1.26+-blue)](https://modelcontextprotocol.io)
[![Python](https://img.shields.io/badge/Python-3.11+-green)](https://python.org)
[![Docker](https://img.shields.io/badge/Docker-ready-blue)](https://docker.com)
[![Web App](https://img.shields.io/badge/Web%20App-sor.edtechlabs.dev-purple)](https://sor.edtechlabs.dev)
[![Standards](https://img.shields.io/badge/Standards-50%20States%20(CASE®)-orange)](https://rosetta.commongoodlt.com)
[![Google Classroom](https://img.shields.io/badge/Google%20Classroom-OAuth2%20v1-yellow)](https://classroom.google.com)

**Science of Reading** Model Context Protocol (MCP) server and teacher web workspace for K–3. Its core is a deterministic decodability engine: every word in a passage is aligned sound by sound to its dictionary pronunciation using only the phonics patterns taught so far, so teachers (and AI assistants generating text) can see exactly which words students can decode and why the rest can't be. It also provides three-cueing prompt detection, Simple View of Reading screening profiles, explicit intervention scripts, and standards lookup, with **Google Classroom** publishing.

🌐 **Live Web Application:** [https://sor.edtechlabs.dev](https://sor.edtechlabs.dev)  
📖 **Comprehensive Teacher Manual:** [USER_GUIDE.md](USER_GUIDE.md)

---

## Key Features & Capabilities

- 🔬 **Scope-aware decodability engine:** Each word's spelling is aligned to its CMU Pronouncing Dictionary pronunciation using only grapheme-phoneme correspondences (GPCs) taught through the selected grade and unit. Every word gets a status (decodable, taught heart word, not yet decodable, irregular, not in dictionary), a sound-by-sound breakdown (`ch - a - t → /ch/ /ă/ /t/`), and, when blocked, the exact untaught pattern (e.g. `igh → /ī/` for *night*).
- 📚 **Scope & sequence you can replace:** A cumulative default K–3 sequence ships for illustration. Districts should load their adopted program's sequence via `SOR_SCOPE_PATH` (JSON) or pass `taught_gpcs` / `taught_heart_words` directly.
- 🤖 **Verified generation loop for AI assistants:** The `generate_aligned_decodable` prompt has the assistant draft a passage, check it with `verify_decodable_text`, and revise until it meets the target, so generated text is checked rather than assumed to be decodable.
- 🚫 **Three-cueing (MSV) prompt detection:** Flags prompts like "look at the picture" or "what would make sense" and suggests decoding-focused replacements.
- 🎯 **Simple View screening profiles:** Places a student in a word-recognition / language-comprehension quadrant using a cutoff you set to your screener's benchmark. Clearly labelled as screening, not diagnosis; intervention cards attach only for skills a diagnostic has identified.
- 🧩 **Explicit intervention scripts:** Deterministic I Do / We Do / You Do cards with word chains, multisensory cues and corrective feedback.
- 🖨️ **Print-first worksheets** and 🎓 **Google Classroom** coursework export.
- 🔒 **Data minimization:** Student names, ID-like numbers (e.g. GTIDs), emails, phone numbers and dates are scrubbed before processing, and nothing is stored. See [Limitations](#limitations).

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
| `verify_decodable_text` | Check a passage against the cumulative phonics scope: per-word status, missing patterns, heart words, three-cueing flags |
| `map_orthography` | Map words to grapheme/phoneme sequences (dictionary-aligned) and syllable types |
| `lookup_competency` | Look up CASE framework and state academic standards for a phonics skill |
| `estimate_readability` | Flesch-Kincaid Grade Level estimate (not a Lexile measure; unreliable for K–2 text) |
| `classify_vocabulary` | Classify text into Beck Tier 1/2/3 with instructional recommendations |
| `match_word` | Single-word lookup in vocabulary corpus (tier, decodability, frequency) |
| `search_evidence` | Query a small curated research database by topic (effect sizes reported per source, not averaged) |
| `list_frameworks` | Enumerate theoretical frameworks and the 5 Pillars of Reading |
| `list_assessments` | Browse evidence-based assessment tools (screener, diagnostic, PM, outcome) |
| `align_standards` | Map skill descriptions to 50 U.S. state frameworks with CASE® deep links |
| `evaluate_simple_view` | Simple View of Reading screening profile (not a diagnosis); set `cutoff`, pass `diagnosed_skills` for cards |
| `get_instructional_remediation` | Get structured I Do / We Do / You Do explicit remediation cards |
| `sanitize_pii` | Remove student identifiers from a record before LLM processing (pattern-based) |

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
| `sor://evidence/meta-analyses` | Curated research sources with findings and links |

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
# Run complete test suite
python3 -m pytest
```

---

## How Decodability Is Checked

1. The grade and unit resolve to a cumulative set of taught GPC ids and heart words (`src/engine/scope_sequence.py`).
2. Each word's pronunciations come from the CMU Pronouncing Dictionary (`cmudict`).
3. A dynamic-programming search (`src/engine/decoder.py`) tries to spell the pronunciation using the GPC catalog (`src/engine/gpc.py`), costing 0 for a taught GPC and 1 for an untaught one. Positional rules cover silent-e (VCe), open syllables, soft c/g, FLOSS, word-final patterns and schwa (multisyllabic words only).
4. Cost 0 → **decodable**. Otherwise a taught heart word → **heart word**; a spelling that works with untaught GPCs → **not yet decodable** (with the missing patterns); no spelling at all → **irregular**.
5. `accessible_pct` = decodable + taught heart words. `meets_target` compares it to `target_pct` (default 90). Decodability thresholds vary by program and state, so set the target your district uses.

### Using your district's scope & sequence

Create a JSON file shaped like `DEFAULT_SEQUENCE` in `src/engine/scope_sequence.py`:

```json
{
  "K": [{"title": "m, s, t, p, short a", "gpcs": ["m", "s", "t", "p", "short_a"], "heart_words": ["the", "a", "I"]}],
  "1": [{"title": "silent-e: a_e, i_e", "gpcs": ["vce_a", "vce_i"], "heart_words": ["who"]}]
}
```

and set `SOR_SCOPE_PATH=/path/to/scope.json`. GPC ids are listed in `src/engine/gpc.py`; unknown ids are rejected at load time.

---

## Limitations

- **Default scope is illustrative.** It follows the general order of structured-literacy programs but is not any specific program. Results are only as meaningful as the scope they're checked against.
- **Pronunciation dictionary.** Names and rare words may be missing (reported as `not_in_dictionary` for a teacher to check). Dictionary pronunciations reflect General American English.
- **Screening, not diagnosis.** `evaluate_simple_view` cannot identify dyslexia or any disability. The default cutoff (0.60) is a placeholder.
- **Privacy.** Pattern-based scrubbing reduces but cannot guarantee removal of every identifier, and this project has not been independently audited. It does not by itself make a deployment FERPA or COPPA compliant; districts should complete their own privacy review and data agreements.
- **Georgia standards.** Bundled GA codes are the legacy ELAGSE set, replaced by Georgia's K–12 ELA standards in 2025–26. Pulling current standards from Georgia's CASE repository is a planned next step.
- **Research database.** The evidence table is a small curated set. Check original sources before citing.

---

## License

© 2026 EdTech Labs. All rights reserved. The CMU Pronouncing Dictionary is used under its BSD license.
