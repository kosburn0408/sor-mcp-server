# Science of Reading Teacher Workspace — Comprehensive User Manual & Guide

[![Live Web App](https://img.shields.io/badge/Live%20Web%20App-sor.edtechlabs.dev-purple)](https://sor.edtechlabs.dev)
[![Standards Satchel](https://img.shields.io/badge/Standards-50%20States%20(CASE®)-orange)](https://rosetta.commongoodlt.com)
[![FERPA Shield](https://img.shields.io/badge/FERPA-Compliant%20%26%20ZDR-green)](#-data-privacy--ferpa-shield)

Welcome to the **Science of Reading (SoR) Teacher-First Workspace**. This platform is designed specifically for **K–3 classroom teachers, reading specialists, interventionists, and literacy coaches**. It translates over 50 years of interdisciplinary reading research (Simple View of Reading, Scarborough's Reading Rope, Five Pillars, IES/WWC Practice Guides) into low-friction, print-ready classroom assets with zero prompt engineering required.

🌐 **Access the Live Web App:** [https://sor.edtechlabs.dev](https://sor.edtechlabs.dev)

---

## Table of Contents
1. [Science of Reading Core Foundations](#science-of-reading-core-foundations)
2. [Teacher Workspace Architecture & Navigation](#teacher-workspace-architecture--navigation)
3. [Step-by-Step Teacher Workflows](#step-by-step-teacher-workflows)
   - [Quadrant 1: Decodable Text Generator & Scope Verifier](#quadrant-1-decodable-text-generator--scope-verifier)
   - [Quadrant 2: Explicit Phonics Routine Builder](#quadrant-2-explicit-phonics-routine-builder)
   - [Quadrant 3: MTSS Screener & Georgia HB 538 Remediation](#quadrant-3-mtss-screener--georgia-hb-538-remediation)
   - [Quadrant 4: Decodability & Anti-Cueing Auditor](#quadrant-4-decodability--anti-cueing-auditor)
   - [Workspace 5: Three-Tier Vocabulary Classifier](#workspace-5-three-tier-vocabulary-classifier)
   - [Workspace 6: State Standards Alignment (CASE® Network)](#workspace-6-state-standards-alignment-case-network)
4. [Classroom Printing & Export Options](#classroom-printing--export-options)
   - [Printable Student Worksheets (@media print)](#printable-student-worksheets-media-print)
   - [Publishing Directly to Google Classroom](#publishing-directly-to-google-classroom)
5. [Context-Aware Dynamic Left Research Drawer](#context-aware-dynamic-left-research-drawer)
6. [Data Privacy & FERPA Shield](#data-privacy--ferpa-shield)
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
│ 📖 Decodable Text Generator              │ 🧩 Explicit Phonics Routine Builder       │
│ Create & audit stories using taught GPCs │ Generate 5-day I Do / We Do / You Do     │
│ with auto-fetched grade scope (< 200ms)  │ scripts with multisensory cues.          │
├──────────────────────────────────────────┼──────────────────────────────────────────┤
│ 🎯 MTSS / Screener & Remediation         │ 🔍 Decodability & Anti-Cueing Auditor    │
│ Translate DIBELS scores into Georgia     │ Visual proof inspector with color        │
│ HB 538 cards & CASE® Rosetta links.      │ badges & phonetic breakdown tooltips.    │
└──────────────────────────────────────────┴──────────────────────────────────────────┘
```

Top navigation tabs also allow rapid switching between tools, while the **🔒 FERPA Compliant: PII Auto-Scrubbed** shield badge in the header ensures student data privacy is active.

---

## Step-by-Step Teacher Workflows

### Quadrant 1: Decodable Text Generator & Scope Verifier
**Goal:** Create or audit reading passages to ensure 100% alignment with taught phonics patterns.

1. **Select Scope Scope:** Choose your **Grade Level** (K, 1st, 2nd, 3rd) and **Unit/Module** (Unit 1–10).
2. **Instant Scope Fetching (< 200ms):** The active scope box instantly updates to show:
   - *Taught Graphemes:* e.g. `a, e, i, o, u, sh, ch, th, wh, ck`
   - *Heart Words to Pre-Teach:* e.g. `the, said, was, you`
3. **Input Passage:** Paste your reading text into the box (or use the pre-filled sample text).
4. **Click "Audit Decodability & Render Visual Badges":** The **DecodableInspector** renders:
   - **Audit Metrics Bar:** `% Decodable Ratio`, `Total Word Count`, `Heart Words Used`, and `Anti-Cueing Compliance: PASSED`.
   - 🟢 **Green Badges:** Words fully decodable using taught GPCs.
   - 🟡 **Yellow/Heart Badges:** High-frequency irregular Heart Words.
   - 🔴 **Red Badges:** Off-scope or untaught words.
5. **Interactive Tooltips:** Hover or tap any word badge to view its exact **phonetic breakdown** (e.g. `ch - a - t → /tʃ/ /æ/ /t/`).

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

### Quadrant 3: MTSS Screener & Georgia HB 538 Remediation
**Goal:** Translate assessment scores (DIBELS NWF, Acadience, MAP) into Georgia HB 538-compliant 5-day intervention plans with state standards deep links.

1. **Select HB 538 Screener Deficit Profile:**
   - *Nonsense Word Fluency Low* (Decoding Score: 0.35)
   - *Phoneme Segmentation Deficit* (Decoding Score: 0.28)
   - *Vowel Team Confusion* (Decoding Score: 0.42)
   - *Consonant Blend Breakdown* (Decoding Score: 0.38)
   - Or enter custom assessment scores (Decoding 0.0–1.0 & Language Comprehension 0.0–1.0).
2. **Student Identity (Optional):** Enter a student name. The FERPA Shield automatically anonymizes it to `[STUDENT_1]` before processing.
3. **Click "Generate HB 538 Remediation Plan & CASE Links":**
   - Renders Simple View profile (e.g. `⚠️ Decoding Deficit (Georgia HB 538 Priority)`).
   - Generates 5-day explicit intervention cards.
   - Attaches official **1EdTech CASE® Standards Satchel** deep links (`https://rosetta.commongoodlt.com/#/search?q={code}`) for direct curriculum alignment.

---

### Quadrant 4: Decodability & Anti-Cueing Auditor
**Goal:** Audit commercial reading passages for untaught graphemes and eliminate 3-Cueing (MSV) guessing prompts.

1. **Paste Text Selection:** Paste any reading passage into the text area.
2. **Click "Run Visual Audit & Anti-Cueing Inspection":**
   - Scans text for untaught phonics patterns.
   - Enforces anti-cueing guardrails (flags prompts that encourage students to guess words from pictures or context instead of decoding).

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
**Goal:** Find aligned learning standards across **all 50 U.S. states** powered by Standards Satchel (Rosetta).

1. **Enter Learning Goal / Skill:** e.g., `"decode words with silent e"`.
2. **Select State Framework:** Georgia (GSE), California (CCSS-CA), Texas (TEKS), Florida (B.E.S.T.), New York, North Carolina, Ohio, Pennsylvania, Virginia, etc.
3. **Click "Find Standards":** Displays matching standard codes, descriptions, and direct links to the official 1EdTech CASE® record.

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
   - **Google OAuth Access Token:** Paste your Google OAuth bearer token (or leave blank to test in instant Demo Mode).
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
  - *Decodable Generator:* Displays Linnea Ehri's Orthographic Mapping research, NRP phonics meta-analyses ($d=0.44$), and definitions for Decodable Text, Off-Scope Words, and Heart Words.
  - *Phonics Routine Builder:* Displays IES/WWC Practice Guide evidence on explicit modeling (I Do / We Do / You Do).
  - *MTSS Screener:* Displays Gough & Tunmer's Simple View of Reading ($R = D \times LC$) and Georgia HB 538 literacy requirements.
  - *Visual Auditor:* Displays David Kilpatrick's research on eliminating 3-Cueing (MSV) guessing habits.

---

## Data Privacy & FERPA Shield

Student data privacy is enforced at both the client and server levels:

- 🔒 **Client-Side Pre-Flight Sanitizer (`sanitizeClientPII`):** Before any data leaves your browser, student names (e.g. *Alex Smith*) and student IDs (e.g. *GA-12345*) are automatically replaced with synthetic tokens like `[STUDENT_1]`.
- 🔔 **Toast Notifications:** A green toast popup alerts you whenever student identifiers are detected and anonymized.
- 🛡️ **Zero Data Retention (ZDR):** No student identity mappings are saved to disk or database logs.
- 📜 **Compliance:** Fully compliant with **FERPA**, **COPPA**, and **GDPR** right-to-erasure guidelines.

---

## MCP Server Integration for AI Agents

For developers and tech-savvy administrators running AI assistants (Antigravity, Claude, Hermes), the underlying Python engine operates as a Model Context Protocol (MCP) server:

### Available MCP Tools (14)
- `get_phonics_scope`: Fetch scope & sequence for grade/unit.
- `verify_decodable_text`: Verify decodability ratio & flag untaught GPCs.
- `evaluate_simple_view`: Compute Simple View diagnostic profile & remediations.
- `get_instructional_remediation`: Retrieve explicit I Do / We Do / You Do intervention cards.
- `align_standards`: Query 50-state framework standards with CASE® Rosetta links.
- `classify_vocabulary`: Classify text into Beck Tier 1/2/3.
- `search_evidence`: Search WWC/BEE research meta-analyses with effect sizes & DOIs.
- `sanitize_pii`: FERPA-compliant PII anonymizer.

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
For support or questions regarding Georgia HB 538 implementation or 1EdTech CASE® integration, visit **[https://sor.edtechlabs.dev](https://sor.edtechlabs.dev)**.
