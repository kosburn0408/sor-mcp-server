# Science of Reading MCP Server & Teacher Workspace

[![MCP](https://img.shields.io/badge/MCP-1.26–1.x-blue)](https://modelcontextprotocol.io)
[![Python](https://img.shields.io/badge/Python-3.11+-green)](https://python.org)
[![Docker](https://img.shields.io/badge/Docker-ready-blue)](https://docker.com)
[![Web App](https://img.shields.io/badge/Web%20App-sor.edtechlabs.dev-purple)](https://sor.edtechlabs.dev)
[![Standards](https://img.shields.io/badge/Georgia%20standards-live%20via%20SuitCASE%20(CASE®)-orange)](https://case.georgiastandards.org)
[![Google Classroom](https://img.shields.io/badge/Google%20Classroom-export-yellow)](https://classroom.google.com)

**Science of Reading** Model Context Protocol (MCP) server and teacher web workspace for K–3. Its core is a deterministic decodability engine: every word in a passage is aligned sound by sound to its dictionary pronunciation using only the phonics patterns taught so far, so teachers (and AI assistants generating text) can see exactly which words students can decode and why the rest can't be. It also provides three-cueing prompt detection, Simple View of Reading screening profiles, explicit intervention scripts, and standards lookup (current Georgia K–12 ELA standards from Georgia's CASE repository), with **Google Classroom** export.

🌐 **Live Web Application:** [https://sor.edtechlabs.dev](https://sor.edtechlabs.dev)  
📖 **Teacher manual:** [USER_GUIDE.md](USER_GUIDE.md)
🧪 **Method & privacy drafts:** [docs/decodability-methods-note.md](docs/decodability-methods-note.md) · [docs/student-data-handling.md](docs/student-data-handling.md)
📚 **District scope files & coach review:** [Using your district's scope & sequence](#using-your-districts-scope--sequence) · [Checking the engine with a literacy coach](#checking-the-engine-with-a-literacy-coach)

---

## Key Features & Capabilities

- 🔬 **Scope-aware decodability engine:** Each word's spelling is aligned to its CMU Pronouncing Dictionary pronunciation using only grapheme-phoneme correspondences (GPCs) taught through the selected grade and unit. Every word gets a status (decodable, taught heart word, not yet decodable, irregular, not in dictionary), a sound-by-sound breakdown (`ch - a - t → /ch/ /ă/ /t/`), and, when blocked, the exact untaught pattern (e.g. `igh → /ī/` for *night*).
- 📚 **Scope & sequence you can replace:** A cumulative default K–3 sequence ships for illustration. Districts should load their adopted program's sequence via `SOR_SCOPE_PATH` (JSON) or pass `taught_gpcs` / `taught_heart_words` directly.
- 🤖 **Verified generation loop for AI assistants:** The `generate_aligned_decodable` prompt has the assistant draft a passage, check it with `verify_decodable_text`, and revise until it meets the target, so generated text is checked rather than assumed to be decodable.
- 🚫 **Three-cueing (MSV) prompt detection:** Flags prompts like "look at the picture" or "what would make sense" and suggests decoding-focused replacements.
- 🎯 **Simple View screening profiles:** Places a student in a word-recognition / language-comprehension quadrant using a cutoff you set to your screener's benchmark. Clearly labelled as screening, not diagnosis; intervention cards attach only for skills a diagnostic has identified.
- 🧩 **Explicit intervention scripts:** Deterministic I Do / We Do / You Do cards with word chains, multisensory cues and corrective feedback.
- 🏛️ **Standards lookup:** Georgia uses the current K–12 ELA standards from Georgia's CASE repository (SuitCASE), searching the K–3 Foundations strands. Nine other states (CA, FL, IL, NC, NY, OH, PA, TX, VA) have only a small sample of codes, with Common Core as a crosswalk.
- 🖨️ **Print-first worksheets** and 🎓 **Google Classroom export.** Export works with a Google access token the teacher pastes in. The token is sent only in the Authorization header and is never stored; without a token the export runs in demo mode with sample courses. There is no built-in Google sign-in flow yet.
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
        "SOR_DB_PATH": "db/sor_evidence.duckdb"
      }
    }
  }
}
```

##### 🤖 Hermes Server Deployment Configuration

Run Hermes against a checkout of this repository (not the outdated copy in `agentic-edu-skills/mcp-servers/science-of-reading/`):

```json
{
  "mcpServers": {
    "science-of-reading": {
      "command": "/root/sor-mcp-server/.venv/bin/python3",
      "args": ["/root/sor-mcp-server/server.py"],
      "cwd": "/root/sor-mcp-server",
      "env": {
        "SOR_DB_PATH": "/root/sor-mcp-server/db/sor_evidence.duckdb"
      }
    }
  }
}
```

Add `SOR_SCOPE_PATH` once the district's scope & sequence file exists (see [Configuration](#configuration)).

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
| `get_phonics_scope` | Cumulative taught patterns, graphemes and heart words through a grade/unit (default or `SOR_SCOPE_PATH` sequence) |
| `verify_decodable_text` | Check a passage against the cumulative phonics scope: per-word status, missing patterns, heart words, three-cueing flags |
| `map_orthography` | Map words to grapheme/phoneme sequences (dictionary-aligned) and syllable types |
| `lookup_competency` | Alias of `align_standards`, kept for existing clients |
| `estimate_readability` | Flesch-Kincaid Grade Level estimate (not a Lexile measure; unreliable for K–2 text) |
| `classify_vocabulary` | Classify text into Beck Tier 1/2/3 with instructional recommendations |
| `match_word` | One word: vocabulary tier (if in the small corpus) and scope-aware decodability: decodable by the end of a grade, first unit where it becomes decodable, missing patterns |
| `search_evidence` | Query a small curated research database by topic (effect sizes reported per source, not averaged) |
| `list_frameworks` | Enumerate theoretical frameworks and the 5 Pillars of Reading |
| `list_assessments` | Browse evidence-based assessment tools (screener, diagnostic, PM, outcome) |
| `align_standards` | Standards for a skill description: current Georgia K–12 ELA (live, via SuitCASE); a small sample for 9 other states with a Common Core crosswalk |
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
| `sor://word-lists` | High-frequency word lists (Dolch, Fry) and example heart words with their irregular parts. Most high-frequency words are decodable and should be taught through phonics |
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

## Deployment (Docker)

```bash
git pull
docker compose build
docker compose run --rm sor-seed   # only when the research/standards seed data changed (see below)
# restart the web app and MCP services the way they are normally started
```

- The DuckDB database lives on the persistent `sor-duckdb-data` volume (`SOR_DB_PATH=/data/sor_evidence.duckdb`). `ensure_database()` only seeds a **new** database, so changes to `db/seed.py` don't reach production until you run `sor-seed`.
- DuckDB is pinned (`duckdb==1.5.5`) because database files are tied to the DuckDB storage format. Change the pin and re-seed together.
- The Georgia CASE framework is cached on the same volume (`SOR_GA_CASE_CACHE`) and refreshed weekly.
- The homepage is served with `Cache-Control: no-cache`. If a CDN still shows an old page after a deploy, purge `https://sor.edtechlabs.dev/`.

---

## Configuration

| Variable | Default | Purpose |
|---|---|---|
| `SOR_DB_PATH` | `db/sor_evidence.duckdb` (`/data/...` in Docker) | Research, vocabulary, standards and assessment database |
| `SOR_SCOPE_PATH` | *(unset: illustrative default)* | District scope & sequence JSON (build with `scripts/build_scope.py`) |
| `SOR_GA_CASE_BASE_URL` | `https://case.georgiastandards.org/ims/case/v1p1` | Georgia CASE API |
| `SOR_GA_ELA_FRAMEWORK_ID` | `391c3abe-c1ec-4a4a-a942-c9e152b35102` | Georgia K–12 ELA framework |
| `SOR_GA_CASE_CACHE` | `db/ga_ela_case_package.json` (`/data/...` in Docker) | Cached framework package |
| `SOR_GA_CASE_TTL_DAYS` | `7` | Cache lifetime |
| `SOR_GA_CASE_OFFLINE` | *(unset)* | `1` = never download; cache only (used in tests) |
| `SOR_API_BASE_URL` | `https://sor.edtechlabs.dev/api/v1` | Legacy remote API. No current tool depends on it |

All analysis (decodability, scope, orthography, readability, screening, standards) runs locally. Only the Georgia standards lookup makes a network call, to Georgia's CASE repository.

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

Easier: type the program's lessons into a spreadsheet and convert it.

```bash
# Start from the default sequence as a template (one row per unit)
python3 scripts/build_scope.py --export-default -o scopes/my_program.csv
# Edit in Sheets/Excel: grade, unit, title, patterns ("m; a; sh; a_e; -ed"), heart_words ("the; said")
python3 scripts/build_scope.py scopes/my_program.csv -o scopes/my_program.json
SOR_SCOPE_PATH=scopes/my_program.json python3 webapp.py
```

Patterns can be GPC ids or teacher notation (a single vowel = its short sound, `a_e` = silent-e, `-ed`, `open syllable`, `schwa`). The script warns about ambiguous spellings such as `ea` and about patterns introduced twice.

### Decodability targets

States and programs set different criteria, and research on the ideal proportion is limited. For example, California's instructional-materials criteria call for at least 75–80% of words made only of previously taught sound-spellings, with the remaining 20–25% previously taught irregular high-frequency words and story words. To apply a criterion like that, pass `min_decodable_pct=80` along with `target_pct` (the share that must be decodable or taught heart words).

### Checking the engine with a literacy coach

```bash
python3 scripts/coach_review.py prepare scopes/example_passages.csv -o review.csv   # passage_id,grade,unit,text
# Coach fills coach_agrees (Y/N), coach_status, coach_notes for each word in Sheets/Excel
python3 scripts/coach_review.py ingest review.csv                                     # agreement report + test cases
python3 -m pytest tests/test_coach_cases.py
```

Every disagreement is saved to `tests/fixtures/coach_cases.json` and becomes a regression test. Some disagreements mean the engine needs a fix; others mean the scope file doesn't match what the program teaches, so fix the scope file first. Set `SOR_SCOPE_PATH` to the district's scope before both steps.

---

## Limitations

- **Default scope is illustrative.** It follows the general order of structured-literacy programs but is not any specific program. Results are only as meaningful as the scope they're checked against.
- **Pronunciation dictionary.** Names and rare words may be missing (reported as `not_in_dictionary` for a teacher to check). Dictionary pronunciations reflect General American English.
- **Screening, not diagnosis.** `evaluate_simple_view` cannot identify dyslexia or any disability. The default cutoff (0.60) is a placeholder.
- **Privacy.** Pattern-based scrubbing reduces but cannot guarantee removal of every identifier, and this project has not been independently audited. It does not by itself make a deployment FERPA or COPPA compliant; districts should complete their own privacy review and data agreements.
- **Georgia standards.** Georgia lookups use the current K–12 ELA standards from Georgia's CASE repository (`src/tools/ga_case.py`), searching the K–3 Foundations strands and caching the framework for a week. If the repository can't be reached and there's no cache, the bundled legacy ELAGSE codes are returned with a notice. Matching is by keyword, so confirm the best match.
- **Research database.** The evidence table is a small curated set. Check original sources before citing.
- **Vocabulary tiers.** The tier corpus has only a few dozen words; other words fall back to a short academic-word list, and unknown words get no tier.
- **Other states' standards.** Outside Georgia, standards come from a small sample of codes, not complete frameworks.
- **Google Classroom.** Export needs a pasted access token; there's no built-in Google sign-in yet.

---

## License

© 2026 EdTech Labs. All rights reserved. The CMU Pronouncing Dictionary is used under its BSD license.
