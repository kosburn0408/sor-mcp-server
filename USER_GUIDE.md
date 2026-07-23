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

### Why This Matters Right Now

**37% of American 4th graders read below the Basic level** on the NAEP (National Assessment of Educational Progress, 2024). That's not a curriculum problem — it's an implementation problem. The research is clear. What's missing is the bridge between what we know and what teachers can actually do at 8:15 on Monday morning.

### What This Tool Does

This MCP server **is that bridge.** It takes the body of SoR research — the frameworks, the effect sizes, the scope and sequences — and turns it into **printable, 5-minute lesson plans** that any teacher can use immediately. It validates that the texts you give students use only the phonics patterns they've been taught. It checks that your curriculum aligns with state standards and research evidence. And it does all of this without ever sending a student's name to an AI model.

This is SoR research, operationalized.

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
| 🏛️ **District Curriculum Director** | Maps purchased curriculum to state standards using CASE GUID alignment, verifies scope and sequence compliance |

### When to Use This Tool

| Context | What You Do |
|---|---|
| 📊 **After universal screening** | Enter DIBELS/Acadience scores → get reading profile + remediation plan |
| 📝 **Planning small groups** | Generate differentiated word chains and decodable passages per group |
| 🤔 **"Why can't he read this?"** | Run `verify_decodable_text` to see exactly which words use untaught phonics patterns |
| 📚 **Evaluating curriculum** | Check if a purchased program's scope and sequence aligns to research and state standards |
| 🎓 **PLC / professional development** | Generate explicit I Do/We Do/You Do scripts for demo lessons |
| 📄 **Writing IEP goals** | Get CASE-aligned standard references and evidence citations for goal justifications |

---

## User Stories

### Story 1: The 2nd Grade Teacher Who Just Got DIBELS Scores

> *"Marcus scored Well Below Benchmark on NWF-CLS. His decoding score is 0.38. What do I do?"*

**Before this tool:** You'd spend 45 minutes Googling "consonant blend interventions," find a TPT worksheet, and hope it targets the right skill.

**With this tool:**

1. Run the diagnostic:
   ```
   evaluate_simple_view(decoding=0.38, comprehension=0.75, grade="2nd")
   ```

2. The server auto-detects: **Dyslexia profile** → deficit codes: `cvc_mixed`, `consonant_blends`, `consonant_digraphs`

3. Three remediation cards are generated automatically. You print them.

4. Monday's 8:15 AM small group: **5-minute Consonant Blends routine** — complete script, word chain, multisensory cue, and corrective feedback language.

**Result:** Marcus gets targeted instruction the next morning, not next week.

---

### Story 2: The Reading Specialist With 6 Intervention Groups

> *"I have 6 students across 3 grade levels with different deficits. I need differentiated materials."*

**Before:** Hours of manual differentiation. Some kids get materials that don't actually match their scope and sequence.

**With this tool:**

1. Batch-diagnose all 6 students in one call
2. For each student, generate:
   - A **word chain** at their exact phonics level
   - A **decodable passage** using only their mastered phonemes
   - A **heart word list** for the sight words they haven't learned yet
3. Run `verify_decodable_text` on every passage to guarantee no untaught patterns slip through

**Result:** Six differentiated reading groups, each with scope-and-sequence-verified materials, in under 5 minutes.

---

### Story 3: The Literacy Coach Running a PLC on Explicit Phonics

> *"I need to demonstrate the I Do/We Do/You Do model for silent-e. My teachers are skeptical that it works."*

**With this tool:**

1. Request: `explicit_phonics_routine(target="silent_e", grade_level="2nd")`
2. The server generates a complete script with:
   - **Micro-PD** (2-sentence research basis — "NRP Phonics, d=0.48")
   - **I DO** (Teacher models with think-aloud: "Watch me: cap → cape!")
   - **WE DO** (Guided practice: "Let's try together: kit→kite, hop→hope")
   - **YOU DO** (Independent: "Now you: can→cane, pin→pine")
   - **Multisensory cue** (Magic E Wand — index card with 'e')
   - **Corrective feedback** ("I see a silent-e. What does it tell the vowel to do?")

3. Print and bring to PLC. Demo it live.

**Result:** Teachers see the structure, try it next day, and Marcus starts decoding CVCe words.

---

### Story 4: The Curriculum Director Evaluating a New Reading Program

> *"This publisher says their program is 'Science of Reading aligned.' Is it?"*

**With this tool:**

1. Run `verify_decodable_text` on a sample passage from the program
2. The verifier flags:
   - 🔴 **Off-scope words** — words using phonics patterns not yet taught
   - 🟡 **Heart words** — sight words that should be explicitly introduced, not expected to be decoded
   - 🔴 **Cueing detected** — any text that encourages guessing from pictures or context
3. Run `align_standards_case` to check if their scope maps to Georgia GSE
4. Run `search_evidence` to see what the research actually says about their approach

**Result:** You go into the adoption meeting with data, not opinions.

---

## For Someone New to the Science of Reading

If you're just starting your SoR journey, this tool helps you learn while you teach:

### Learn the Five Pillars

Ask: `list_frameworks()`

The server returns the National Reading Panel's five pillars — the foundation of structured literacy:

| Pillar | What It Means | Try This Tool |
|---|---|---|
| 🔤 **Phonemic Awareness** | Hearing individual sounds in words | `verify_decodable_text` — see how sounds map to print |
| 📖 **Phonics** | Connecting sounds to letters | `query_sor_curriculum(strand="phonology")` |
| 📈 **Fluency** | Reading accurately with expression | `evaluate_simple_view` — decoding score feeds fluency |
| 📚 **Vocabulary** | Knowing what words mean | `classify_vocabulary` — Tier 1/2/3 word breakdown |
| 🧠 **Comprehension** | Understanding what you read | `analyze_lexile` — text complexity for comprehension |

### Understand the Simple View of Reading

The most important formula in literacy: **Reading = Decoding × Language Comprehension**

Send any two scores (0.0–1.0) and the server tells you exactly what's happening:

```
Decoding: 0.95, Comprehension: 0.90 → "Typical reader — on track"
Decoding: 0.40, Comprehension: 0.85 → "Dyslexia profile — focus on phonics"
Decoding: 0.90, Comprehension: 0.35 → "Hyperlexic — focus on vocabulary and background knowledge"
Decoding: 0.35, Comprehension: 0.35 → "Garden variety — prioritize decoding first"
```

### Avoid the 3-Cueing Mistake

The server actively blocks strategies that reading research has discredited:

| Strategy | Why It's Blocked |
|---|---|
| ❌ "Look at the picture for clues" | Teaches guessing, not decoding |
| ❌ "What word would make sense here?" | MSV — Meaning, Structure, Visual cueing |
| ❌ "Skip it and come back" | Avoids the decoding work entirely |
| ✅ "Sound it out, left to right" | Phoneme-grapheme correspondence — this is the goal |

Run any text through `verify_decodable_text` and the anti-cueing guardrails will flag problematic content.

---

## Quick Start

### From Docker (Recommended)

```bash
git clone https://github.com/kosburn0408/sor-mcp-server.git
cd sor-mcp-server
docker compose up -d
```

### From pip

```bash
pip install -r requirements.txt
python3 server.py --seed-only
python3 server.py
```

---

## Tool Reference

### Diagnostic Tools

| Tool | Input | Output |
|---|---|---|
| `query_sor_curriculum` | grade, strand, phoneme | Scope & sequence for that skill |
| `evaluate_simple_view` | decoding, comprehension scores | Reading profile + auto-remediation |
| `analyze_lexile` | Text | Lexile score + grade level |
| `classify_vocabulary` | Text | Tier 1/2/3 word breakdown |

### Verification Tools

| Tool | Input | Output |
|---|---|---|
| `verify_decodable_text` | Text, scope | % decodable, off-scope words, cueing flags |
| `search_evidence` | Topic | WWC/BEE/NRP papers with effect sizes |
| `align_standards_case` | Skill description, state | CASE GUIDs + state standard codes |

### Remediation Tools

| Tool | Input | Output |
|---|---|---|
| `get_instructional_remediation` | deficit_code, grade | Full remediation card (I Do/We Do/You Do) |
| `explicit_phonics_routine` | Target skill, grade | Structured teaching script |
| `decodable_passage_builder` | Mastered phonemes, target | Skill-constrained passage |
| `multisyllabic_decoding_routine` | Word list, syllable type | Syllable division + mapping |

### Privacy Tools

| Tool | Input | Output |
|---|---|---|
| `create_privacy_session` | Label | Session ID for anonymous tracking |
| `anonymize_student_data` | Student records JSON | PII-free academic data |
| `destroy_privacy_session` | Session ID | Confirms ZDR enforcement |
| `verify_privacy_status` | — | FERPA compliance status |

---

## Error Codes

The server returns structured error codes instead of stack traces:

| Code | Meaning |
|---|---|
| `ERR_OFF_SCOPE_PHONEME` | This phoneme isn't in the scope and sequence for this grade |
| `ERR_INVALID_GRADE_BAND` | Grade must be K–5 |
| `ERR_CUEING_DETECTED` | Content uses 3-cueing/MSV strategies — blocked |
| `ERR_HEART_WORD_AS_DECODABLE` | This word is a heart word, not fully decodable at this level |
| `ERR_INVALID_SYLLABLE_TYPE` | Unknown syllable type — use: closed, open, VCe, r-controlled, vowel team, C+le |
| `ERR_UNTAUGHT_PATTERN` | This pattern hasn't been taught in the provided scope and sequence |
| `ERR_MISSING_SCOPE` | A scope and sequence is required for this verification |

---

## Research Basis

Every tool response references the underlying research:

| Framework | What It Says |
|---|---|
| **Simple View of Reading** (Gough & Tunmer, 1986) | Reading = Decoding × Language Comprehension |
| **Scarborough's Reading Rope** (2001) | Reading weaves word recognition + language comprehension strands |
| **National Reading Panel** (2000) | Five pillars: Phonemic Awareness, Phonics, Fluency, Vocabulary, Comprehension |
| **WWC Practice Guides** | Evidence-based recommendations from IES What Works Clearinghouse |
| **BEE Meta-Analyses** | Effect sizes from Johns Hopkins Best Evidence Encyclopedia |

---

## Getting Help

- **GitHub Issues:** [kosburn0408/sor-mcp-server/issues](https://github.com/kosburn0408/sor-mcp-server/issues)
- **Example workflows:** See the `examples/` directory in the repository
- **Hackathon submission:** Global MCP Hackathon 2026 — Education/Public Good category

---

## License

MIT — use freely in your classroom, district, or product. Student data stays on your machine — always.
