"""Vocabulary tier classification tool.

Classifies words into Beck, McKeown & Kucan's (2013) three-tier framework:

  Tier 1: Basic, high-frequency words used in everyday conversation.
           (e.g., dog, happy, run, book, red)

  Tier 2: High-utility academic words that appear across content areas.
           (e.g., analyze, compare, contrast, evidence, infer)

  Tier 3: Domain-specific, low-frequency words tied to a content area.
           (e.g., photosynthesis, hypotenuse, phoneme, isotope)

Theoretical basis:
- Beck, McKeown & Kucan (2013) "Bringing Words to Life"
- National Reading Panel: vocabulary instruction effect size d=0.47-0.52
- Scarborough's Rope: vocabulary is a critical strand in language comprehension
- Simple View of Reading: vocabulary contributes to linguistic comprehension
"""

import re
from collections import Counter
from typing import Any


# Tier 2 academic words (subset of Coxhead's Academic Word List, adapted for K-5)
TIER_2_PATTERNS: dict[str, list[str]] = {
    "analyze": ["analyze", "analysis", "analyst", "analytic", "analytical"],
    "approach": ["approach", "approachable", "approaching"],
    "assess": ["assess", "assessment", "assessing", "assessed"],
    "assume": ["assume", "assumed", "assuming", "assumption"],
    "authority": ["authority", "authoritative", "authorities"],
    "benefit": ["benefit", "beneficial", "beneficiary", "benefits"],
    "concept": ["concept", "conception", "concepts", "conceptual"],
    "consist": ["consist", "consisted", "consistency", "consistent"],
    "context": ["context", "contexts", "contextual"],
    "contract": ["contract", "contracted", "contracting"],
    "create": ["create", "created", "creating", "creation", "creative"],
    "data": ["data", "database", "dataset"],
    "define": ["define", "defined", "defines", "defining", "definition"],
    "derive": ["derive", "derived", "derives", "deriving"],
    "distribute": ["distribute", "distributed", "distribution"],
    "economy": ["economy", "economic", "economical", "economics"],
    "environment": ["environment", "environmental"],
    "establish": ["establish", "established", "establishment"],
    "estimate": ["estimate", "estimated", "estimation"],
    "evidence": ["evidence", "evident", "evidently"],
    "export": ["export", "exported", "exporting"],
    "factor": ["factor", "factors", "factored"],
    "finance": ["finance", "financial", "financially"],
    "formula": ["formula", "formulas", "formulate", "formulation"],
    "function": ["function", "functional", "functioning"],
    "identify": ["identify", "identified", "identification"],
    "income": ["income", "incomes"],
    "indicate": ["indicate", "indicated", "indication", "indicative"],
    "individual": ["individual", "individually", "individuals"],
    "interpret": ["interpret", "interpretation", "interpreted"],
    "involve": ["involve", "involved", "involvement"],
    "issue": ["issue", "issued", "issues", "issuing"],
    "labor": ["labor", "labored", "labors"],
    "legal": ["legal", "illegal", "legality"],
    "legislate": ["legislate", "legislated", "legislation", "legislative"],
    "major": ["major", "majority", "majorities"],
    "method": ["method", "methodical", "methods"],
    "occur": ["occur", "occurred", "occurrence", "occurs"],
    "percent": ["percent", "percentage", "percentages"],
    "period": ["period", "periodic", "periods"],
    "policy": ["policy", "policies"],
    "principle": ["principle", "principles", "principal"],
    "proceed": ["proceed", "proceeding", "proceedings"],
    "process": ["process", "processed", "processes", "processing"],
    "require": ["require", "required", "requirement", "requires"],
    "research": ["research", "researched", "researcher"],
    "respond": ["respond", "responded", "respondent", "response"],
    "role": ["role", "roles"],
    "section": ["section", "sections", "sector"],
    "significant": ["significant", "significance", "significantly"],
    "similar": ["similar", "similarity", "similarly"],
    "source": ["source", "sourced", "sources"],
    "specific": ["specific", "specifically", "specification"],
    "structure": ["structure", "structured", "structures"],
    "theory": ["theory", "theoretical", "theories"],
    "vary": ["vary", "varied", "varies", "variety", "various"],
    "achieve": ["achieve", "achieved", "achievement", "achieves"],
    "acquire": ["acquire", "acquired", "acquisition"],
    "administer": ["administer", "administration", "administrative"],
    "affect": ["affect", "affected", "affecting", "affects"],
    "appropriate": ["appropriate", "appropriately"],
    "aspect": ["aspect", "aspects"],
    "assist": ["assist", "assistance", "assistant"],
    "category": ["category", "categories", "categorize"],
    "chapter": ["chapter", "chapters"],
    "commission": ["commission", "commissioned"],
    "community": ["community", "communities"],
    "complex": ["complex", "complexity"],
    "compute": ["compute", "computation", "computer"],
    "conclude": ["conclude", "concluded", "conclusion"],
    "conduct": ["conduct", "conducted", "conducting"],
    "consequence": ["consequence", "consequences", "consequently"],
    "construct": ["construct", "constructed", "construction"],
    "consume": ["consume", "consumed", "consumer", "consumption"],
    "credit": ["credit", "credited", "credits"],
    "culture": ["culture", "cultural", "culturally"],
    "design": ["design", "designed", "designing"],
    "distinct": ["distinct", "distinction", "distinctive"],
    "element": ["element", "elements", "elementary"],
    "equate": ["equate", "equated", "equation"],
    "evaluate": ["evaluate", "evaluated", "evaluation"],
    "feature": ["feature", "featured", "features"],
    "final": ["final", "finalize", "finally"],
    "focus": ["focus", "focused", "focusing"],
    "impact": ["impact", "impacted", "impacting"],
    "injure": ["injure", "injured", "injury"],
    "institute": ["institute", "instituted", "institution"],
    "invest": ["invest", "invested", "investment"],
    "item": ["item", "items"],
    "journal": ["journal", "journals"],
    "maintain": ["maintain", "maintained", "maintenance"],
    "normal": ["normal", "abnormal", "normally"],
    "obtain": ["obtain", "obtained", "obtaining"],
    "participate": ["participate", "participant", "participation"],
    "perceive": ["perceive", "perceived", "perception"],
    "positive": ["positive", "positively"],
    "potential": ["potential", "potentially"],
    "previous": ["previous", "previously"],
    "primary": ["primary", "primarily"],
    "purchase": ["purchase", "purchased", "purchasing"],
    "range": ["range", "ranged", "ranging"],
    "region": ["region", "regional", "regions"],
    "regulate": ["regulate", "regulated", "regulation"],
    "relevant": ["relevant", "relevance"],
    "reside": ["reside", "residence", "resident"],
    "resource": ["resource", "resources"],
    "restrict": ["restrict", "restricted", "restriction"],
    "secure": ["secure", "secured", "security"],
    "seek": ["seek", "seeking", "seeks"],
    "select": ["select", "selected", "selection"],
    "site": ["site", "sites"],
    "strategy": ["strategy", "strategic", "strategies"],
    "survey": ["survey", "surveyed", "surveying"],
    "text": ["text", "texts", "textual"],
    "tradition": ["tradition", "traditional", "traditionally"],
    "transfer": ["transfer", "transferred", "transferring"],
}


# Tier 3 domain-specific word lists by domain
TIER_3_DOMAINS: dict[str, set[str]] = {
    "literacy": {
        "phoneme", "grapheme", "morpheme", "syllable", "digraph",
        "diphthong", "schwa", "onset", "rime", "blend", "segment",
        "decode", "encode", "orthographic", "phonological", "semantic",
        "syntactic", "prosody", "fluency", "comprehension", "metacognition",
        "lexicon", "etymology", "morphology", "syntax", "pragmatics",
    },
    "science": {
        "hypothesis", "experiment", "variable", "organism", "ecosystem",
        "photosynthesis", "mitosis", "gravity", "molecule", "atom",
        "evolution", "habitat", "adaptation", "species", "cell",
        "organism", "fossil", "climate", "erosion", "precipitation",
    },
    "mathematics": {
        "numerator", "denominator", "quadrilateral", "exponent", "integer",
        "polynomial", "coefficient", "variable", "equation", "fraction",
        "decimal", "percent", "volume", "perimeter", "circumference",
        "symmetry", "congruent", "parallel", "perpendicular", "algorithm",
    },
    "social_studies": {
        "constitution", "democracy", "legislature", "amendment", "census",
        "civilization", "colony", "revolution", "immigration", "economics",
        "geography", "archaeology", "artifact", "primary_source", "cartography",
        "culture", "sovereignty", "federalism", "suffrage", "ratification",
    },
}


def classify_text(text: str, domain: str = "literacy") -> dict[str, Any]:
    """Classify all words in a text into Tier 1, 2, or 3 categories.

    Args:
        text: The text to analyze.
        domain: Content domain for Tier 3 word matching (literacy, science,
                mathematics, social_studies). Defaults to 'literacy'.

    Returns:
        Dictionary with tier breakdown, word lists, and instructional recommendations.
    """
    if not text or not text.strip():
        return {"error": "No text provided for analysis", "tiers": None}

    # Extract words
    words = re.findall(r"[a-zA-Z]+(?:'[a-zA-Z]+)?", text.lower())
    if not words:
        return {"error": "No recognizable words found", "tiers": None}

    # Build flattened tier lookups
    tier_2_words: set[str] = set()
    for base, forms in TIER_2_PATTERNS.items():
        tier_2_words.update(forms)
        tier_2_words.add(base)

    tier_3_words = TIER_3_DOMAINS.get(domain, TIER_3_DOMAINS["literacy"])

    # Classify each distinct word
    distinct_words = set(words)
    tier1: list[str] = []
    tier2: list[str] = []
    tier3: list[str] = []

    for word in distinct_words:
        if word in tier_3_words:
            tier3.append(word)
        elif word in tier_2_words:
            tier2.append(word)
        else:
            tier1.append(word)

    total_distinct = len(distinct_words)
    tier1_count = len(tier1)
    tier2_count = len(tier2)
    tier3_count = len(tier3)

    # Frequency analysis — how often do tier words appear in the text?
    word_freq = Counter(words)
    tier1_tokens = sum(word_freq[w] for w in tier1)
    tier2_tokens = sum(word_freq[w] for w in tier2)
    tier3_tokens = sum(word_freq[w] for w in tier3)
    total_tokens = len(words)

    # Recommendations
    recommendation = _get_vocabulary_recommendation(
        tier2_count, tier3_count, total_distinct
    )

    return {
        "domain": domain,
        "total_distinct_words": total_distinct,
        "total_tokens": total_tokens,
        "tier_breakdown": {
            "tier_1": {
                "count": tier1_count,
                "percentage": round(tier1_count / total_distinct * 100, 1),
                "token_count": tier1_tokens,
                "token_percentage": round(tier1_tokens / total_tokens * 100, 1),
                "description": "Basic conversational words",
            },
            "tier_2": {
                "count": tier2_count,
                "percentage": round(tier2_count / total_distinct * 100, 1),
                "token_count": tier2_tokens,
                "token_percentage": round(tier2_tokens / total_tokens * 100, 1),
                "description": "High-utility academic words",
                "words": sorted(tier2),
            },
            "tier_3": {
                "count": tier3_count,
                "percentage": round(tier3_count / total_distinct * 100, 1),
                "token_count": tier3_tokens,
                "token_percentage": round(tier3_tokens / total_tokens * 100, 1),
                "description": f"Domain-specific ({domain}) words",
                "words": sorted(tier3),
            },
        },
        "recommendation": recommendation,
        "framework_note": (
            "Beck, McKeown & Kucan (2013): Tier 2 words deserve the most "
            "instructional attention — they are high-utility across domains "
            "and less likely to be learned incidentally. National Reading "
            "Panel: explicit vocabulary instruction yields d=0.47-0.52. "
            "Scarborough's Rope: vocabulary is a critical strand in the "
            "language comprehension half of skilled reading."
        ),
    }


def _get_vocabulary_recommendation(
    tier2_count: int, tier3_count: int, total: int
) -> str:
    """Generate vocabulary instruction recommendations."""
    if tier2_count == 0 and tier3_count == 0:
        return (
            "Text is composed entirely of Tier 1 (basic) words — no "
            "vocabulary instruction needed for word meanings. Consider "
            "adding richer vocabulary to build language comprehension."
        )
    if tier2_count <= 3:
        return (
            f"Light vocabulary load: {tier2_count} Tier 2 words identified. "
            "Pre-teach each before reading with student-friendly definitions, "
            "context examples, and multiple exposures. One brief lesson may suffice."
        )
    if tier2_count <= 8:
        return (
            f"Moderate vocabulary load: {tier2_count} Tier 2 words. "
            "Select 4-5 most critical words for deep instruction. "
            "Provide student-friendly definitions, contextual examples, "
            "and opportunities for students to use words in discussion."
        )
    return (
        f"Heavy vocabulary load: {tier2_count} Tier 2 words. "
        "Select 5-7 highest-leverage words for explicit instruction. "
        "Use a vocabulary routine: pronounce, explain, provide examples, "
        "ask questions, and have students interact with words. "
        "Scaffold remaining words contextually during reading."
    )


def match_word_vocabulary(word: str, grade: int | None = None) -> dict[str, Any]:
    """Look up a single word's tier classification in the database.

    Args:
        word: The word to look up.
        grade: Optional grade level filter.

    Returns:
        Dictionary with tier classification and database info.
    """
    from db.database import get_connection
    conn = get_connection()
    word_lower = word.lower().strip()

    query = "SELECT word, grade, tier, frequency, decodable FROM vocabulary_corpus WHERE word = ?"
    params: list[str | int] = [word_lower]

    if grade is not None:
        query += " AND grade = ?"
        params.append(grade)

    result = conn.execute(query, params).fetchall()

    if not result:
        # Fall back to in-memory classification
        tier_2_words: set[str] = set()
        for base, forms in TIER_2_PATTERNS.items():
            tier_2_words.update(forms)
            tier_2_words.add(base)

        if word_lower in tier_2_words:
            tier = 2
            tier_label = "Tier 2 — High-utility academic word"
        elif any(word_lower in domain_words for domain_words in TIER_3_DOMAINS.values()):
            tier = 3
            tier_label = "Tier 3 — Domain-specific word"
        else:
            tier = 1
            tier_label = "Tier 1 — Basic conversational word"

        return {
            "word": word_lower,
            "tier": tier,
            "tier_label": tier_label,
            "source": "in-memory classifier",
            "in_corpus": False,
        }

    rows = [
        {
            "word": r[0],
            "grade": r[1],
            "tier": r[2],
            "frequency": r[3],
            "decodable": r[4],
        }
        for r in result
    ]

    tier_map = {1: "Tier 1 — Basic", 2: "Tier 2 — Academic", 3: "Tier 3 — Domain-specific"}

    return {
        "word": word_lower,
        "tier": rows[0]["tier"],
        "tier_label": tier_map.get(rows[0]["tier"], "Unknown"),
        "source": "corpus database",
        "in_corpus": True,
        "entries": rows,
    }


if __name__ == "__main__":
    import json
    sample = (
        "The dog ran quickly through the park. Scientists analyze the "
        "ecosystem to understand how organisms interact. The phoneme "
        "and grapheme relationship is important for decoding."
    )
    result = classify_text(sample)
    print(json.dumps(result, indent=2))
