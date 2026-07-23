# Example Workflows

Copy-paste-ready scenarios. Replace the sample data with your own.

---

## 1. Diagnose a Struggling Reader (2nd Grade)

> *Marcus scored 0.38 on his DIBELS Nonsense Word Fluency. His language comprehension is fine at 0.85. What do I do?*

```python
from src.core.router import query_sor_curriculum
from src.tools.diagnostics import evaluate_simple_view
from src.tools.remediation import get_instructional_remediation

# Step 1: Run the Simple View diagnostic
result = evaluate_simple_view(
    decoding=0.38,
    language_comprehension=0.85,
    grade="2nd"
)

print(f"Profile: {result.diagnostic.reading_profile}")
print(f"Deficit codes: {result.diagnostic.deficit_codes}")
# → Profile: dyslexia
# → Deficit codes: ['cvc_mixed', 'consonant_blends', 'consonant_digraphs']

# Step 2: Get remediation cards for each deficit
for code in result.diagnostic.deficit_codes:
    card = get_instructional_remediation(code, "2nd")
    print(card.to_markdown())
    print("\n---\n")

# Step 3: The remediation cards include:
# - Micro-PD (why this matters)
# - I Do / We Do / You Do script
# - Multisensory cue
# - Word chain
# - Corrective feedback
# - Connected text
```

**Output:** 3 printable cards. Print them. Bring to small group Monday at 8:15.

---

## 2. Check if a Book Is Decodable for Your Students

> *The curriculum says "Level D" but my kids can't read it. Why not?*

```python
from src.tools.decodability import verify_decodable_text

# Sample text from a "Level D" book
text = """Kate and Jake went to the lake.
They saw a big snake on a rock.
The snake slid into the water and swam away."""

# Check against a 1st grade scope (CVC + blends only, no silent-e yet)
result = verify_decodable_text(
    text=text,
    target_skill="cvc_mixed",
    grade_level="1st",
    mastered_phonemes=["short_a", "short_i", "short_o", "short_e", "short_u",
                       "l_blends", "r_blends", "s_blends", "final_blends"],
    taught_heart_words=["the", "a", "to", "and", "they", "saw", "into"]
)

print(f"Decodable: {result.decodable_pct}%")
print(f"Off-scope words: {result.off_scope_words}")
# → Decodable: 64%
# → Off-scope words: ['Kate', 'Jake', 'lake', 'snake', 'slid', 'away']
# These are ALL CVCe (silent-e) words — not yet taught!

print(f"Heart words used but not taught: {result.untaught_heart_words}")
# → ['water', 'swam']

print(f"Cueing flags: {result.cueing_flags}")
# → [] (good — no guessing strategies detected)
```

**Outcome:** The book uses silent-e patterns that haven't been taught yet. Either pre-teach CVCe, switch to a truly decodable text, or introduce these as heart words.

---

## 3. Align a Lesson to Georgia Standards

> *I'm teaching consonant blends to 1st graders. Which GSE standard does this hit?*

```python
from src.tools.standards import align_standards_case

result = align_standards_case(
    skill_description="Decode regularly spelled one-syllable words with consonant blends",
    state="GEORGIA",
    grade="1"
)

for match in result.matches:
    print(f"{match.code}: {match.description}")
    # → ELAGSE1RF3: Know and apply grade-level phonics and word analysis skills in decoding words

# Get the CASE GUID for your lesson plan or IEP
print(f"CASE CFItem GUID: {result.case_guid}")
# → Maps to the 1EdTech CASE framework for interoperability
```

---

## 4. Generate a Decodable Passage

> *My group has mastered short vowels and blends. I need a passage that uses ONLY those sounds.*

```python
from src.prompts.decodable_passage import build_decodable_passage

passage = build_decodable_passage(
    target_phoneme="consonant_blends",
    mastered_phonemes=["short_a", "short_i", "short_o", "short_e", "short_u",
                       "l_blends", "r_blends", "s_blends", "final_blends"],
    topic="animals",
    grade_level="1st"
)

print(passage.title)
# → "Frog on a Log"

print(passage.text)
# → "A frog sat on a log. The frog can jump and swim.
#    The frog is fast. Splash! The frog is in the pond."

print(f"Word count: {passage.word_count}")
print(f"Heart words: {passage.heart_words}")
# → ['the', 'is', 'a', 'in', 'and']
```

**Output:** A 22-word passage where EVERY word is decodable or a pre-taught heart word. No surprises.

---

## 5. Explain the Research Behind Phonics Instruction

> *My principal wants evidence that systematic phonics works. Give me citations with effect sizes.*

```python
from src.tools.diagnostics import search_evidence

result = search_evidence("systematic phonics instruction")

for paper in result.papers:
    print(f"{paper.title} ({paper.year})")
    print(f"  Effect size: d={paper.effect_size}")
    print(f"  Finding: {paper.finding[:120]}...")
    print(f"  Source: {paper.source}")
    print()

# → Ehri et al. (2001) — d=0.41, WWC
# → Archer & Hughes (2011) — d=0.58, WWC
# → Goodwin & Ahn (2013) — d=0.32, BEE
```

---

## 6. Classify Vocabulary for Pre-Teaching

> *I'm reading a science passage about river ecology. Which words should I pre-teach?*

```python
from src.tools.diagnostics import classify_vocabulary

text = """The tributary flows into the larger river.
Pollution from nearby farms can harm the ecosystem.
Scientists observe the water quality every month."""

result = classify_vocabulary(text)

print("Tier 2 words (pre-teach these):")
for word in result.word_details:
    if word.tier == 2:
        print(f"  {word.word} — academic, high utility across subjects")

print("\nTier 3 words (teach in context):")
for word in result.word_details:
    if word.tier == 3:
        print(f"  {word.word} — domain-specific to this unit")
# → Tier 2: observe, quality
# → Tier 3: tributary, pollution, ecosystem
```

---

## 7. Batch-Diagnose a Reading Group

> *I have 5 students at my intervention table. I need a remediation plan for each.*

```python
from src.tools.diagnostics import evaluate_simple_view
from src.tools.remediation import get_instructional_remediation

students = [
    {"name": "Marcus", "decoding": 0.38, "comprehension": 0.85, "grade": "2nd"},
    {"name": "Aisha", "decoding": 0.55, "comprehension": 0.60, "grade": "2nd"},
    {"name": "Luis", "decoding": 0.72, "comprehension": 0.80, "grade": "2nd"},
    {"name": "Emma", "decoding": 0.28, "comprehension": 0.70, "grade": "2nd"},
    {"name": "Jayden", "decoding": 0.45, "comprehension": 0.50, "grade": "2nd"},
]

for student in students:
    result = evaluate_simple_view(
        decoding=student["decoding"],
        language_comprehension=student["comprehension"],
        grade=student["grade"]
    )
    print(f"\n{student['name']}: {result.diagnostic.reading_profile}")
    print(f"  Needs: {', '.join(result.diagnostic.deficit_codes[:2])}")

# → Marcus: dyslexia → cvc_mixed, consonant_blends
# → Aisha: garden_variety → cvc_mixed, consonant_blends
# → Luis: typical → on track — enrichment
# → Emma: dyslexia → phoneme_segmentation, cvc_mixed
# → Jayden: garden_variety → cvc_mixed, consonant_blends
```

---

## Where to Go Next

- Full tool reference: [USER_GUIDE.md](USER_GUIDE.md)
- API documentation: See docstrings in `src/tools/` and `src/prompts/`
- Run the tests: `pytest tests/ -v`
- File an issue: [GitHub Issues](https://github.com/kosburn0408/sor-mcp-server/issues)
