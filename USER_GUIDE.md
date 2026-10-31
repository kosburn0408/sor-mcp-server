# Science of Reading Teacher Workspace — Comprehensive User Manual & Guide

[![Live Web App](https://img.shields.io/badge/Live%20Web%20App-sor.edtechlabs.dev-purple)](https://sor.edtechlabs.dev)
[![Standards Satchel](https://img.shields.io/badge/Standards-50%20States%20(CASE®)-orange)](https://rosetta.commongoodlt.com)
[![Data Minimization](https://img.shields.io/badge/Student%20data-minimized%2C%20not%20stored-green)](#data-privacy)

Welcome to the **Science of Reading (SoR) Teacher-First Workspace**. This platform is designed specifically for **K–3 classroom teachers, reading specialists, interventionists, and literacy coaches**. It translates over 50 years of interdisciplinary reading research (Simple View of Reading, Scarborough's Reading Rope, Five Pillars, IES/WWC Practice Guides) into low-friction, print-ready classroom assets with zero prompt engineering required.

🌐 **Access the Live Web App:** [https://sor.edtechlabs.dev](https://sor.edtechlabs.dev)

---

## Table of Contents
1. [Science of Reading Core Foundations](#science-of-reading-core-foundations)
2. [Teacher Workspace Architecture & Navigation](#teacher-workspace-architecture--navigation)
3. [Step-by-Step Teacher Workflows](#step-by-step-teacher-workflows)
   - [Quadrant 1: Decodable Text Checker](#quadrant-1-decodable-text-checker)
   - [Quadrant 2: Explicit Phonics Routine Builder](#quadrant-2-explicit-phonics-routine-builder)
   - [Quadrant 3: MTSS Screener & Intervention Planning](#quadrant-3-mtss-screener--intervention-planning)
   - [Quadrant 4: Decodability & Anti-Cueing Auditor](#quadrant-4-decodability--anti-cueing-auditor)
   - [Workspace 5: Three-Tier Vocabulary Classifier](#workspace-5-three-tier-vocabulary-classifier)
   - [Workspace 6: State Standards Alignment (CASE® Network)](#workspace-6-state-standards-alignment-case-network)
4. [Classroom Printing & Export Options](#classroom-printing--export-options)
   - [Printable Student Worksheets (@media print)](#printable-student-worksheets-media-print)
   - [Publishing Directly to Google Classroom](#publishing-directly-to-google-classroom)
5. [Context-Aware Dynamic Left Research Drawer](#context-aware-dynamic-left-research-drawer)
6. [Data Privacy](#data-privacy)
7. [MCP Server Integration for AI Agents](#mcp-server-integration-for-ai-agents)

---

## Science of Reading Core Foundations

The Science of Reading is an extensive body of empirical research establishing that **reading must be explicitly and systematically taught**. 

```
                                      SIMPLE VIEW OF READING
 ┌────────────────────────────────┐                             ┌────────────────────────────────┐
 │     Decoding (D)               │     Linguistic              │   Reading Comprehension (R)    │
 │ Word Recognition & Systematic  │  X  Comprehension (LC)   =   │   Ultimate Goal of All         │
 │ Grapheme-Phoneme Mapping       │     Vocabulary & Language   │   Literacy Instruction         │
 └────────────────────────────────┘                             └────────────────────────────────┘
```

### The 5 Essential Pillars of Reading (National Reading Panel)
1. 🔤 **Phonemic Awareness:** Hearing, isolating, and manipulating individual spoken sounds (phonemes).
2. 📖 **Phonics:** Connecting spoken sounds (phonemes) to written letters (graphemes) using explicit sound-spelling rules.
3. 📈 **Fluency:** Reading text accurately, at an appropriate pace, with natural prosody and expression.
4. 📚 **Vocabulary:** Knowing the depth and breadth of word meanings (Tier 1 basic, Tier 2 cross-domain academic, Tier 3 technical).
5. 🧠 **Comprehension:** Active mental construction of meaning, backed by background knowledge and linguistic structures.

---

## Teacher Workspace Architecture & Navigation

When you open **[https://sor.edtechlabs.dev](https://sor.edtechlabs.dev)**, the top section features a **4-Quadrant Task Card Selector**. Clicking any card instantly launches that goal-oriented workspace:

```
┌──────────────────────────────────────────┬──────────────────────────────────────────┐
│ 📖 Decodable Text Checker                │ 🧩 Explicit Phonics Routine Builder       │
│ Create & audit stories using taught GPCs │ Generate 5-day I Do / We Do / You Do     │
│ against the taught scope & sequence.     │ scripts with multisensory cues.          │
├──────────────────────────────────────────┼──────────────────────────────────────────┤
│ 🎯 MTSS / Screener & Remediation         │ 🔍 Decodability & Anti-Cueing Auditor    │
│ Translate DIBELS scores into Georgia     │ Visual proof inspector with color        │
│ screening profiles & intervention cards. │ badges & phonetic breakdown tooltips.    │
└──────────────────────────────────────────┴──────────────────────────────────────────┘
```

Top navigation tabs also allow rapid switching between tools, while the **🔒 Student names removed before processing** badge in the header opens a plain-language explanation of how student data is handled.

---

## Step-by-Step Teacher Workflows

### Quadrant 1: Decodable Text Checker
**Goal:** Check whether a passage is decodable for students who have been taught the patterns through a given grade and unit.

1. **Choose Grade and Unit.** The unit list shows each unit's focus (e.g. *Unit 2: silent-e: a_e, i_e*). The scope box shows what is new this unit, all graphemes taught so far, and the heart words taught so far. Scope is cumulative.
2. **Paste the passage** and click **Audit Decodability**.
3. **Read the report:**
   - **Decodable with taught patterns** and **Decodable + taught heart words** percentages, compared with the target (default 90%; districts should use their own criterion).
   - 🟢 **Decodable** words: every letter or letter team maps to its sound with a taught pattern.
   - 🟡 **Taught heart words.**
   - 🔴 **Not yet decodable** words, with the untaught pattern named (e.g. *night* needs `igh → /ī/`), and **irregular** words that haven't been taught as heart words.
   - ⚪ **Not in dictionary** (usually names): check these by hand.
   - **What blocks this passage:** a list of untaught patterns and the words that need them, so you can swap words or teach the pattern first.
4. **Hover or tap any word** for its sound-by-sound breakdown (e.g. `ch - a - t → /ch/ /ă/ /t/`).

**About the default sequence:** it is an illustrative K–3 progression, not any specific published program. Ask your administrator to load your adopted program's scope & sequence (`SOR_SCOPE_PATH`) for accurate results.

**Generating new text:** the web app checks text; it does not write it. To generate a decodable passage, use the MCP server with an AI assistant and the `generate_aligned_decodable` prompt, which checks each draft with this same engine and revises until it passes.

---

### Quadrant 2: Explicit Phonics Routine Builder
**Goal:** Generate a 5-day explicit phonics lesson script for whole-group or small-group instruction.

1. **Enter Target Phoneme / Skill:** Type the target sound (e.g., `/sh/`, `/ch/`, `/ai/`, `/silent_e/`).
2. **Select Multisensory Cue Technique:**
   - *Finger Tapping* (Phoneme Segmentation)
   - *Elkonin Sound Boxes*
   - *Sky Writing / Arm Tapping*
   - *Magic-E Wand*
3. **Click "Build 5-Day Scripted Routine":** Instantly generates a complete 5-day explicit lesson plan following the **I Do (Teacher Model) → We Do (Guided Practice) → You Do (Independent Mastery)** model, complete with word chaining sequences.

---

### Quadrant 3: MTSS Screener & Intervention Planning
**Goal:** See a student's Simple View of Reading screening profile and get explicit intervention scripts for skills a diagnostic has identified.

1. **Enter scores** for decoding/word reading and for language or listening comprehension on a 0–1 scale (for example, percentile rank ÷ 100), or pick an example profile.
2. **Set the cutoff** to your screener's at-risk benchmark on the same scale. The default 0.60 is only a placeholder.
3. **Choose diagnosed skills (optional).** A screening score tells you *whether* a student is at risk, not *which* phonics skill to teach. After a phonics or phonological awareness diagnostic, select the skills it identified to attach intervention cards.
4. **Student name (optional):** replaced with `[STUDENT]` in your browser before anything is sent.
5. **Click "Show Screening Profile & Intervention Cards":**
   - Profile: *On track*, *Word-recognition difficulty*, *Language-comprehension difficulty*, or *Mixed difficulty*, with a flag when scores are near the cutoff.
   - A reminder that this is a screening profile, not a diagnosis. It cannot identify dyslexia.
   - 5-step explicit intervention cards (I Do / We Do / You Do, word chain, corrective feedback, connected text) for each diagnosed skill.

Georgia's Early Literacy Act (HB 538) requires universal screening in K–3; follow your district's approved screener and intervention guidance.

---

### Quadrant 4: Decodability & Anti-Cueing Auditor
**Goal:** Audit passages, lesson scripts or teacher prompts for three-cueing (MSV) language and untaught patterns.

1. **Paste text** (a passage, a guided-reading script, or a list of prompts).
2. **Click "Run Visual Audit & Anti-Cueing Inspection":**
   - Flags prompts that send students to pictures, context or first letters ("look at the picture", "what would make sense", "does it sound right", "skip it and come back", "get your mouth ready") and explains why each is a problem.
   - Suggests a decoding-focused replacement for each (e.g. "Point to each letter or letter team, say the sounds, and blend them").
   - Checks decodability using the grade and unit selected in Quadrant 1.

---

### Workspace 5: Three-Tier Vocabulary Classifier
**Goal:** Analyze passages using Isabel Beck's 3-Tier model to select high-utility Tier 2 words for pre-teaching.

1. **Paste Passage:** Enter your read-aloud or comprehension text.
2. **Click "Classify Vocabulary Tiers":** Displays count and breakdown across:
   - *Tier 1:* Basic conversational words.
   - 🎯 *Tier 2 (Academic):* High-utility, cross-domain academic words to pre-teach (with occurrence counts).
   - *Tier 3:* Domain-specific technical terms.

---

### Workspace 6: State Standards Alignment (CASE® Network)
**Goal:** Find the standard a lesson or skill addresses. Georgia results come live from Georgia's CASE repository (SuitCASE) and use the current K–12 ELA standards (codes like `1.F.P.2`). Nine other states have only a small sample of codes, with Common Core as a crosswalk.

1. **Enter Learning Goal / Skill:** e.g., `"decode words with silent e"`.
2. **Select State:** Georgia (current K-12 ELA, via SuitCASE), or California, Texas, Florida, New York, North Carolina, Ohio, Pennsylvania, Virginia or Illinois (sample codes only).
3. **Click "Find Standards":** Displays matching codes, descriptions and links to each CASE® record. Read the notice above the results: it says whether the codes are current or a fallback. Matching is by keyword, so confirm the best match.

---

## Classroom Printing & Export Options

Every workspace result includes an **Export Action Bar** designed for instant classroom deployment:

```
[ 🖨️ Print Student Sheet ]  [ 📄 Download PDF ]  [ 📋 Copy Plain Text ]  [ 🎓 Export to Google Classroom ]
```

### Printable Student Worksheets (@media print)
Clicking **`Print Student Sheet`** activates specialized print CSS:
- Automatically hides all app bars, navigation tabs, sidebars, buttons, forms, and background shading.
- Sets body typography to **Atkinson Hyperlegible** (18pt–24pt font with 1.6 line spacing) for optimal readability for young readers and students with dyslexia.
- Automatically inserts a printable worksheet header:
  ```
  Name: ____________________________________    Date: __________________
  Science of Reading Practice Sheet             Grade: _______ Unit: _______
  ```

---

### Publishing Directly to Google Classroom

You can publish decodable passages and phonics routines directly to your Google Classroom stream as an assignment:

1. Click **`🎓 Export to Google Classroom`** on any generated passage or routine.
2. An interactive Google Classroom modal opens:
   - **Google Access Token:** Paste a Google access token with Classroom permissions, or leave it blank to try Demo Mode with sample courses. The token is sent only in the request header and is never stored. There is no built-in Google sign-in yet.
   - **Select Course:** Choose your target active class (e.g., *1st Grade Reading — Unit 3*).
   - **Assignment Title & Instructions:** Pre-filled with your decodable story or 5-day routine script.
   - **Points:** Set maximum points (default: 100).
3. Click **`🎓 Publish Assignment`**:
   - Sends a `POST` request to `https://classroom.googleapis.com/v1/courses/{courseId}/courseWork`.
   - Displays a success state with a direct outbound link (`🔗 Open in Google Classroom`) to view the live assignment.

---

## Context-Aware Dynamic Left Research Drawer

In the top app bar, click the **`Topic & Research Guide`** button to open the pull-out left drawer:

- **Dynamic Content:** The drawer automatically updates its theoretical background, research papers, DOIs, and key vocabulary based on whichever tab you are currently viewing!
- **Tab Context Summary:**
  - *Decodable Text Checker:* Ehri et al. (2001) phonics meta-analysis (d = 0.41 overall; 0.55 when begun in K–1), and definitions for Decodable Text, Off-Scope Words, and Heart Words.
  - *Phonics Routine Builder:* Displays IES/WWC Practice Guide evidence on explicit modeling (I Do / We Do / You Do).
  - *MTSS Screener:* Gough & Tunmer's Simple View of Reading ($R = D \times LC$).
  - *Visual Auditor:* Displays David Kilpatrick's research on eliminating 3-Cueing (MSV) guessing habits.

---

## Data Privacy

The app is designed to minimize student data:

- 🔒 **Names removed in the browser:** the student name you enter is replaced with `[STUDENT]` before anything is sent, and pasted text is scrubbed of that name and of identifier-like patterns (long ID numbers such as GTIDs, emails, phone numbers, dates). A notice appears when something is removed.
- 🔒 **Server-side scrubbing:** the `sanitize_pii` tool drops named PII fields, scrubs free-text fields the same way, and issues pseudonymous tokens using a per-process secret key.
- 🗑️ **Nothing stored:** requests are processed in memory; names and scores are not written to disk or a database.
- ⚠️ **Limits:** automatic scrubbing cannot catch every identifier (for example, a classmate's name in a passage). Don't paste student records into the app. This project has not been independently audited, and using it does not by itself make a deployment FERPA or COPPA compliant; districts should complete their own privacy review and data agreements.

---

## MCP Server Integration for AI Agents

For developers, district IT administrators, and tech-savvy educators running AI assistants (Antigravity, Claude Desktop, Cursor, VS Code, Cline, Roo Code), the underlying Python engine operates as a Model Context Protocol (MCP) server.

### Step-by-Step MCP Server Setup Guide

#### 1. Clone & Initialize Environment
```bash
git clone https://github.com/kosburn0408/sor-mcp-server.git
cd sor-mcp-server

python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Verify / seed local DuckDB database
python3 server.py --seed-only
```

#### 2. Configure Your AI Client

##### 🟢 Claude Desktop (`claude_desktop_config.json`)
Open `~/Library/Application Support/Claude/claude_desktop_config.json` (macOS) or `%APPDATA%\Claude\claude_desktop_config.json` (Windows) and add:

```json
{
  "mcpServers": {
    "science-of-reading": {
      "command": "/absolute/path/to/sor-mcp-server/.venv/bin/python3",
      "args": ["/absolute/path/to/sor-mcp-server/server.py"],
      "env": {
        "SOR_API_BASE_URL": "https://sor.edtechlabs.dev/api/v1",
        "SOR_DB_PATH": "/absolute/path/to/sor-mcp-server/db/sor_evidence.duckdb"
      }
    }
  }
}
```

##### 🟣 Hermes Agent / Antigravity / Cursor / VS Code / Cline (`mcp.json`)
Add the following to your workspace or Hermes `mcp.json`:

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

##### 🤖 Hermes Server Deployment Configuration (`10.100.0.35` / `ubuntu-root`)

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

---

### Available MCP Tools (14)
- `get_phonics_scope`: Cumulative scope & sequence (taught patterns and heart words) through a grade/unit.
- `verify_decodable_text`: Verify decodability ratio & flag untaught GPCs.
- `evaluate_simple_view`: Simple View screening profile (not a diagnosis) and cards for diagnosed skills.
- `get_instructional_remediation`: Retrieve explicit I Do / We Do / You Do intervention cards.
- `align_standards`: Query 50-state framework standards with CASE® Rosetta links.
- `classify_vocabulary`: Classify text into Beck Tier 1/2/3.
- `search_evidence`: Search WWC/BEE research meta-analyses with effect sizes & DOIs.
- `map_orthography`: Map phonemes, graphemes, and Orton-Gillingham syllable division.
- `estimate_readability`: Flesch-Kincaid Grade Level estimate (not a Lexile measure).
- `match_word`: Single-word corpus lookup.
- `list_frameworks`: Enumerate 5 Pillars and Reading Rope.
- `list_assessments`: Categorized assessment instruments catalog.
- `lookup_competency`: CASE competency lookup.
- `sanitize_pii`: Removes student identifiers before LLM processing (pattern-based).

### Available FastMCP Prompts (4)
- `generate_aligned_decodable`: Generate decodable passage matching scope.
- `explicit_phonics_routine`: Scripted 5-day explicit phonics routine.
- `vocabulary_tier_routine`: Isabel Beck Tier 2 pre-teaching routine.
- `standards_alignment_routine`: Lesson plan state standard alignment plan.

### Available MCP Resources (6)
- `sor://frameworks`: Theoretical frameworks (Simple View, Reading Rope, 5 Pillars).
- `sor://frameworks/syllable-rules`: Orton-Gillingham 6 syllable types and division rules.
- `sor://word-lists`: Decodable word lists & high-frequency Heart Words.
- `sor://assessments`: Reading assessment instruments database.
- `sor://standards-satchel`: Standards Satchel (Rosetta) CASE network metadata.
- `sor://evidence/meta-analyses`: WWC/BEE research studies with effect sizes ($d$) & DOIs.

---

## License & Support

© 2026 EdTech Labs. All rights reserved.
For support or questions regarding the workspace or 1EdTech CASE® integration, visit **[https://sor.edtechlabs.dev](https://sor.edtechlabs.dev)**.
