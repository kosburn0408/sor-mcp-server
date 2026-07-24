# Example Workflows

**For developers and tech-savvy educators** who have cloned the repository and set up the Python environment.

Each example below assumes:

```bash
# Clone repository and install dependencies:
git clone https://github.com/kosburn0408/sor-mcp-server.git
cd sor-mcp-server
pip install -r requirements.txt
python3 server.py --seed-only
```

Then run any example with `python3` — replace the sample data with your own.

---

## 1. Diagnose a Struggling Reader (2nd Grade)

> *Marcus scored 0.38 on his DIBELS Nonsense Word Fluency. His language comprehension is fine at 0.85. What do I do?*

```python
from src.tools.diagnostics import evaluate_simple_view
from src.tools.remediation import get_instructional_remediation

# Step 1: Run the Simple View diagnostic
result = evaluate_simple_view(
    decoding_score=0.38,
    language_comp_score=0.85,
    student_grade="2"
)

print(f"Profile: {result['diagnostic']['reading_profile']}")
print(f"Deficit codes: {result['diagnostic']['deficit_codes']}")
# → Profile: dyslexia
# → Deficit codes: ['cvc_mixed', 'consonant_blends', 'consonant_digraphs']

# Step 2: Get remediation cards for each deficit
for code in result['diagnostic']['deficit_codes']:
    card = get_instructional_remediation(code, "2")
    if "remediation_card" in card:
        print(card["remediation_card"].to_markdown())
```

---

## 2. Check if a Book Is Decodable for Your Students

> *Check text decodability against phonics patterns.*

```python
from src.tools.decodability import check_decodability

text = "The cat sat on the mat. The man had a hat."

result = check_decodability(text=text, grade_level="1")

print(f"Decodable: {result['decodable_pct']}%")
print(f"Instructional level: {result['instructional_level']}")
print(f"Off-scope words: {result['off_scope_words']}")
print(f"Heart words: {result['heart_words']}")
```

---

## 3. Align a Lesson to Standards

> *I'm teaching consonant blends to 1st graders. Which standard does this hit?*

```python
from src.tools.evidence import align_standards

result = align_standards(
    description="Decode regularly spelled one-syllable words with consonant blends",
    state="GA",
    grade="1"
)

for match in result["matches"]:
    print(f"{match['code']}: {match['description']}")
```

---

## 4. Search Evidence Base

> *My principal wants evidence that systematic phonics works. Give me citations with effect sizes.*

```python
from src.tools.evidence import search_evidence

result = search_evidence("phonics instruction")

for paper in result["papers"]:
    print(f"{paper['title']} ({paper['year']})")
    print(f"  Effect size: d={paper['effect_size']}")
    print(f"  Finding: {paper['finding']}")
    print(f"  Source: {paper['source']}")
    print()
```

---

## 5. Classify Vocabulary for Pre-Teaching

```python
from src.tools.vocabulary import classify_vocabulary

text = """The tributary flows into the larger river.
Pollution from nearby farms can harm the ecosystem.
Scientists observe the water quality every month."""

result = classify_vocabulary(text)

print("Tier 2 words:", result["tier_2_words"])
print("Tier 3 words:", result["tier_3_words"])
```

---

## Where to Go Next

- Full user guide: [USER_GUIDE.md](../USER_GUIDE.md)
- Main documentation: [README.md](../README.md)
- Run the tests: `python3 -m pytest`
