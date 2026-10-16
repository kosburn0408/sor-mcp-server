"""Database seed script for Science of Reading evidence & standards repository.

Populates DuckDB database with:
- Theoretical frameworks (Simple View, Scarborough's Rope, NRP, Active View)
- Research sources; effect sizes only where checked against the source
- Academic standards aligned via Common Good Learning Tools Satchel Rosetta (CASE® format)
- Tiered vocabulary corpus (Tier 1/2/3)
- Evidence-based reading assessments (DIBELS, Acadience, MAP)
"""

from __future__ import annotations

from pathlib import Path
import sys
from typing import Any

# Ensure repository root is on Python path
repo_root = Path(__file__).resolve().parent.parent
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

import duckdb

import db.database as _database
from db.database import SCHEMA_PATH, get_db_path

_TABLES = (
    "theoretical_frameworks",
    "research_papers",
    "vocabulary_corpus",
    "standards",
    "assessments",
)


def seed_database(db_path: Path | str | None = None) -> Any:
    """Create the schema and seed DuckDB with frameworks, research, vocabulary and standards.

    Always opens its own read-write connection (the shared connection used by the tools is
    read-only), rebuilds the tables from schema.sql so schema upgrades apply, and then resets
    the shared connection so tools see the new data.
    """
    path = str(db_path or get_db_path())
    if _database._connection is not None:
        try:
            _database._connection.close()
        except Exception:
            pass
        _database._connection = None

    conn = duckdb.connect(path)
    for table in _TABLES:
        conn.execute(f"DROP TABLE IF EXISTS {table}")
    conn.execute(SCHEMA_PATH.read_text(encoding="utf-8"))

    # Seed theoretical frameworks
    frameworks = [
        (
            1,
            "Simple View of Reading",
            "Gough & Tunmer",
            1986,
            "Reading Comprehension = Decoding (D) x Language Comprehension (LC). Both components are necessary; neither is sufficient alone.",
            "decoding, language_comprehension, reading_comprehension",
            "https://doi.org/10.1177/074193258600700104",
        ),
        (
            2,
            "Scarborough's Reading Rope",
            "Hollis Scarborough",
            2001,
            "Visualizes reading as interconnected strands: Word Recognition strands become automatic; Language Comprehension strands become increasingly strategic.",
            "phonological_awareness, decoding, sight_recognition, background_knowledge, vocabulary, language_structures, verbal_reasoning, literacy_knowledge",
            "https://www.readingrockets.org/topics/about-reading/articles/scarboroughs-reading-rope",
        ),
        (
            3,
            "National Reading Panel 5 Pillars",
            "NRP",
            2000,
            "Identifies 5 components of effective reading instruction. The Panel ran meta-analyses for phonemic awareness, phonics and guided oral reading; it ran none for vocabulary or text comprehension, so no single pooled effect size exists per pillar.",
            "phonemic_awareness, phonics, fluency, vocabulary, comprehension",
            "https://www.nichd.nih.gov/publications/pubs/nrp/findings",
        ),
        (
            4,
            "Active View of Reading",
            "Duke & Cartwright",
            2021,
            "Extends the Simple View by adding active self-regulation and bridging processes (for example reading fluency and vocabulary knowledge used in reading) that connect word recognition and language comprehension.",
            "word_recognition, language_comprehension, active_self_regulation, bridging_processes",
            "https://readingrockets.org/resources/resource-library/science-reading-progresses-communicating-advances-beyond-simple-view",
        ),
    ]
    conn.executemany(
        "INSERT INTO theoretical_frameworks VALUES (?, ?, ?, ?, ?, ?, ?)",
        frameworks,
    )

    # Seed research papers
    # (id, title, authors, year, framework, finding, effect_size, source, url, verification, notes)
    # Effect sizes are stored only when checked against the source. Everything else is NULL.
    papers = [
        (
            1,
            "Systematic Phonics Instruction Helps Students Learn to Read: Evidence from the National Reading Panel's Meta-Analysis",
            "Ehri, L. C., Nunes, S. R., Stahl, S. A., & Willows, D. M.",
            2001,
            "phonics",
            "Systematic phonics instruction had a moderate overall effect on reading outcomes (d = 0.41). Effects were larger when instruction began early (d = 0.55) than after first grade (d = 0.27).",
            0.41,
            "National Reading Panel / Review of Educational Research",
            "https://doi.org/10.3102/00346543071003393",
            "verified",
            "Checked against the journal abstract.",
        ),
        (
            2,
            "Phonemic Awareness Instruction Helps Children Learn to Read: Evidence from the National Reading Panel's Meta-Analysis",
            "Ehri, L. C., Nunes, S. R., Willows, D. M., Schuster, B. V., Yaghoub-Zadeh, Z., & Shanahan, T.",
            2001,
            "phonemic_awareness",
            "Immediately after training, phonemic awareness instruction showed effects of d = 0.86 on phonemic awareness, d = 0.53 on reading and d = 0.59 on spelling.",
            0.53,
            "National Reading Panel / Reading Research Quarterly",
            "https://doi.org/10.1598/RRQ.36.3.2",
            "verified",
            "d = 0.53 is the reading outcome. Checked against the NRP report chapter.",
        ),
        (
            3,
            "A Synthesis of Research on Effective Interventions for Building Reading Fluency with Elementary Students with Learning Disabilities",
            "Chard, D. J., Vaughn, S., & Tyler, B. J.",
            2002,
            "fluency",
            "Synthesis of 24 studies. Effective interventions included an explicit model of fluent reading, repeated reading of familiar text with corrective feedback, and performance criteria for moving to harder text. No pooled effect size is reported.",
            None,
            "Journal of Learning Disabilities",
            "https://doi.org/10.1177/00222194020350050101",
            "verified",
            "Study count and features checked against a summary of the article. The DOI was not re-checked.",
        ),
        (
            4,
            "The Effects of Vocabulary Intervention on Young Children's Word Learning: A Meta-Analysis",
            "Marulis, L. M., & Neuman, S. B.",
            2010,
            "vocabulary",
            "Overall effect of d = 0.88 on vocabulary measures for interventions with young children (pre-K and kindergarten focus). The meta-analysis does not isolate Tier 2 words.",
            0.88,
            "Review of Educational Research",
            "https://doi.org/10.3102/0034654310377087",
            "verified",
            "Checked against the abstract. An earlier version of this entry described the result as being about Tier 2 words and carried a wrong DOI.",
        ),
        (
            5,
            "Improving Reading Comprehension in Kindergarten Through 3rd Grade (WWC Practice Guide)",
            "Shanahan, T., et al.",
            2010,
            "comprehension",
            "WWC practice guide recommending explicit teaching of comprehension strategies. Practice guides report levels of evidence rather than pooled effect sizes.",
            None,
            "What Works Clearinghouse Practice Guide",
            "https://ies.ed.gov/ncee/wwc/PracticeGuide/14",
            "unverified",
            "Recommendation levels not re-checked. An earlier version listed d = 0.55, which practice guides do not report.",
        ),
        (
            6,
            "Decoding and Fluency: Foundation Skills for Struggling Older Readers",
            "Archer, A. L., Gleason, M. M., & Vachon, V. L.",
            2003,
            "phonics",
            "Practice-oriented article recommending instruction in decoding long words plus fluency practice such as repeated reading. It is not a meta-analysis and reports no pooled effect size.",
            None,
            "Learning Disability Quarterly",
            "https://doi.org/10.2307/1593592",
            "verified",
            "Title, authors and citation checked. An earlier version used a different title, a DOI that did not match, and d = 0.62.",
        ),
        (
            7,
            "Effective Beginning Reading Programs: A Best-Evidence Synthesis",
            "Slavin, R. E., Lake, C., Chambers, B., Cheung, A., & Davis, S.",
            2009,
            "foundational_skills",
            "Best-evidence synthesis of beginning reading programs. Specific effect sizes were not re-checked.",
            None,
            "Best Evidence Encyclopedia / Review of Educational Research",
            "https://www.bestevidence.org/reading/elem_read.htm",
            "unverified",
            "An earlier version listed d = 0.47 and a finding about cooperative learning that could not be traced to this source.",
        ),
        (
            8,
            "Foundational Skills to Support Reading for Understanding in Kindergarten Through 3rd Grade (WWC Practice Guide)",
            "Foorman, B., et al.",
            2016,
            "foundational_skills",
            "Evidence levels: teach students academic language skills (minimal evidence); develop awareness of the segments of sounds in speech and how they link to letters (strong); teach students to decode words, analyze word parts, and write and recognize words (strong); ensure that each student reads connected text every day (moderate). The guide recommends decodable words and texts and notes that non-decodable words essential to a text can be taught.",
            None,
            "What Works Clearinghouse Practice Guide",
            "https://www.galiteracycenter.org/s/wwc_foundationalreading_040717.pdf",
            "verified",
            "Recommendation levels checked against the guide text. The guide reports evidence levels, not pooled effect sizes.",
        ),
        (
            9,
            "The Science of Reading Progresses: Communicating Advances Beyond the Simple View of Reading",
            "Duke, N. K., & Cartwright, K. B.",
            2021,
            "simple_view",
            "Proposes the Active View of Reading, which adds active self-regulation and bridging processes to the Simple View. Argues that language comprehension work should not wait for decoding to be secure.",
            None,
            "Reading Research Quarterly",
            "https://readingrockets.org/resources/resource-library/science-reading-progresses-communicating-advances-beyond-simple-view",
            "unverified",
            "Title and authors confirmed from a Reading Rockets listing; the final claim paraphrases the article's argument and was not checked against the full text.",
        ),
        (
            10,
            "The Current State of the Evidence Examining the Effects of Orton-Gillingham Reading Interventions for Students With or at Risk for Word-Level Reading Disabilities",
            "Stevens, E. A., Austin, C., Moore, C., Scammacca, N., Boucher, A. N., & Vaughn, S.",
            2021,
            "phonics",
            "Meta-analysis found a positive average effect favoring Orton-Gillingham-based approaches, but not a statistically reliable one for phonological awareness, phonics, fluency or spelling, and no significant differences for vocabulary or comprehension. Multisensory components were not tested separately.",
            None,
            "Exceptional Children",
            "https://readingrockets.org/resources/resource-library/current-state-evidence-examining-effects-orton-gillingham-reading",
            "verified",
            "Checked against a summary of the abstract; the effect size was not reported there.",
        ),
    ]
    conn.executemany(
        "INSERT INTO research_papers VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        papers,
    )

    # Seed vocabulary corpus (Tier 1/2/3)
    vocab = [
        # Grade 1 - Tier 1
        ("dog", 1, 1, 100, True, "cvc"), ("cat", 1, 1, 100, True, "cvc"),
        ("run", 1, 1, 95, True, "cvc"), ("big", 1, 1, 95, True, "cvc"),
        ("red", 1, 1, 95, True, "cvc"), ("sun", 1, 1, 90, True, "cvc"),
        # Grade 1 - Tier 2
        ("describe", 1, 2, 30, False, "complex"), ("predict", 1, 2, 25, False, "complex"),
        ("compare", 1, 2, 25, False, "complex"), ("contrast", 1, 2, 20, False, "complex"),
        # Grade 1 - Tier 3
        ("habitat", 1, 3, 10, False, "complex"), ("syllable", 1, 3, 15, False, "complex"),
        # Grade 2 - Tier 1
        ("house", 2, 1, 80, False, "cvce"), ("water", 2, 1, 75, False, "complex"),
        ("friend", 2, 1, 70, False, "complex"), ("happy", 2, 1, 70, False, "complex"),
        # Grade 2 - Tier 2
        ("analyze", 2, 2, 20, False, "complex"), ("infer", 2, 2, 25, False, "complex"),
        ("sequence", 2, 2, 20, False, "complex"), ("conclude", 2, 2, 15, False, "complex"),
        # Grade 2 - Tier 3
        ("ecosystem", 2, 3, 8, False, "complex"), ("phoneme", 2, 3, 10, False, "complex"),
        ("grapheme", 2, 3, 10, False, "complex"),
        # Grade 3 - Tier 1
        ("beautiful", 3, 1, 40, False, "complex"), ("dangerous", 3, 1, 35, False, "complex"),
        ("mountain", 3, 1, 30, False, "complex"), ("weather", 3, 1, 30, False, "complex"),
        # Grade 3 - Tier 2
        ("evaluate", 3, 2, 20, False, "complex"), ("hypothesize", 3, 2, 15, False, "complex"),
        ("synthesize", 3, 2, 12, False, "complex"), ("substantiate", 3, 2, 8, False, "complex"),
        # Grade 3 - Tier 3
        ("etymology", 3, 3, 5, False, "complex"), ("semantic", 3, 3, 5, False, "complex"),
        ("prosody", 3, 3, 4, False, "complex"),
    ]
    conn.executemany(
        "INSERT INTO vocabulary_corpus VALUES (?, ?, ?, ?, ?, ?)",
        vocab,
    )

    # Seed standards (Common Good Learning Tools - Satchel Rosetta CASE® Exchange format)
    standards = [
        ("CCSS", "K", "ELA", "RF.K.2", "Demonstrate understanding of spoken words, syllables, and sounds (phonemes)", "phonemic_awareness"),
        ("CCSS", "K", "ELA", "RF.K.3", "Know and apply grade-level phonics and word analysis skills in decoding words", "phonics"),
        ("CCSS", "1", "ELA", "RF.1.2", "Demonstrate understanding of spoken words, syllables, and sounds (phonemes)", "phonemic_awareness"),
        ("CCSS", "1", "ELA", "RF.1.3", "Know and apply grade-level phonics and word analysis skills in decoding words", "phonics"),
        ("CCSS", "1", "ELA", "RF.1.4", "Read with sufficient accuracy and fluency to support comprehension", "fluency"),
        ("CCSS", "2", "ELA", "RF.2.3", "Know and apply grade-level phonics and word analysis skills in decoding words", "phonics"),
        ("CCSS", "2", "ELA", "RF.2.4", "Read with sufficient accuracy and fluency to support comprehension", "fluency"),
        ("CCSS", "2", "ELA", "L.2.4", "Determine or clarify the meaning of unknown and multiple-meaning words and phrases", "vocabulary"),
        ("CCSS", "3", "ELA", "RF.3.3", "Know and apply grade-level phonics and word analysis skills in decoding words", "phonics"),
        ("CCSS", "3", "ELA", "RF.3.4", "Read with sufficient accuracy and fluency to support comprehension", "fluency"),
        ("CCSS", "3", "ELA", "RL.3.1", "Ask and answer questions to demonstrate understanding of a text, referring explicitly to the text as the basis for the answers", "comprehension"),
        ("CCSS", "4", "ELA", "RF.4.4", "Read with sufficient accuracy and fluency to support comprehension", "fluency"),
        ("CCSS", "4", "ELA", "RL.4.2", "Determine a theme of a story, drama, or poem from details in the text; summarize the text", "comprehension"),
        ("CCSS", "4", "ELA", "L.4.4", "Determine or clarify the meaning of unknown and multiple-meaning words and phrases", "vocabulary"),
        ("CCSS", "5", "ELA", "RF.5.4", "Read with sufficient accuracy and fluency to support comprehension", "fluency"),
        ("CCSS", "5", "ELA", "RL.5.1", "Quote accurately from a text when explaining what the text says explicitly and when drawing inferences", "comprehension"),
        ("CCSS", "5", "ELA", "L.5.4", "Determine or clarify the meaning of unknown and multiple-meaning words and phrases", "vocabulary"),

        # Georgia Standards of Excellence (GSE)
        ("GA", "K", "ELA", "ELAGSEKRF2", "Demonstrate understanding of spoken words, syllables, and sounds (phonemes)", "phonemic_awareness"),
        ("GA", "K", "ELA", "ELAGSEKRF3", "Know and apply grade-level phonics and word analysis skills in decoding words", "phonics"),
        ("GA", "K", "ELA", "ELAGSEKRF4", "Read emergent-reader texts with purpose and understanding", "fluency"),
        ("GA", "1", "ELA", "ELAGSE1RF2", "Demonstrate understanding of spoken words, syllables, and sounds (phonemes)", "phonemic_awareness"),
        ("GA", "1", "ELA", "ELAGSE1RF3", "Know and apply grade-level phonics and word analysis skills in decoding words", "phonics"),
        ("GA", "1", "ELA", "ELAGSE1RF4", "Read with sufficient accuracy and fluency to support comprehension", "fluency"),
        ("GA", "2", "ELA", "ELAGSE2RF3", "Know and apply grade-level phonics and word analysis skills in decoding words", "phonics"),
        ("GA", "2", "ELA", "ELAGSE2RF4", "Read with sufficient accuracy and fluency to support comprehension", "fluency"),
        ("GA", "2", "ELA", "ELAGSE2L4", "Determine or clarify the meaning of unknown and multiple-meaning words and phrases", "vocabulary"),
        ("GA", "3", "ELA", "ELAGSE3RF3", "Know and apply grade-level phonics and word analysis skills in decoding words", "phonics"),
        ("GA", "3", "ELA", "ELAGSE3RF4", "Read with sufficient accuracy and fluency to support comprehension", "fluency"),

        # Texas TEKS
        ("TX", "K", "ELA", "110.2.b.2.A", "Demonstrate phonological awareness by identifying and producing rhyming words", "phonemic_awareness"),
        ("TX", "1", "ELA", "110.3.b.3.A", "Use a resource such as a picture dictionary or digital resource to find words", "vocabulary"),
        ("TX", "2", "ELA", "110.4.b.2.B", "Demonstrate and apply phonetic knowledge by decoding multisyllabic words", "phonics"),

        # Florida B.E.S.T.
        ("FL", "K", "ELA", "ELA.K.F.1.2", "Demonstrate phonological awareness", "phonemic_awareness"),
        ("FL", "1", "ELA", "ELA.1.F.1.3", "Use knowledge of grade-appropriate phonics and word analysis skills to decode words accurately", "phonics"),
        ("FL", "2", "ELA", "ELA.2.F.1.4", "Read grade-level texts with accuracy, automaticity, and appropriate prosody or expression", "fluency"),

        # California Common Core State Standards (CCSS-CA / Satchel Rosetta CASE®)
        ("CA", "K", "ELA", "CA.CCSS.ELA-Literacy.RF.K.2", "Demonstrate understanding of spoken words, syllables, and sounds (phonemes)", "phonemic_awareness"),
        ("CA", "1", "ELA", "CA.CCSS.ELA-Literacy.RF.1.3", "Know and apply grade-level phonics and word analysis skills in decoding words", "phonics"),
        ("CA", "2", "ELA", "CA.CCSS.ELA-Literacy.RF.2.4", "Read with sufficient accuracy and fluency to support comprehension", "fluency"),

        # New York Next Generation Learning Standards (NY)
        ("NY", "K", "ELA", "NY.KRF2", "Demonstrate understanding of spoken words, syllables, and sounds (phonemes)", "phonemic_awareness"),
        ("NY", "1", "ELA", "NY.1RF3", "Know and apply grade-level phonics and word analysis skills in decoding words", "phonics"),
        ("NY", "2", "ELA", "NY.2RF4", "Read grade-level text with sufficient accuracy and fluency to support comprehension", "fluency"),

        # North Carolina Standard Course of Study (NC)
        ("NC", "1", "ELA", "NC.1.RF.3", "Know and apply grade-level phonics and word analysis skills in decoding words", "phonics"),
        ("NC", "2", "ELA", "NC.2.RF.4", "Read with sufficient accuracy and fluency to support comprehension", "fluency"),

        # Ohio Learning Standards (OH)
        ("OH", "1", "ELA", "OH.RF.1.3", "Know and apply grade-level phonics and word analysis skills in decoding words", "phonics"),
        ("OH", "2", "ELA", "OH.RF.2.4", "Read with sufficient accuracy and fluency to support comprehension", "fluency"),

        # Pennsylvania Academic Standards (PA)
        ("PA", "1", "ELA", "CC.1.1.1.D", "Know and apply grade-level phonics and word analysis skills in decoding words", "phonics"),
        ("PA", "2", "ELA", "CC.1.1.2.E", "Read with accuracy and fluency to support comprehension", "fluency"),

        # Virginia Standards of Learning (VA)
        ("VA", "1", "ELA", "VA.SOL.1.6", "The student will apply phonetic principles to read and spell words", "phonics"),
        ("VA", "2", "ELA", "VA.SOL.2.7", "The student will expand vocabulary and use word study strategies", "vocabulary"),

        # Illinois Learning Standards (IL)
        ("IL", "1", "ELA", "IL.CCSS.RF.1.3", "Know and apply grade-level phonics and word analysis skills in decoding words", "phonics"),
        ("IL", "2", "ELA", "IL.CCSS.RF.2.4", "Read with sufficient accuracy and fluency to support comprehension", "fluency"),
    ]
    conn.executemany(
        "INSERT INTO standards VALUES (?, ?, ?, ?, ?, ?)",
        standards,
    )

    # Seed assessments
    assessments = [
        (1, "DIBELS 8th Edition", "screener", "K-8", "phonemic_awareness, phonics, fluency, comprehension", "1:1, 1-3 minutes per measure", "Benchmark cut points, risk levels", "https://dibels.uoregon.edu/"),
        (2, "Acadience Reading", "screener", "K-6", "phonemic_awareness, phonics, fluency, comprehension", "1:1, 3-5 minutes per measure", "Benchmark goals per grade", "https://acadiencelearning.org/"),
        (3, "NWEA MAP Reading Fluency", "screener", "K-5", "phonemic_awareness, phonics, fluency, comprehension", "Computer-based, ~20 min", "RIT scores, Lexile", "https://www.nwea.org/map-reading-fluency/"),
        (4, "AIMSweb Plus", "screener", "K-8", "phonemic_awareness, phonics, fluency, comprehension", "1:1 or group, 1-4 minutes", "National percentiles, rate of improvement", "https://www.pearsonassessments.com/aimsweb.html"),
        (5, "CORE Phonics Survey", "diagnostic", "K-12", "phonics, phonemic_awareness", "1:1, 10-15 minutes", "Mastery levels per skill", "https://www.corelearn.com/"),
        (6, "PAST (Phonological Awareness Screening Test)", "diagnostic", "K-3", "phonemic_awareness", "1:1, 5-10 minutes", "Stage of phonological awareness development", "https://www.thepasttest.com/"),
        (7, "QRI-6 (Qualitative Reading Inventory)", "diagnostic", "K-12", "fluency, comprehension, vocabulary", "1:1, 20-40 minutes", "Independent/instructional/frustration levels", "https://www.pearson.com/"),
        (8, "easyCBM", "progress_monitoring", "K-8", "phonemic_awareness, phonics, fluency, comprehension, vocabulary", "1:1 or group, 1-5 minutes", "Percentile ranks, rate of improvement", "https://www.easycbm.com/"),
        (9, "FastBridge", "progress_monitoring", "K-12", "phonemic_awareness, phonics, fluency, comprehension, vocabulary", "Computer-based, 5-20 min", "National norms, growth rates", "https://www.fastbridge.org/"),
        (10, "i-Ready Diagnostic", "diagnostic", "K-12", "phonemic_awareness, phonics, fluency, comprehension, vocabulary", "Computer-adaptive, 45-90 min", "Scale scores, grade-level placements, Lexile", "https://www.curriculumassociates.com/i-ready"),
        (11, "Star Reading", "screener", "K-12", "comprehension, vocabulary", "Computer-adaptive, 15-20 min", "Scaled scores, percentile ranks, Lexile", "https://www.renaissance.com/products/star-reading/"),
    ]
    conn.executemany(
        "INSERT INTO assessments VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        assessments,
    )

    conn.commit()
    print(f"Database seeded successfully at {path}")
    print(f"  Frameworks: {conn.execute('SELECT count(*) FROM theoretical_frameworks').fetchone()[0]}")
    print(f"  Research papers: {conn.execute('SELECT count(*) FROM research_papers').fetchone()[0]}")
    print(f"  Vocabulary entries: {conn.execute('SELECT count(*) FROM vocabulary_corpus').fetchone()[0]}")
    print(f"  Standards: {conn.execute('SELECT count(*) FROM standards').fetchone()[0]}")
    print(f"  Assessments: {conn.execute('SELECT count(*) FROM assessments').fetchone()[0]}")

    return conn


if __name__ == "__main__":
    seed_database()
