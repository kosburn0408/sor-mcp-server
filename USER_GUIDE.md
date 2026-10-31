# Science of Reading Teacher Workspace — User Guide

[![Live Web App](https://img.shields.io/badge/Live%20Web%20App-sor.edtechlabs.dev-purple)](https://sor.edtechlabs.dev)
[![Georgia standards](https://img.shields.io/badge/Georgia%20standards-live%20via%20SuitCASE-orange)](https://case.georgiastandards.org)
[![Data Minimization](https://img.shields.io/badge/Student%20data-minimized%2C%20not%20stored-green)](#data-privacy)

The **Science of Reading Teacher Workspace** is for **K–3 classroom teachers, reading specialists, interventionists and literacy coaches**. It turns established reading research (the Simple View of Reading, Scarborough's Reading Rope, the National Reading Panel's five components, and IES/WWC practice guides) into checks and scripts you can use in class, with no prompt writing.

🌐 **Open the app:** [https://sor.edtechlabs.dev](https://sor.edtechlabs.dev)

---

## Contents
1. [Science of Reading foundations](#science-of-reading-foundations)
2. [Finding your way around](#finding-your-way-around)
3. [Step 1: MTSS Screener & Intervention Planning](#step-1-mtss-screener--intervention-planning)
4. [Step 2: Decodable Text Checker](#step-2-decodable-text-checker)
5. [Step 3: Explicit Phonics Routine](#step-3-explicit-phonics-routine)
6. [Step 4: Visual Auditor (three-cueing and decodability)](#step-4-visual-auditor-three-cueing-and-decodability)
7. [Classify Vocabulary](#classify-vocabulary)
8. [Standards Alignment](#standards-alignment)
9. [Printing, copying and Google Classroom](#printing-copying-and-google-classroom)
10. [Topic & Research Guide drawer](#topic--research-guide-drawer)
11. [Data privacy](#data-privacy)
12. [For literacy leads: your program's scope & sequence and a coach review](#for-literacy-leads-your-programs-scope--sequence-and-a-coach-review)
13. [For technical staff: AI assistant (MCP) setup](#for-technical-staff-ai-assistant-mcp-setup)

---

## Science of Reading foundations

Reading must be taught explicitly and systematically.

```
                         SIMPLE VIEW OF READING (Gough & Tunmer, 1986)
 ┌─────────────────────────────┐       ┌─────────────────────────────┐       ┌───────────────────────────┐
 │ Word Recognition (Decoding) │   ×   │  Language Comprehension     │   =   │  Reading Comprehension    │
 │ sound-spelling knowledge,   │       │  vocabulary, background     │       │  the goal of literacy     │
 │ decoding, sight recognition │       │  knowledge, language        │       │  instruction              │
 └─────────────────────────────┘       └─────────────────────────────┘       └───────────────────────────┘
```

**The five components (National Reading Panel, 2000)**
1. 🔤 **Phonemic awareness:** hearing, isolating and manipulating the individual sounds in spoken words.
2. 📖 **Phonics:** connecting sounds (phonemes) to letters and letter teams (graphemes).
3. 📈 **Fluency:** reading accurately, at an appropriate rate, with expression.
4. 📚 **Vocabulary:** knowing word meanings in depth (Tier 1 everyday, Tier 2 cross-domain academic, Tier 3 technical).
5. 🧠 **Comprehension:** building meaning from text, supported by background knowledge and language.

---

## Finding your way around

The app opens on four cards, one per step, and a row of tabs with the same tools plus two standalone ones:

```
┌──────────────────────────────────────────┬──────────────────────────────────────────┐
│ STEP 1  🎯 MTSS Screener & Remediation   │ STEP 2  📖 Decodable Text Checker        │
│ Screener scores → Simple View screening  │ Check a passage against the phonics      │
│ profile + cards for diagnosed skills.    │ patterns taught through a grade & unit.  │
├──────────────────────────────────────────┼──────────────────────────────────────────┤
│ STEP 3  🧩 Explicit Phonics Routine      │ STEP 4  🔍 Visual Audit & Anti-Cueing    │
│ Ready-to-teach I Do / We Do / You Do     │ Flag three-cueing prompts and untaught   │
│ scripts with word chains and cues.       │ patterns in passages and lesson scripts. │
└──────────────────────────────────────────┴──────────────────────────────────────────┘
Tabs:  Step 1: MTSS Screener | Step 2: Decodable Text Checker | Step 3: Phonics Routine |
       Step 4: Visual Auditor | Classify Vocabulary | Standards Alignment
```

The **🔒 Student names removed before processing** badge in the header explains how student data is handled. The **Topic & Research Guide** button opens a drawer with the research behind the current tab.

---

## Step 1: MTSS Screener & Intervention Planning

**Goal:** see a student's Simple View of Reading screening profile, and get explicit intervention scripts for skills a diagnostic has identified.

1. **Enter scores** for word reading/decoding and for language or listening comprehension, on a 0–1 scale (for example, percentile rank ÷ 100). Or choose an **Example Profile** to see how it works. Examples use illustrative scores.
2. **Set the At-Risk Cutoff** to your screener's at-risk benchmark on the same scale. The default 0.60 is only a placeholder.
3. **Choose Skills Identified by a Diagnostic (optional).** A screening score tells you *whether* a student is at risk, not *which* skill to teach. After a phonics or phonological-awareness diagnostic, select the skills it identified. Hold Ctrl (Windows) or ⌘ (Mac) to select more than one.
4. **Student Name (optional):** replaced with `[STUDENT]` in your browser before anything is sent.
5. Click **Step 1: Show Screening Profile & Intervention Cards**. You get:
   - **Profile:** *On Track*, *Word-Recognition Difficulty*, *Language-Comprehension Difficulty* or *Mixed Difficulty*, with a warning when a score is near the cutoff.
   - **A reminder** that this is screening, not diagnosis. It cannot identify dyslexia or any disability.
   - **One intervention card per diagnosed skill:** a short teacher brief, I Do / We Do / You Do script, word chain, multisensory cue, corrective feedback and a connected sentence.
   - **Next steps** for the profile.

Georgia's Early Literacy Act (HB 538) requires universal screening in K–3; follow your district's approved screener and intervention guidance.

---

## Step 2: Decodable Text Checker

**Goal:** check whether students who have been taught the patterns through a given grade and unit can decode a passage.

1. **Choose Grade Level and Unit / Module Focus.** Each unit shows its focus (e.g. *Unit 2: silent-e: a_e, i_e*). The box below shows what's new this unit, every grapheme taught so far, and the heart words taught so far. Scope is cumulative.
2. **Paste the passage** and click **Step 2: Audit Decodability & Render Visual Badges**.
3. **Read the report:**
   - **Decodable with taught patterns** and **Decodable + taught heart words** percentages. The second is compared with a 90% target. The target can't be changed in the web app yet; your administrator can set a different criterion through the AI assistant tools.
   - 🟢 **Decodable:** every letter or letter team maps to its sound with a taught pattern.
   - 🟡 **Taught heart word.**
   - 🔴 **Not yet decodable** (the untaught pattern is named, e.g. *night* needs `igh → /ī/`), or **irregular** and not yet taught as a heart word.
   - ⚪ **Not in dictionary** (usually names): check by hand.
   - **What blocks this passage:** each untaught pattern with the words that need it, so you can swap words or teach the pattern first.
   - **Three-cueing prompts** found in the text, if any.
4. **Hover or tap any word** for its sound-by-sound breakdown (e.g. `ch - a - t → /ch/ /ă/ /t/`).
5. **Edit Text in Place** lets you adjust wording in the report before printing. It doesn't re-check the text: to check a revision, change the passage box and audit again.

**About the default sequence:** it is an illustrative K–3 progression, not any specific published program. For accurate results, your literacy lead should load your adopted program's scope & sequence (see [For literacy leads](#for-literacy-leads-your-programs-scope--sequence-and-a-coach-review)).

**Writing new text:** the web app checks text; it doesn't write it. To generate a decodable passage, use an AI assistant connected to this tool's server with the `generate_aligned_decodable` prompt. It checks each draft with this same checker and revises until the draft passes.

---

## Step 3: Explicit Phonics Routine

**Goal:** get a ready-to-teach explicit routine for one small-group session, about 5–7 minutes.

1. Choose a **Skill**:
   - phoneme segmentation
   - short a
   - mixed short vowels
   - consonant blends
   - consonant digraphs
   - silent-e
   - r-controlled vowels
   - vowel teams
   - prefix un-
2. Choose a **Grade Level**.
3. Click **Step 3: Show Explicit Routine**. The routine includes:
   - a teacher brief with the research basis
   - an I Do / We Do / You Do script
   - a word chain that changes one sound at a time, plus a "watch for" non-example
   - a multisensory cue with materials and procedure
   - corrective-feedback language
   - a connected sentence to read

Repeat the routine across several days as students need. The scripts are written by people, not generated, and are the same each time.

---

## Step 4: Visual Auditor (three-cueing and decodability)

**Goal:** check passages, guided-reading scripts or teacher prompts for three-cueing (MSV) language and untaught patterns.

1. **Paste text.**
2. Click **Step 4: Run Visual Audit & Anti-Cueing Inspection**. The audit:
   - **Flags prompts** that send students to pictures, context or first letters, and explains why each is a problem. Examples: "look at the picture", "what would make sense", "does it sound right", "skip it and come back", "get your mouth ready".
   - **Suggests a decoding-focused replacement** for each, such as "Point to each letter or letter team, say the sounds, and blend them".
   - **Checks decodability** using the grade and unit currently selected in Step 2.

---

## Classify Vocabulary

**Goal:** find Tier 2 words worth pre-teaching in a read-aloud or passage (Beck, McKeown & Kucan).

1. Paste the text and click **Classify Vocabulary Tiers**.
2. The results show:
   - **Tier 1 (everyday) words.**
   - **Tier 2 candidates,** most useful first.
   - **Tier 3 (rare or technical) words.**
   - **Names,** and any words without frequency data.

Tiers are **estimates** based on how often words occur in English, plus a small hand-built word list. Frequency can't tell an everyday word like *frog* from an academic word like *reluctant* when both are uncommon, so treat Tier 2 as a list to review. Pre-teach the words that are useful across many texts, and skip words your students already know.

---

## Standards Alignment

**Goal:** find the standard a lesson or skill addresses.

1. **Enter a skill**, e.g. `decode words with silent e`.
2. **Choose a state.**
   - **Georgia (current K-12 ELA, via SuitCASE):** results come live from Georgia's CASE repository, using the current K–12 ELA standards in the K–3 Foundations strands (codes like `1.F.P.2`).
   - **California, Texas, Florida, New York, North Carolina, Ohio, Pennsylvania, Virginia, Illinois:** a small sample of codes only, with Common Core as a fallback.
3. Click **Find Standards (Standards Satchel)**. Read the notice above the results: it says whether the codes are current or a fallback. Matching is by keyword, so confirm the best match.

---

## Printing, copying and Google Classroom

Results from Steps 1–4 have an action bar:

| Result | Buttons |
|---|---|
| Step 1 screening profile | Print Student Sheet · Download PDF · Copy Plain Text · Export to Google Classroom |
| Step 2 and Step 4 reports | Print Student Sheet · Download PDF · Copy Plain Text · Edit Text in Place · Export to Google Classroom |
| Step 3 routine | Print · Copy Plain Text · Export to Google Classroom |

Vocabulary and standards results don't have an action bar; use your browser's print or copy.

### Printing
**Print** hides menus, buttons and forms and uses **Atkinson Hyperlegible** at 18pt or larger with 1.6 line spacing. A header is added:
```
Name: ____________________________________    Date: __________________
Science of Reading Practice Sheet             Grade: _______ Unit: _______
```
**Download PDF** opens the same print dialog; choose *Save as PDF*.

**Before printing or exporting:** anything printed, copied or exported leaves the app's privacy protections, so check it for student names first.

### Google Classroom
1. Click **Export to Google Classroom** on a result.
2. In the window that opens:
   - **Google Access Token:** paste a Google access token with Classroom permissions, or leave it blank to try **Demo Mode** with sample courses. The token is sent only in the request header and is never stored. There's no built-in Google sign-in yet, so most teachers will need IT to provide a token or will use Demo Mode.
   - **Select Course**, **Assignment Title & Instructions** (pre-filled) and **Points** (default 100).
3. Click **Publish Coursework**. You'll see a link to open the assignment in Google Classroom; in Demo Mode the link is a sample.

---

## Topic & Research Guide drawer

Click **Topic & Research Guide** to open a drawer that changes with the tab you're on:

| Tab | What the drawer shows |
|---|---|
| Step 1 | Gough & Tunmer (1986), the Simple View of Reading |
| Step 2 | Ehri, Nunes, Stahl & Willows (2001): systematic phonics, d = 0.41 overall and 0.55 when begun in K–1 |
| Step 3 | Foorman et al. (2016), WWC Foundational Skills practice guide |
| Step 4 | Ehri (2014) on orthographic mapping; Kilpatrick (2015) on three-cueing |
| Vocabulary | Beck, McKeown & Kucan (2013); Marulis & Neuman (2010) |
| Standards | 1EdTech CASE® |

Each drawer also includes key terms. Check the original source before citing a number.

---

## Data privacy

The app is designed to minimize student data:

- 🔒 **Names removed in the browser.** The student name you enter is replaced with `[STUDENT]` before anything is sent. Pasted text is also scrubbed of that name and of identifier-like patterns: long ID numbers such as GTIDs, emails, phone numbers and dates. A notice appears when something is removed.
- 🔒 **Server-side scrubbing.** The server's `sanitize_pii` tool drops named personal fields, scrubs free text the same way, and issues pseudonymous tokens with a per-process secret key.
- 🗑️ **Nothing stored.** Requests are processed in memory; names and scores aren't written to disk or a database.
- ⚠️ **Limits.**
  - Automatic scrubbing can't catch every identifier, such as a classmate's name in a passage. Don't paste student records into the app.
  - Anything you print, copy or export leaves these protections.
  - The project hasn't been independently audited, and using it doesn't by itself make a deployment FERPA or COPPA compliant. Districts should complete their own privacy review and data agreements.

---

## For literacy leads: your program's scope & sequence and a coach review

The Step 2 checker is only as accurate as the scope & sequence it checks against. Two tools help (both described in the [README](README.md#using-your-districts-scope--sequence)):

1. **Load your program's sequence.**
   - Type the program's units into a spreadsheet: grade, unit, title, patterns, heart words.
   - Patterns can be written the way teachers write them (`m; a; sh; a_e; -ed; open syllable`).
   - Technical staff convert it with `scripts/build_scope.py` and turn it on with `SOR_SCOPE_PATH`.
   - A template of the default sequence is in `scopes/template_default.csv`.
2. **Have a coach check the results.**
   - `scripts/coach_review.py` turns 10–20 real passages into a review sheet with one row per word.
   - A coach marks each word agree or disagree, and gives the right status where they disagree.
   - Every disagreement becomes a test, so fixes can be checked. Many disagreements turn out to be scope-file corrections rather than errors in the checker.

---

## For technical staff: AI assistant (MCP) setup

The same engine runs as a Model Context Protocol (MCP) server for AI assistants (Claude Desktop, Cursor, VS Code, Cline, Hermes and others). Full setup, deployment and configuration are in the [README](README.md). In brief:

```bash
git clone https://github.com/kosburn0408/sor-mcp-server.git
cd sor-mcp-server
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python3 server.py --seed-only
```

Claude Desktop (`claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "science-of-reading": {
      "command": "/absolute/path/to/sor-mcp-server/.venv/bin/python3",
      "args": ["/absolute/path/to/sor-mcp-server/server.py"],
      "env": {
        "SOR_DB_PATH": "/absolute/path/to/sor-mcp-server/db/sor_evidence.duckdb"
      }
    }
  }
}
```

Other clients (`mcp.json`):

```json
{
  "mcpServers": {
    "science-of-reading": {
      "command": "python3",
      "args": ["server.py"],
      "cwd": "/path/to/sor-mcp-server",
      "env": { "SOR_DB_PATH": "db/sor_evidence.duckdb" }
    }
  }
}
```

Add `"SOR_SCOPE_PATH": "/path/to/your_program.json"` to `env` once your program's scope file exists.

### Tools (14)
- `get_phonics_scope`: cumulative taught patterns and heart words through a grade/unit.
- `verify_decodable_text`: per-word decodability against the taught scope, missing patterns, three-cueing flags; optional `target_pct` and `min_decodable_pct`.
- `map_orthography`: each word's letters and letter teams mapped to their sounds, with a one-word syllable-type label. It does not divide words into syllables.
- `estimate_readability`: Flesch-Kincaid grade estimate (not a Lexile measure; unreliable for K–2 text).
- `classify_vocabulary`: estimated Tier 1/2/3 with Tier 2 candidates to review.
- `match_word`: one word's estimated tier and scope-aware decodability (decodable by end of a grade, first unit decodable, missing patterns).
- `evaluate_simple_view`: screening profile (not a diagnosis); set `cutoff`, pass `diagnosed_skills` for cards.
- `get_instructional_remediation`: the explicit intervention card for a skill.
- `align_standards`: current Georgia K–12 ELA standards via SuitCASE; a small sample for 9 other states with a Common Core fallback.
- `lookup_competency`: alias of `align_standards`.
- `search_evidence`: small curated research table, effect sizes per source.
- `list_frameworks`, `list_assessments`: frameworks and assessment instruments.
- `sanitize_pii`: removes student identifiers before AI processing (pattern-based).

### Prompts (4)
- `generate_aligned_decodable`: drafts a decodable passage and revises until `verify_decodable_text` passes.
- `explicit_phonics_routine`: has the AI draft an I Do / We Do / You Do routine for a sound. For a fixed, reviewed script, use `get_instructional_remediation` (what Step 3 shows).
- `vocabulary_tier_routine`: Tier 2 pre-teaching routine.
- `standards_alignment_routine`: lesson-to-standards alignment plan.

### Resources (6)
- `sor://frameworks`: Simple View, Reading Rope, five components.
- `sor://frameworks/syllable-rules`: the six syllable types and division rules.
- `sor://word-lists`: high-frequency word lists (Dolch, Fry) and example heart words with their irregular parts.
- `sor://assessments`: reading assessment instruments.
- `sor://standards-satchel`: CASE network metadata.
- `sor://evidence/meta-analyses`: curated research sources with findings and links.

---

## License & support

© 2026 EdTech Labs. All rights reserved.
Questions about the workspace or 1EdTech CASE® integration: [https://sor.edtechlabs.dev](https://sor.edtechlabs.dev).
