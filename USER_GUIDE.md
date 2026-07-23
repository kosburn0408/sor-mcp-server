# Science of Reading MCP Server — User Guide

## What Is This?

A tool that analyzes any text through the lens of the **Science of Reading** — the body of research on how children learn to read. Teachers get:

- **Lexile score** — how hard is this text?
- **Decodability** — what percentage of words can a K-3 student sound out?
- **Vocabulary tiers** — which words are everyday, academic, or domain-specific?
- **Evidence alignment** — does this approach match what research says works?
- **🆕 Remediation cards** — printable I Do/We Do/You Do scripts for struggling readers
- **🆕 Simple View diagnostic** — profile students + auto-generate lesson plans
- **🆕 Decodable passages** — skill-constrained texts that won't trip students up
- **🆕 FERPA privacy layer** — student names never reach the LLM

It runs as a Docker container on your computer. No cloud, no subscription, no data leaving your machine. **Student PII stays on your machine — always.**

---

## How to Use This Tool

You don't need to be a programmer. Here are the three things most teachers do:

### 📖 1. Check if a Book Is Right for Your Students

> *"Is this chapter too hard for my 2nd graders?"*

```python
# Paste any text and get answers in seconds
text = open("hooch-chapter1.txt").read()

# How hard is it?
compute_lexile(text)
# → Lexile: 550L, Grade: 2 ✅

# Can they sound out the words?
check_decodability(text, grade="2")
# → 78% decodable — some support needed for: "tributary", "observation"

# Which words should I pre-teach?
classify_text(text)
# → Tier 2 words to teach: observe, investigate, protect
```

### 👤 2. Diagnose a Struggling Reader

> *"Marcus guesses at words instead of sounding them out. What's going on?"*

```python
# Simple View of Reading diagnostic
evaluate_simple_view(decoding=0.42, comprehension=0.80, grade="2nd")
# → Profile: DYSLEXIA pattern
# → Deficit codes: cvc_mixed, consonant_blends, consonant_digraphs
# → 3 remediation cards auto-generated ← ready to print and use
```

### 🎯 3. Get a Lesson Plan for a Reading Deficit

> *"I need a 5-minute small-group activity for silent-e. Right now."*

```python
# One call — full lesson plan
card = get_instructional_remediation("cvce_silent_e", "2nd")

# Print this and bring it to your reading group:
print(card.to_markdown())
```

**What prints out:**
```
## 🎯 Instructional Remediation Card: Silent-e Pattern
### 1. Pedagogy Brief (Micro-PD)
The Silent-e Rule: Final-e makes the vowel say its name...
> Research basis: NRP Phonics (d=0.48)

### 2. Explicit Teaching Routine (I Do / We Do / You Do) — ~5 min
🔵 I DO: Watch me read this word: /c/.../a/.../p/, cap. Now I add
    silent-e: cape! The 'a' says its name.
🟡 WE DO: Let's try together: kit→kite, hop→hope, not→note.
🟢 YOU DO: Now you try: can→cane, pin→pine, cub→cube.

### 3. Word Chain & Practice
cap → cape → tape → tap → tape → shape
Watch for: have (rule breaker!)

### 4. Corrective Feedback
❌ If incorrect: "I see a silent-e. What does it tell the vowel to do?"
✅ If correct: "You spotted the silent-e! That's the rule!"
```

### 🔒 4. Keep Student Data Private

```python
# Student names NEVER leave your computer
session = create_privacy_session("reading groups")
# → Jane Doe becomes std_a3f27b8c — LLM sees only the token
# After you're done:
destroy_privacy_session(session)
# → All PII erased. Zero data retention.
```

---

## Quick Start (5 Minutes)

### Step 1: Install Docker

Mac: `brew install --cask docker`
Windows: [docker.com/products/docker-desktop](https://www.docker.com/products/docker-desktop)

### Step 2: Download the Server

```bash
git clone https://github.com/kosburn0408/agentic-edu-skills.git
cd agentic-edu-skills/mcp-servers/science-of-reading
```

### Step 3: Start It

```bash
docker compose up -d
```

Wait 30 seconds. The server is now running.

---

## Using the Server

### Option A: With Hermes Agent (AI Assistant)

If you use Hermes Agent, the server auto-connects. Just ask:

> *"Analyze this text for Lexile level and vocabulary tiers"*
>
> *"Is this passage decodable for a first grader?"*
>
> *"What does the research say about phonics instruction?"*

### Option B: Direct via Python

```python
from tools.lexile import compute_lexile
from tools.vocabulary import classify_text
from tools.decodability import check_decodability

# Your text
text = """Hooch sniffed the morning air. His tail gave one sharp wag.
Something waited around the river bend. The trees whispered secrets."""

# Analyze
lexile = compute_lexile(text)
vocab = classify_text(text)
decode = check_decodability(text, grade=2)

print(f"Lexile: {lexile['lexile_score']}L (Grade {lexile['grade_level']})")
print(f"Decodable: {decode['decodable_pct']}%")
print(f"Tier 2 words: {[w['word'] for w in vocab['word_details'] if w['tier'] == 2]}")
```

### Option C: One-Shot Seed (Populate the Database)

```bash
docker compose --profile seed up
```

This pre-loads the database with research papers, vocabulary lists, and standards. One-time only.

---

## What Each Tool Does

### 📊 Lexile Analysis (`compute_lexile`)

| Input | Output |
|---|---|
| Any English text | Lexile score (e.g., 660L) |
| | Grade level (e.g., "4") |
| | Word count, sentence length, rare word ratio |
| | Framework guidance (Simple View of Reading) |

**Example output:**
```
Lexile: 660L | Grade: 4
Framework: Simple View of Reading — Linguistic comprehension
increasingly drives reading outcomes as decoding becomes automatic.
```

### 🔤 Decodability Check (`check_decodability`)

| Input | Output |
|---|---|
| Text + target grade (K-3) | % of words that are decodable |
| | List of non-decodable words |
| | Grade-specific phonics patterns checked |

K checks CVC words (cat, dog). Grade 1 adds blends (stop, frog). Grade 2 adds digraphs (ship, chat). Grade 3 adds multisyllabic decoding.

### 📚 Vocabulary Tiers (`classify_text`)

Based on Beck, McKeown & Kucan's tiered vocabulary framework:

| Tier | Examples | What It Means |
|---|---|---|
| **Tier 1** | dog, river, tree, run | Everyday words — kids already know these |
| **Tier 2** | observe, investigate, protect | Academic words — teach these explicitly |
| **Tier 3** | tributary, ecosystem, conservation | Domain-specific — teach in context |

### 🔬 Evidence Search (`search_evidence`)

Query the embedded research database:

```python
from tools.evidence import search_evidence
results = search_evidence("phonics")
# Returns WWC Practice Guides, BEE meta-analyses, NRP findings
```

### 📋 Standards Alignment (`align_standards`)

Check if a text aligns with state standards:

```python
from tools.evidence import align_standards
standards = align_standards(grade="2", subject="ELA", state="Georgia")
```

---

## Real-World Examples

### Example 1: Evaluating a Book for Your Classroom

> *"Is Hooch the River Dog appropriate for my second graders?"*

```python
text = open("hooch-chapter1.txt").read()
r = compute_lexile(text)
print(f"Lexile: {r['lexile_score']}L → Grade {r['grade_level']}")
# → Lexile: 550L → Grade 2 ✅
```

### Example 2: Building a Vocabulary Lesson

> *"Which words should I pre-teach before reading Chapter 4?"*

```python
v = classify_text(chapter4_text)
tier2 = [w['word'] for w in v['word_details'] if w['tier'] == 2]
print("Pre-teach these words:", tier2)
# → ['debris', 'observation', 'current']
```

### Example 3: Checking Decodability for Early Readers

> *"Can my struggling first graders read this independently?"*

```python
d = check_decodability(text, grade=1)
print(f"{d['decodable_pct']}% decodable")
if d['decodable_pct'] < 80:
    print("⚠️ May need support for:", d['non_decodable'])
```

---

## 🆕 Instructional Remediation

### Diagnose a Struggling Reader

> *"My 2nd grader reads choppy and guesses at words. How do I help?"*

```python
from tools.remediation import get_instructional_remediation

# Step 1: Diagnose with Simple View of Reading
# evaluate_simple_view(decoding=0.35, comprehension=0.75, grade="2nd")
# → Profile: dyslexia → 3 deficit codes auto-generated

# Step 2: Get a remediation card
card = get_instructional_remediation("cvce_silent_e", "2nd")
print(card.to_markdown())
```

**What you get — a printable card with:**
- 📋 **Micro-PD** — 2-sentence explainer of the reading principle
- 🎯 **I Do / We Do / You Do** — 5-minute script for small-group instruction
- 👆 **Multisensory Cue** — kinesthetic anchor (finger tapping, sound boxes, magic-e wand)
- 🔗 **Word Chain** — 4-6 words for pattern practice
- 💬 **Corrective Feedback** — exactly what to say for errors and successes
- 📖 **Connected Text** — one decodable sentence using the target pattern

### Available Remediations (9 Deficit Codes)

| Code | Skill | Grade |
|---|---|---|
| `cvc_short_a` | Short Vowel /a/ | K-1 |
| `cvc_mixed` | Mixed Short Vowels | K-1 |
| `consonant_blends` | CCVC/CVCC Blends | 1-2 |
| `cvce_silent_e` | Silent-e Pattern | 1-2 |
| `consonant_digraphs` | sh, ch, th, wh, ck | K-1 |
| `vowel_teams` | ai, ay, ee, ea, oa | 2-3 |
| `r_controlled` | ar, or, er, ir, ur | 2-3 |
| `phoneme_segmentation` | Phoneme Awareness | K-1 |
| `prefix_un` | Prefix un- | 2-3 |

### Get Decodable Passages

> *"I need a short text my student can actually read — only using the sounds they know."*

```python
from tools.decodable_resources import recommend_decodable_resources
result = recommend_decodable_resources(
    mastered_skills=["cvc_mixed", "basic_sight_words"],
    target_phoneme="short_a",
    topic_interest="animals"
)
# → "Pat and the Cat" — 14 words, 100% decodable
```

---

## 🔒 Student Privacy & FERPA Compliance

The server enforces **Zero Data Retention (ZDR)** — student names and IDs never reach an LLM. Here's how it works:

### The Privacy Flow

```
Teacher uploads: "Jane Doe, GA-12345, decoding=0.42"
    ↓ anonymize_student_data()
LLM sees:       "std_a3f27b8c, decoding=0.42"  ← NO real name
    ↓ LLM generates remediation
    ↓ deanonymize
Teacher sees:   "Jane Doe needs: consonant blends" ← name restored
    ↓ destroy_privacy_session()
All PII erased from memory
```

### Using It

```python
from tools.privacy_sanitizer import get_pii_manager

mgr = get_pii_manager()
session = mgr.create_session("Tuesday reading groups")

# Strip PII from student records
student = {
    "first_name": "Jane", "last_name": "Doe",
    "state_student_id": "GA-12345",
    "decoding_score": 0.42, "grade": "2nd"
}
student["_session_id"] = session
clean = mgr.anonymize_student_record(student)
# → {"student_token": "std_a3f27b8c", "decoding_score": 0.42, "grade": "2nd"}
# ↑ Safe to send to LLM!

# After LLM generates output:
output = mgr.deanonymize_response_text(
    "std_a3f27b8c needs consonant blend remediation", session
)
# → "Jane Doe needs consonant blend remediation"

# When done — erase everything:
mgr.destroy_session(session)
```

### What's Stripped (25 Fields)

`first_name`, `last_name`, `full_name`, `state_student_id`, `email`, `dob`, `date_of_birth`, `address`, `phone`, `guardian_name`, `parent_name` — and more.

### Compliance

| Standard | Status |
|---|---|
| FERPA | ✅ Compliant |
| COPPA | ✅ Compliant |
| GDPR Right to Erasure | ✅ ZDR by default |

---

## Troubleshooting

| Problem | Fix |
|---|---|
| "Docker not found" | Install Docker Desktop |
| "Connection refused" | Wait 30s for startup, then retry |
| "DB not seeded" | Run `docker compose --profile seed up` |
| Empty results | Check text has at least 5 words |
| "Port already in use" | Change port in docker-compose.yml |

---

## Theoretical Frameworks Embedded

Every tool response includes framework annotations. The server references:

| Framework | What It Says |
|---|---|
| **Simple View of Reading** (Gough & Tunmer 1986) | Reading = Decoding × Language Comprehension |
| **Scarborough's Rope** (2001) | Reading weaves word recognition + language comprehension strands |
| **Five Pillars** (NRP 2000) | Phonemic Awareness, Phonics, Fluency, Vocabulary, Comprehension |
| **WWC Practice Guides** | Evidence-based recommendations from IES What Works Clearinghouse |
| **BEE Meta-Analyses** | Effect sizes from Johns Hopkins Best Evidence Encyclopedia |

---

## Next Steps

1. **Try it with Hooch** — run Lexile analysis on a chapter
2. **Pre-teach vocabulary** — generate Tier 2 word lists for each chapter
3. **Align with Georgia standards** — check GSE alignment
4. **Share with colleagues** — the repo is MIT-licensed, free for any educator

## Support

Issues and feature requests: https://github.com/kosburn0408/agentic-edu-skills/issues