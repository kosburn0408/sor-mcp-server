"""Seed the DuckDB database with Science of Reading research data."""

import duckdb
import os
from pathlib import Path

DB_DIR = Path(__file__).parent
SCHEMA_PATH = DB_DIR / "schema.sql"


def get_db_path() -> str:
    """Get database path from environment or default."""
    return os.environ.get("SOR_DB_PATH", str(DB_DIR / "sor_evidence.duckdb"))


def seed_database(db_path: str | None = None) -> duckdb.DuckDBPyConnection:
    """Create schema and seed with evidence-based research data."""
    conn = duckdb.connect(db_path or get_db_path())

    # Create schema
    conn.execute(SCHEMA_PATH.read_text())

    # Seed theoretical frameworks
    frameworks = [
        (1, "Simple View of Reading", "Gough & Tunmer", 1986,
         "Reading comprehension is the product of decoding (word recognition) and linguistic comprehension. D x LC = RC.",
         "decoding, linguistic_comprehension",
         "https://doi.org/10.1177/074193258600700104"),
        (2, "Scarborough's Reading Rope", "Scarborough, H.S.", 2001,
         "Reading is composed of interconnected strands across Language Comprehension and Word Recognition, woven together into skilled reading.",
         "background_knowledge, vocabulary, language_structures, verbal_reasoning, literacy_knowledge, phonological_awareness, decoding, sight_recognition",
         "https://www.readingrockets.org/topics/about-reading/articles/scarboroughs-reading-rope"),
        (3, "National Reading Panel Report", "National Reading Panel", 2000,
         "Identified five essential components of reading instruction based on meta-analysis of empirical research.",
         "phonemic_awareness, phonics, fluency, vocabulary, comprehension",
         "https://www.nichd.nih.gov/publications/pubs/nrp/smallbook"),
        (4, "Foundational Skills to Support Reading for Understanding (WWC Practice Guide)", "Foorman et al.", 2016,
         "Four recommendations for teaching foundational reading skills to K-3 students based on WWC systematic review.",
         "phonemic_awareness, phonics, fluency",
         "https://ies.ed.gov/ncee/wwc/PracticeGuide/21"),
        (5, "Improving Reading Comprehension (WWC Practice Guide)", "Shanahan et al.", 2010,
         "Five recommendations for improving reading comprehension in K-3 based on WWC systematic review.",
         "comprehension, vocabulary, text_structure",
         "https://ies.ed.gov/ncee/wwc/PracticeGuide/14"),
        (6, "Four-Part Processing Model", "Seidenberg & McClelland", 1989,
         "Word recognition involves four interconnected processors: phonological, orthographic, meaning, and context.",
         "phonological, orthographic, meaning, context",
         "https://doi.org/10.1037/0033-295X.96.4.523"),
    ]
    conn.executemany(
        "INSERT OR IGNORE INTO theoretical_frameworks VALUES (?, ?, ?, ?, ?, ?, ?)",
        frameworks,
    )

    # Seed research papers
    papers = [
        (1, "Phonemic Awareness Instruction Helps Children Learn to Read", "Ehri et al.", 2001,
         "phonemic_awareness",
         "Explicit phonemic awareness instruction has a moderate to large effect on reading outcomes (d=0.53 to d=0.86). Instruction is most effective when focused on 1-2 PA skills.",
         0.70, "WWC", "https://doi.org/10.1598/RRQ.36.3.2"),
        (2, "Systematic Phonics Instruction Helps Students Learn to Read", "Ehri et al.", 2001,
         "phonics",
         "Systematic phonics instruction has a moderate effect on reading outcomes (d=0.41). Effects are larger when instruction begins in K-1 rather than later.",
         0.41, "WWC", "https://doi.org/10.3102/00346543071003393"),
        (3, "Repeated Reading Interventions for Students with Learning Disabilities", "Chard et al.", 2002,
         "fluency",
         "Repeated reading with corrective feedback has a large effect on reading fluency (d=0.68). Peer-assisted and adult-led models both show strong effects.",
         0.68, "WWC", "https://doi.org/10.1177/00222194020350050101"),
        (4, "Vocabulary Instruction in Early Reading", "Coyne et al.", 2007,
         "vocabulary",
         "Embedded vocabulary instruction (teaching word meanings during storybook reading) shows moderate effects (d=0.47). Extended instruction with multiple exposures is more effective.",
         0.47, "WWC", "https://doi.org/10.1086/519491"),
        (5, "Reciprocal Teaching of Comprehension Strategies", "Rosenshine & Meister", 1994,
         "comprehension",
         "Reciprocal teaching (predicting, questioning, clarifying, summarizing) has a moderate to large effect on comprehension (d=0.32 to 0.88).",
         0.60, "BEE", "https://doi.org/10.3102/00346543064004479"),
        (6, "Phonological Awareness Training", "Bus & van IJzendoorn", 1999,
         "phonemic_awareness",
         "Phonological awareness training has a large effect on reading (d=0.73). Combined with letter knowledge instruction, effects increase substantially.",
         0.73, "BEE", "https://doi.org/10.2307/1161921"),
        (7, "Explicit Instruction: Effective and Efficient Teaching", "Archer & Hughes", 2011,
         "phonics",
         "Explicit instruction model (I do, we do, you do) is highly effective for teaching foundational reading skills. Clear modeling, guided practice, and independent practice are key.",
         0.58, "WWC", "https://explicitinstruction.org/"),
        (8, "Reading Fluency: Critical Issues for Struggling Readers", "Torgesen & Hudson", 2006,
         "fluency",
         "Oral reading fluency in 1st grade predicts reading comprehension in later grades. Fluency interventions should target both accuracy and automaticity.",
         0.55, "WWC", "https://doi.org/10.1007/0-387-28338-8_6"),
        (9, "Robust Vocabulary Instruction", "Beck, McKeown & Kucan", 2013,
         "vocabulary",
         "Three-tier vocabulary framework: Tier 1 (basic), Tier 2 (high-utility academic), Tier 3 (domain-specific). Rich instruction should focus on Tier 2 words with multiple exposures.",
         0.52, "BEE", "https://doi.org/10.1002/trtr.2029"),
        (10, "Close Reading and Comprehension", "Fisher & Frey", 2012,
         "comprehension",
         "Close reading with text-dependent questions improves comprehension. Students benefit from repeated readings with different purposes at each pass.",
         0.45, "WWC", "https://doi.org/10.1002/TRTR.01117"),
        (11, "The Simple View of Reading: A Meta-Analysis", "Hjetland et al.", 2020,
         "simple_view",
         "Meta-analysis of 64 studies confirms the Simple View: decoding and language comprehension are independent predictors of reading comprehension. Combined, they explain 50-60% of variance in reading comprehension.",
         0.75, "BEE", "https://doi.org/10.1080/10888438.2020.1805594"),
        (12, "Morphological Awareness and Reading", "Goodwin & Ahn", 2013,
         "phonics",
         "Morphological awareness instruction has a moderate effect on reading outcomes (d=0.32). Effects are stronger for struggling readers (d=0.41).",
         0.32, "BEE", "https://doi.org/10.1080/19345747.2012.744202"),
    ]
    conn.executemany(
        "INSERT OR IGNORE INTO research_papers VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
        papers,
    )

    # Seed vocabulary corpus (Tier 1, 2, 3 words by grade level)
    vocab = [
        # Kindergarten - Tier 1 (high-frequency, decodable)
        ("cat", 0, 1, 100, True, "CVC"), ("dog", 0, 1, 100, True, "CVC"),
        ("big", 0, 1, 90, True, "CVC"), ("red", 0, 1, 85, True, "CVC"),
        ("run", 0, 1, 80, True, "CVC"), ("sit", 0, 1, 80, True, "CVC"),
        ("hat", 0, 1, 75, True, "CVC"), ("sun", 0, 1, 70, True, "CVC"),
        ("pig", 0, 1, 65, True, "CVC"), ("log", 0, 1, 60, True, "CVC"),
        # Kindergarten - Tier 2 (academic, some decodable)
        ("compare", 0, 2, 15, False, "complex"), ("observe", 0, 2, 12, False, "complex"),
        ("describe", 0, 2, 10, False, "complex"), ("predict", 0, 2, 8, False, "complex"),
        # Kindergarten - Tier 3 (domain-specific)
        ("phoneme", 0, 3, 5, False, "complex"), ("blend", 0, 3, 5, True, "CCVCC"),
        ("segment", 0, 3, 4, False, "complex"),

        # Grade 1 - Tier 1
        ("shark", 1, 1, 80, True, "CVC"), ("chip", 1, 1, 75, True, "CVC"),
        ("shop", 1, 1, 70, True, "CVC"), ("thin", 1, 1, 65, True, "CVC"),
        ("ring", 1, 1, 60, True, "CVCC"), ("sing", 1, 1, 60, True, "CVCC"),
        ("jump", 1, 1, 55, True, "CVCC"), ("milk", 1, 1, 50, True, "CVCC"),
        ("lake", 1, 1, 55, True, "CVCe"), ("cake", 1, 1, 50, True, "CVCe"),
        # Grade 1 - Tier 2
        ("explain", 1, 2, 15, False, "complex"), ("identify", 1, 2, 12, False, "complex"),
        ("sequence", 1, 2, 10, False, "complex"), ("organize", 1, 2, 8, False, "complex"),
        # Grade 1 - Tier 3
        ("decodable", 1, 3, 5, False, "complex"), ("syllable", 1, 3, 5, False, "complex"),
        ("digraph", 1, 3, 4, False, "complex"),

        # Grade 2 - Tier 1
        ("kitchen", 2, 1, 50, True, "CVC"), ("garden", 2, 1, 45, True, "CVC"),
        ("bottle", 2, 1, 40, False, "CVC"), ("candle", 2, 1, 35, False, "CCVCC"),
        ("purple", 2, 1, 30, False, "CVCe"), ("circle", 2, 1, 28, False, "complex"),
        # Grade 2 - Tier 2
        ("analyze", 2, 2, 20, False, "complex"), ("classify", 2, 2, 18, False, "complex"),
        ("evidence", 2, 2, 15, False, "complex"), ("interpret", 2, 2, 12, False, "complex"),
        # Grade 2 - Tier 3
        ("phonological", 2, 3, 6, False, "complex"), ("orthographic", 2, 3, 4, False, "complex"),
        ("morpheme", 2, 3, 5, False, "complex"),

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
        "INSERT OR IGNORE INTO vocabulary_corpus VALUES (?, ?, ?, ?, ?, ?)",
        vocab,
    )

    # Seed standards (CASE framework - select state examples)
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
        ("TEXAS", "K", "ELA", "110.2.b.2.A", "Demonstrate phonological awareness by identifying and producing rhyming words", "phonemic_awareness"),
        ("TEXAS", "1", "ELA", "110.3.b.3.A", "Use a resource such as a picture dictionary or digital resource to find words", "vocabulary"),
        ("TEXAS", "2", "ELA", "110.4.b.2.B", "Demonstrate and apply phonetic knowledge by decoding multisyllabic words", "phonics"),
        ("FLORIDA", "K", "ELA", "ELA.K.F.1.2", "Demonstrate phonological awareness", "phonemic_awareness"),
        ("FLORIDA", "1", "ELA", "ELA.1.F.1.3", "Use knowledge of grade-appropriate phonics and word analysis skills to decode words accurately", "phonics"),
        ("FLORIDA", "2", "ELA", "ELA.2.F.1.4", "Read grade-level texts with accuracy, automaticity, and appropriate prosody or expression", "fluency"),
        ("NY", "K", "ELA", "KRF2", "Demonstrate understanding of spoken words, syllables, and sounds (phonemes)", "phonemic_awareness"),
        ("NY", "1", "ELA", "1RF3", "Know and apply phonics and word analysis skills in decoding words", "phonics"),
        # Georgia Standards of Excellence (GSE) — ELA K-5
        ("GEORGIA", "K", "ELA", "ELAGSEKRF2", "Demonstrate understanding of spoken words, syllables, and sounds (phonemes)", "phonemic_awareness"),
        ("GEORGIA", "K", "ELA", "ELAGSEKRF3", "Know and apply grade-level phonics and word analysis skills in decoding words", "phonics"),
        ("GEORGIA", "K", "ELA", "ELAGSEKRF4", "Read emergent-reader texts with purpose and understanding", "fluency"),
        ("GEORGIA", "1", "ELA", "ELAGSE1RF2", "Demonstrate understanding of spoken words, syllables, and sounds (phonemes)", "phonemic_awareness"),
        ("GEORGIA", "1", "ELA", "ELAGSE1RF3", "Know and apply grade-level phonics and word analysis skills in decoding words", "phonics"),
        ("GEORGIA", "1", "ELA", "ELAGSE1RF4", "Read with sufficient accuracy and fluency to support comprehension", "fluency"),
        ("GEORGIA", "2", "ELA", "ELAGSE2RF3", "Know and apply grade-level phonics and word analysis skills in decoding words", "phonics"),
        ("GEORGIA", "2", "ELA", "ELAGSE2RF4", "Read with sufficient accuracy and fluency to support comprehension", "fluency"),
        ("GEORGIA", "2", "ELA", "ELAGSE2L4", "Determine or clarify the meaning of unknown and multiple-meaning words and phrases", "vocabulary"),
        ("GEORGIA", "3", "ELA", "ELAGSE3RF3", "Know and apply grade-level phonics and word analysis skills in decoding words", "phonics"),
        ("GEORGIA", "3", "ELA", "ELAGSE3RF4", "Read with sufficient accuracy and fluency to support comprehension", "fluency"),
        ("GEORGIA", "3", "ELA", "ELAGSE3RL1", "Ask and answer questions to demonstrate understanding of a text, referring explicitly to the text as the basis for the answers", "comprehension"),
        ("GEORGIA", "4", "ELA", "ELAGSE4RF4", "Read with sufficient accuracy and fluency to support comprehension", "fluency"),
        ("GEORGIA", "4", "ELA", "ELAGSE4RL2", "Determine a theme of a story, drama, or poem from details in the text; summarize the text", "comprehension"),
        ("GEORGIA", "4", "ELA", "ELAGSE4L4", "Determine or clarify the meaning of unknown and multiple-meaning words and phrases", "vocabulary"),
        ("GEORGIA", "5", "ELA", "ELAGSE5RF4", "Read with sufficient accuracy and fluency to support comprehension", "fluency"),
        ("GEORGIA", "5", "ELA", "ELAGSE5RL1", "Quote accurately from a text when explaining what the text says explicitly and when drawing inferences", "comprehension"),
        ("GEORGIA", "5", "ELA", "ELAGSE5L4", "Determine or clarify the meaning of unknown and multiple-meaning words and phrases", "vocabulary"),
    ]
    conn.executemany(
        "INSERT OR IGNORE INTO standards VALUES (?, ?, ?, ?, ?, ?)",
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
        "INSERT OR IGNORE INTO assessments VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        assessments,
    )

    conn.commit()
    db_path_str = db_path or get_db_path()
    print(f"Database seeded successfully at {db_path_str}")
    print(f"  Frameworks: {conn.execute('SELECT count(*) FROM theoretical_frameworks').fetchone()[0]}")  # type: ignore[index]
    print(f"  Research papers: {conn.execute('SELECT count(*) FROM research_papers').fetchone()[0]}")  # type: ignore[index]
    print(f"  Vocabulary entries: {conn.execute('SELECT count(*) FROM vocabulary_corpus').fetchone()[0]}")  # type: ignore[index]
    print(f"  Standards: {conn.execute('SELECT count(*) FROM standards').fetchone()[0]}")  # type: ignore[index]
    print(f"  Assessments: {conn.execute('SELECT count(*) FROM assessments').fetchone()[0]}")  # type: ignore[index]

    return conn


if __name__ == "__main__":
    seed_database()
