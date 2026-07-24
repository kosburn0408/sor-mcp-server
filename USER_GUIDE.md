# Science of Reading MCP Server — User Guide

## What Is the Science of Reading?

The Science of Reading (SoR) is a vast, interdisciplinary body of **scientifically-based research** about reading and issues related to reading and writing. It draws from cognitive psychology, neuroscience, linguistics, and education — spanning over five decades of peer-reviewed studies.

This research has produced a clear, consistent finding: **reading is not natural — it must be explicitly taught.** The human brain is wired for speech, but not for reading. Every child must build the neural pathways that connect visual symbols (letters) to sounds (phonemes) to meaning.

### The Five Pillars

The National Reading Panel (2000) identified five essential, non-negotiable components of effective reading instruction:

| Pillar | What It Is | Why It Matters |
|---|---|---|
| 🔤 **Phonemic Awareness** | Hearing and manipulating individual sounds in spoken words | The #1 predictor of reading success. Without it, phonics makes no sense. |
| 📖 **Phonics** | Connecting sounds (phonemes) to written letters (graphemes) | Systematic phonics instruction has an effect size of d=0.41 — meaning it works for most children, and it's essential for struggling readers. |
| 📈 **Fluency** | Reading accurately, at an appropriate rate, with expression | Fluency is the bridge between decoding and comprehension. If all mental energy goes to sounding out words, there's nothing left for meaning. |
| 📚 **Vocabulary** | Knowing what words mean | Vocabulary in 1st grade predicts reading comprehension in 11th grade. The gap starts early and widens without intervention. |
| 🧠 **Comprehension** | Understanding, remembering, and communicating what was read | This is the ultimate goal of all reading instruction. Every other pillar serves this one. |

---

## Who This Is For

This tool is built for **K-5 educators, reading specialists, and literacy coaches** who are transitioning to Structured Literacy and the Science of Reading. You don't need to be a programmer. You need to be someone who looks at a struggling reader and asks: *"What do I do tomorrow morning at 8:15 AM?"*

### Intended Users

| Role | How They Use It |
|---|---|
| 🍎 **Classroom Teacher (K-3)** | Runs a 2nd grader's DIBELS score through Simple View diagnostic → prints a remediation card → runs a 5-minute small group that same day |
| 📋 **Reading Specialist / Interventionist** | Pulls 6 students, batch-diagnoses, gets differentiated word chains and decodable passages for each group |
| 🏫 **Literacy Coach** | Demonstrates explicit phonics routines during PLCs, aligns Tier 2 interventions to WWC evidence |
| 💻 **EdTech Developer** | Integrates the MCP server into their reading app or assessment platform |
| 🏛️ **District Curriculum Director** | Maps purchased curriculum to state standards across 50 states using CASE GUID alignment, verifies scope and sequence compliance |

---

## How a Teacher Actually Uses This

### Option A: Web Dashboard (Recommended for Teachers)

A teacher-friendly Google Material Design 3 web application is live at:
👉 **[https://sor.edtechlabs.dev](https://sor.edtechlabs.dev)**

- **No installation or command line needed.**
- **6 Dedicated Segmented Tabs:**
  1. 🩺 **Diagnose Student:** Input DIBELS/Acadience/MAP scores to generate printable small-group remediation cards.
  2. 📖 **Check Decodability:** Check passages against phonics scopes and flag high-frequency Heart Words.
  3. 📚 **Classify Vocabulary:** Highlight Tier 2 academic words using Isabel Beck's 3-Tier model.
  4. 🔬 **Evidence Search:** Query WWC/BEE research studies with effect sizes ($d$) and direct paper publication links.
  5. 🏛️ **Standards Alignment:** Search standards across **all 50 U.S. states** with deep links to [Standards Satchel](https://rosetta.commongoodlt.com/) by Common Good Learning Tools.
  6. 🎓 **Teacher Guide:** Interactive accordion directions with Scarborough's Reading Rope diagrams.
- **Context-Aware Left Pull-Out Drawer:** Click **`Topic & Research Guide`** at any time to view theoretical research and tool vocabulary dynamically populated for whichever tab you are currently viewing.

### Option B: Via an AI Agent (MCP Server)

Your district or local setup runs the MCP server once. Teachers access it through an AI assistant (Antigravity, Claude, or Hermes):

```
Teacher: "Marcus scored 0.38 on decoding. What do I do?"
   ↓
AI Agent → evaluate_simple_view(decoding=0.38, grade="2nd")
   ↓
Server → Dyslexia profile → 3 remediation cards
   ↓
Teacher: Printable 5-minute lesson plan
```

### Option C: Direct Install (Tech-Savvy / Developers)

```bash
git clone https://github.com/kosburn0408/sor-mcp-server.git
pip install -r requirements.txt
python3 server.py --seed-only && python3 server.py
```

---

## Data Privacy — FERPA by Design

Student data privacy is built into the architecture at the protocol level.

- 🔒 **Names never reach AI:** Student identities are replaced with synthetic tokens (`std_a3f27b8c`).
- 🗑️ **Zero Data Retention (ZDR):** Identity mappings are destroyed when the session ends.
- 🛡️ **25 PII fields stripped:** First name, last name, student ID, email, date of birth — all removed before processing.

---

## MCP Server Capabilities (14 Tools, 4 Prompts, 6 Resources)

### Tools (14)

| Tool | Input | Output |
|---|---|---|
| `query_sor_curriculum` | grade, strand, phoneme | Scope & sequence for that skill |
| `evaluate_simple_view` | decoding, comprehension scores | Reading profile + auto-remediation |
| `analyze_lexile` | Text | Lexile score + grade level |
| `classify_vocabulary` | Text | Tier 1/2/3 word breakdown |
| `verify_decodable_text` | Text, scope | % decodable, off-scope words, cueing flags |
| `search_evidence` | Topic | WWC/BEE/NRP papers with effect sizes & DOIs |
| `align_standards` | Skill description, state | CASE GUIDs + 50-state standard codes & Rosetta deep links |
| `get_instructional_remediation` | deficit_code, grade | Full remediation card (I Do/We Do/You Do) |
| `map_orthography` | Word list | Phonemes, graphemes, syllable division |
| `get_phonics_scope` | Grade, unit | Target phonemes, graphemes, heart words |
| `lookup_competency` | Skill, state | CASE framework alignment |
| `match_word` | Word, grade | Single word corpus lookup |
| `list_frameworks` | — | Enumerates 5 Pillars and Reading Rope |
| `list_assessments` | tool_type | Assessment instruments database |
| `sanitize_pii` | Data dict | FERPA-sanitized student data |

### MCP Prompts (4)

| Prompt | Input | Output |
|---|---|---|
| `generate_aligned_decodable` | grade, unit, topic | Science of Reading decodable passage |
| `explicit_phonics_routine` | target_phoneme, grade | Scripted I Do / We Do / You Do lesson |
| `vocabulary_tier_routine` | words, grade, topic | Isabel Beck Tier 2 pre-teaching routine |
| `standards_alignment_routine` | skill, state, grade | Lesson plan standard alignment with CASE URIs |

### MCP Resources (6)

| Resource URI | Content |
|---|---|
| `sor://frameworks` | Theoretical frameworks (Simple View, Reading Rope, 5 Pillars) |
| `sor://frameworks/syllable-rules` | Orton-Gillingham 6 syllable types and division procedures |
| `sor://word-lists` | Decodable word lists and high-frequency heart words |
| `sor://assessments` | Reading assessment instruments catalog |
| `sor://standards-satchel` | Standards Satchel (Rosetta) CASE network metadata |
| `sor://evidence/meta-analyses` | WWC/BEE research studies with effect sizes and DOIs |

---

## License

© 2026 EdTech Labs. All rights reserved. Student data stays on your machine — always.
