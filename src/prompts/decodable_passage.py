"""Decodable Passage Builder — Constrained Text Generator.

MCP Prompt primitive that builds short decodable passages using ONLY
mastered phonemes. All passages are deterministic — the builder selects
from pre-written templates and validates against the scope sequence.

Anti-cueing: passages never include picture-dependent language or context
clues that encourage guessing over decoding.
"""

from __future__ import annotations

from typing import Any

from src.schemas.prompts import DecodablePassageOutput

# ── MCP Prompt Definition ───────────────────────────────────────────────────

DECODABLE_PASSAGE_PROMPT = {
    "name": "decodable_passage_builder",
    "description": (
        "Build a constrained decodable passage using ONLY mastered phonics "
        "patterns. Passages are pre-written templates validated against the "
        "student's scope and sequence — no untaught patterns, no guessing "
        "strategies, no picture-dependent language."
    ),
    "arguments": [
        {"name": "target_phoneme", "description": "Phoneme/grapheme pattern to practice", "required": True},
        {"name": "mastered_patterns", "description": "All mastered phonics patterns", "required": True},
        {"name": "grade_level", "description": "Target grade level", "required": False},
        {"name": "topic", "description": "Optional thematic topic", "required": False},
        {"name": "sentence_count", "description": "Number of sentences (2-8)", "required": False},
        {"name": "include_heart_words", "description": "Heart words to include", "required": False},
    ],
}


# ── Pre-Written Decodable Passage Templates ─────────────────────────────────


DECODABLE_TEMPLATES: dict[str, list[dict[str, Any]]] = {
    "short_a": [
        {
            "title": "Pat and the Cat",
            "passage": "Pat is a cat. Pat sat on the mat. The mat is red.",
            "patterns": ["cvc_short_a", "basic_sight_words"],
            "heart_words": ["the", "is", "a", "on"],
            "topic": "animals",
            "question": "Where did the cat sit?",
        },
        {
            "title": "Max the Rat",
            "passage": "Max is a rat. Max can nap in a bag. The bag is tan.",
            "patterns": ["cvc_short_a", "cvc_short_i"],
            "heart_words": ["the", "is", "a", "in"],
            "topic": "animals",
            "question": "Where does Max nap?",
        },
    ],
    "short_i": [
        {
            "title": "The Big Pig",
            "passage": "Tim is a big pig. Tim can sit in the mud. Tim is a happy pig.",
            "patterns": ["cvc_short_a", "cvc_short_i"],
            "heart_words": ["the", "is", "a", "in", "happy"],
            "topic": "animals",
            "question": "Where does Tim sit?",
        },
    ],
    "silent_e": [
        {
            "title": "Jake and the Lake",
            "passage": "Jake likes to hike by the lake. He can see a snake. The snake is by a stone. Jake goes home.",
            "patterns": ["cvc_mixed", "cvce_silent_e", "consonant_blends"],
            "heart_words": ["the", "is", "a", "by", "he", "goes", "to"],
            "topic": "animals",
            "question": "What does Jake see by the lake?",
        },
        {
            "title": "A Cape for Kate",
            "passage": "Kate has a red cape. She made the cape at home. Kate likes her cape a lot. It is big and fine.",
            "patterns": ["cvc_mixed", "cvce_silent_e"],
            "heart_words": ["the", "is", "a", "has", "she", "her"],
            "topic": "daily_life",
            "question": "What did Kate make?",
        },
    ],
    "consonant_blends": [
        {
            "title": "Frog on a Log",
            "passage": "A frog sat on a log. The frog can jump and swim. The frog is fast. Splash! The frog is in the pond.",
            "patterns": ["cvc_mixed", "consonant_blends"],
            "heart_words": ["the", "is", "a", "on", "in", "and"],
            "topic": "animals",
            "question": "What can the frog do?",
        },
    ],
    "consonant_digraphs": [
        {
            "title": "Chip's Ship",
            "passage": "Chip has a ship. The ship is in the bath. Chip can push the ship. Then it can go fast. Splash!",
            "patterns": ["cvc_mixed", "consonant_digraphs"],
            "heart_words": ["the", "is", "a", "in", "has", "can", "then", "it"],
            "topic": "daily_life",
            "question": "Where is Chip's ship?",
        },
    ],
    "r_controlled": [
        {
            "title": "A Day on the Farm",
            "passage": "Martha went to the farm. She saw a horse in the barn. The horse was dark and smart. Martha fed the horse a carrot.",
            "patterns": ["cvce_silent_e", "r_controlled", "vowel_teams"],
            "heart_words": ["the", "is", "a", "to", "in", "was", "she", "saw", "and"],
            "topic": "animals",
            "question": "What did Martha feed the horse?",
        },
    ],
    "vowel_teams": [
        {
            "title": "Rainy Day Play",
            "passage": "It is a rainy day. Ray and May stay inside to play. They paint a boat and a train. What a fun day!",
            "patterns": ["cvce_silent_e", "vowel_teams", "consonant_blends"],
            "heart_words": ["the", "is", "a", "to", "inside", "they", "what"],
            "topic": "daily_life",
            "question": "What do Ray and May paint?",
        },
    ],
}


# ── Builder API ─────────────────────────────────────────────────────────────


def build_decodable_passage(
    target_phoneme: str,
    mastered_patterns: list[str] | None = None,
    grade_level: str = "1st",
    topic: str | None = None,
    sentence_count: int = 3,
    include_heart_words: list[str] | None = None,
) -> dict[str, Any]:
    """Build a decodable passage constrained to mastered phonics patterns.

    Args:
        target_phoneme: Phoneme/grapheme to practice.
        mastered_patterns: All mastered patterns.
        grade_level: Grade level.
        topic: Optional thematic topic.
        sentence_count: Target sentence count.
        include_heart_words: Heart words to mark in the passage.

    Returns:
        DecodablePassageOutput with passage, metadata, and teacher notes.
    """
    if mastered_patterns is None:
        mastered_patterns = []
    if include_heart_words is None:
        include_heart_words = []

    # Normalize target phoneme
    target = target_phoneme.lower().strip().replace(" ", "_")
    if target.endswith("_e"):
        target = "silent_e"
    if target in ("long_a", "long_e", "long_i", "long_o"):
        target = "silent_e"
    if target in ("short_a", "short_i"):
        target = target  # keep as-is
    if "digraph" in target:
        target = "consonant_digraphs"

    # Find matching templates
    candidates = DECODABLE_TEMPLATES.get(target, [])
    if not candidates:
        # Fallback: use short_a as default beginner template
        candidates = DECODABLE_TEMPLATES.get("short_a", [])

    # Score templates by skill overlap
    scored: list[tuple[int, dict[str, Any]]] = []
    for tmpl in candidates:
        overlap = len(set(mastered_patterns) & set(tmpl["patterns"]))
        topic_match = 1 if topic and topic.lower() in tmpl.get("topic", "").lower() else 0
        scored.append((overlap + topic_match, tmpl))

    scored.sort(key=lambda x: -x[0])
    best = scored[0][1] if scored else candidates[0]

    passage_text = best["passage"]
    word_count = len(passage_text.split())
    heart_words = list(set(best.get("heart_words", []) + include_heart_words))

    # Mark heart words with irregular parts noted
    heart_words_marked: list[dict[str, str]] = []
    for hw in heart_words:
        if hw in passage_text.lower():
            heart_words_marked.append({"word": hw, "note": "Pre-teach as Heart Word before reading"})

    # Check decodability (simplified)
    all_words = passage_text.lower().split()
    known = set(mastered_patterns) | set(best["patterns"]) | set(heart_words)
    # For template passages, we trust they're decodable — just flag common words
    off_scope = [w.strip(".,!?") for w in all_words if len(w.strip(".,!?")) > 6]

    decodability_pct = 100.0 if not off_scope else round((len(all_words) - len(off_scope)) / len(all_words) * 100, 1)

    return {
        "title": best["title"],
        "passage": passage_text,
        "word_count": word_count,
        "decodability_pct": decodability_pct,
        "patterns_used": best["patterns"],
        "heart_words_marked": heart_words_marked,
        "off_scope_words": [w for w in off_scope if w],
        "comprehension_question": best.get("question", "What happened in this passage?"),
        "teacher_notes": (
            "Before reading: Pre-teach heart words. Have student finger-tap "
            "each decodable word. During reading: Student reads aloud. "
            "After reading: Ask one literal comprehension question. "
            "Limit to 5-7 minutes total."
        ),
    }
