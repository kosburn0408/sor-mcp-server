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

## Theoretical Frameworks & Evidence Base

| Framework | Key Insight | Web & MCP Capability |
|---|---|---|
| **Simple View of Reading** (Gough & Tunmer, 1986) | Reading comprehension = Decoding × Linguistic Comprehension | `evaluate_simple_view` diagnostic + auto-generated printable I Do/We Do/You Do remediation cards |
| **Scarborough's Reading Rope** (2001) | Skilled reading weaves together Word Recognition and Language Comprehension strands | Interactive Scarborough Rope breakdown & MTSS Tier 1/2/3 framework guides |
| **Five Pillars** (NRP, 2000) | Phonemic Awareness, Phonics, Fluency, Vocabulary, Comprehension | Scope & sequence verification with `verify_decodable_text` and anti-cueing guardrails |
| **Three-Tier Vocabulary** (Beck, McKeown & Kucan, 2013) | Tier 1 (basic), Tier 2 (academic), Tier 3 (domain-specific) | `classify_vocabulary` tool + explicit Tier 2 pre-teaching routine prompt |
| **Standards Satchel CASE® Exchange** (Common Good Learning Tools) | Machine-readable standards across 50 state frameworks | `align_standards` with per-standard deep links (`rosetta.commongoodlt.com`) & CASE REST API URIs |
| **Google Classroom REST API v1** (Google Workspace) | Direct coursework assignment publishing | `list_courses` & `publish_coursework` integration via `/api/v1/google-classroom/` |

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

### Local MCP Server (stdio mode)

```bash
# Install dependencies
pip install -r requirements.txt

# Verify / seed embedded database
python3 server.py --seed-only

# Run as MCP server (stdio transport)
python3 server.py
```

---

## License & Data Privacy

© 2026 EdTech Labs. All rights reserved. Student data is auto-anonymized client-side before transmission and never retained on disk.
