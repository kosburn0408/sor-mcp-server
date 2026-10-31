# A Scope-Aware Decodability Engine: Methods Note

**Draft — sor-mcp-server, `src/engine/`**
Status: methods description for review. The validation described at the end is planned and has not yet been run; no validation results are reported here.

## 1. The problem: decodability is relative to what has been taught

Whether a word is "decodable" is not a property of the word alone. *Cake* is decodable for a child who has been taught the silent-e pattern and opaque for a child who has only been taught short vowels. Tools that report a single decodability percentage for a passage — using a fixed notion of phonetic regularity, or a readability formula — answer a question no teacher actually asked. The question a teacher asks is narrower and more useful: **can my students, given the grapheme-phoneme correspondences (GPCs) and heart words taught through this week's unit, read this text?**

That is the question this engine answers. Its design follows the instructional logic of systematic phonics — the approach supported by the National Reading Panel's meta-analysis (Ehri, Nunes, Stahl & Willows, 2001, seeded in the project's evidence database) — and it sits inside the Simple View of Reading framing (Gough & Tunmer, 1986, likewise seeded): decoding is one component of reading, and this engine measures only whether print is accessible, not whether a student comprehends it.

## 2. Method

### 2.1 Pronunciations from the CMU Pronouncing Dictionary

Each word in a submitted passage is looked up in the CMU Pronouncing Dictionary (via the BSD-licensed `cmudict` package), which provides one or more ARPAbet pronunciations per word. Pronunciations are normalized before use: stress digits are stripped, an unstressed `AH0` becomes a distinct schwa phoneme (`AX`), and `ER` variants are collapsed to a single r-controlled phoneme. Keeping schwa distinct matters: a schwa can only be "decoded" once schwa has been taught, which the normalization enforces rather than assumes.

A word counts as decodable if **any** of its listed pronunciations can be spelled with taught patterns. Two words are exceptions: for *the* and *a*, only the primary dictionary entry is used, because their alternate citation forms ("thee", "ay") would make an ordinarily irregular pronunciation look decodable.

### 2.2 The GPC catalog

The catalog (`src/engine/gpc.py`) holds 98 grapheme-phoneme correspondences. Each entry gives an id, a grapheme, the phoneme sequence(s) it can represent, a teacher-facing label and example, and optional positional constraints: word-initial only, word-final only, or valid only before particular letters (the mechanism behind soft c/g). An entry is *taught* when its id appears in the active scope & sequence; the same physical pattern can therefore be decodable in one classroom and not-yet-decodable in another.

### 2.3 Alignment search (cost 0/1 dynamic programming)

For each word, the engine searches for an alignment: a way to segment the spelling into graphemes whose sounds reproduce the dictionary pronunciation exactly. The search is a dynamic program over (letter position, phoneme position) pairs. Every GPC used in an alignment costs **0 if taught, 1 if untaught**, so the cheapest alignment is the one that leans most on what students have been taught; ties are broken in favor of longer graphemes (reading *sh* as one unit rather than *s* + *h*). If the cheapest alignment costs 0, the word is decodable *now*; if it costs more than 0, the specific untaught GPCs in that alignment are the missing patterns, and the tool names them — which is what makes the output actionable ("this text needs vowel teams, which arrive in unit 9") rather than a bare percentage.

On top of the plain catalog, the candidate generator applies positional pattern rules:

- **Silent-e (VCe):** a vowel + single consonant + final *e* (also before *-s* / *-d*) yields the long vowel sound, charged to the `vce_<vowel>` GPC.
- **Open syllables:** a vowel ending a word, or a vowel + one consonant + vowel (VCV) sequence, can carry its long sound (`open_syllable`).
- **Schwa:** a vowel letter may map to schwa only in multisyllabic words (see §4).
- **Final -d after silent-e** (*baked*, *smiled*) may realize the `-ed` suffix as /t/ or /d/ (`suffix_ed`).

### 2.4 Word statuses and passage scores

Every analyzed word receives exactly one status:

| Status | Meaning |
|---|---|
| `decodable` | Cheapest alignment costs 0 — every pattern has been taught. |
| `heart_word` | Not fully decodable, but the word has been taught as a heart word by this point in the scope. |
| `not_yet_decodable` | An alignment exists using untaught patterns; the missing patterns are listed. |
| `irregular` | No alignment exists using any catalogued GPC, and the word has not been taught as a heart word — pre-teach it or replace it. |
| `not_in_dictionary` | No pronunciation found (names, rare words) — flagged for teacher review rather than guessed. |

At passage level the engine reports `decodable_pct`, `accessible_pct` (decodable + taught heart words), and `meets_target`, comparing accessible percentage against a configurable target (default 90%; an optional stricter floor on fully-decodable percentage, `min_decodable_pct`, can also be set). Thresholds vary by program and state, so the target is an input, not a constant baked into the method.

## 3. Scope & sequence inputs

Grade and unit resolve to a **cumulative** taught set: grade 1 unit 3 includes all of kindergarten plus grade 1 units 1–3 — GPCs and heart words alike. Two sources of scope are supported:

- **A default sequence** ships with the engine. It follows the general order common to structured-literacy programs (single consonants and short vowels → digraphs → silent-e → r-controlled vowels and vowel teams → multisyllabic patterns) and is explicitly **illustrative**: it is not any specific published program, and results are only as meaningful as the scope they are checked against.
- **A district's own sequence** can be supplied as a JSON file (`SOR_SCOPE_PATH`) in the same shape, or generated from a spreadsheet of the program's units with `scripts/build_scope.py`, which accepts teacher notation (`m; a; sh; a_e; -ed; open syllable`) as well as GPC ids, and warns about ambiguous spellings and patterns introduced twice. Unknown GPC ids in a custom scope file are rejected at load time.

## 4. Known limitations

- **Dialect.** Dictionary pronunciations reflect General American English (a limitation stated in the project README). Pronunciations that differ regionally can change an alignment's cost.
- **Dictionary coverage.** Words missing from the CMU dictionary — proper names, rare or invented words — are reported as `not_in_dictionary` for teacher review; the engine never invents a pronunciation. Coverage, not pattern logic, is the usual reason a passage scores oddly, and the status makes that visible instead of silently misclassifying the word.
- **The default sequence is illustrative.** Checking a passage against the shipped default when a class follows a specific program can mislabel words in both directions. District scope files are the intended use for consequential decisions.
- **Schwa handling is deliberately conservative.** A vowel letter may be charged to the `schwa` GPC only in multisyllabic words. One-syllable schwa words (*the*, *a*, *was*) therefore stay heart words until taught as such, rather than becoming "decodable" the moment schwa is introduced for multisyllabic words — a modeling choice a reviewer could reasonably contest, documented here so it can be.
- **Any-pronunciation rule.** Because a word passes if *any* dictionary pronunciation aligns at cost 0, heteronyms (*read*, *wind*) are judged by their most teachable reading. The *the*/*a* exception narrows this for the two highest-frequency words, but the rule is a known source of false "decodable" verdicts for other heteronyms.

## 5. Validation plan: literacy-coach review

The engine's verdicts have not yet been validated against expert judgment. The repository ships a workflow for exactly that (`scripts/coach_review.py`), in three steps:

1. **Prepare.** Real passages (CSV: passage id, grade, unit, text) are run through the engine to produce a review sheet — one row per distinct word per passage, with the tool's status, grapheme breakdown, and missing patterns, and blank columns for the coach. The review should be run with the district's own scope file (`SOR_SCOPE_PATH`) so the coach judges against the program they actually teach.
2. **Review.** A literacy coach marks each word agree/disagree and, on disagreement, supplies the correct status and a note (e.g., "taught as a heart word in lesson 22").
3. **Ingest.** The completed sheet is summarized into agreement rates by status, and **every disagreement is written into `tests/fixtures/coach_cases.json`**, which the test suite (`tests/test_coach_cases.py`) then checks against the engine — so a fix for one disagreement cannot silently regress another, and the corpus of expert-judged words grows with each review round.

No agreement rates are reported in this note: the workflow has been built and tested mechanically, but no coach review has been run yet. The honest first validation milestone is a completed review round on passages from a single adopted program, with disagreements triaged into dictionary gaps, scope-file errors, and genuine engine errors before any rate is quoted.

---

*Sources cited are limited to the project's seeded evidence base (`db/seed.py`): Ehri, L. C., Nunes, S. R., Stahl, S. A., & Willows, D. M. (2001), National Reading Panel meta-analysis of systematic phonics instruction; Gough, P. B., & Tunmer, W. E. (1986), the Simple View of Reading; Scarborough, H. (2001), the Reading Rope. The CMU Pronouncing Dictionary is used under its BSD license.*
