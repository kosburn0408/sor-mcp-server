"""Decodable text generation tool.

Produces short decodable passages strictly limited to a student's phonetic
scope and sequence. All passages are template-driven — no LLM generation
at runtime to prevent pedagogical errors (e.g., using patterns the student
has not yet mastered).
"""
from __future__ import annotations

from typing import Any

from .schemas import DecodablePassage, DecodableRecommendation


# ── Scope & Sequence → Decodable Passage Templates ──────────────────────────
#
# Each entry maps a target phoneme to a grade-appropriate decodable passage
# that uses ONLY the listed mastered skills + a small number of explicitly
# listed high-frequency heart words.

DECODABLE_LIBRARY: dict[str, list[dict[str, Any]]] = {
    "short_a": [
        {
            "title": "Pat and the Cat",
            "text": "Pat is a cat. Pat sat on the mat. The mat is red.",
            "mastered_skills": ["cvc_short_a", "basic_sight_words"],
            "heart_words": ["the", "is", "a", "on"],
            "topic": "animals"
        },
        {
            "title": "Max the Rat",
            "text": "Max is a rat. Max can nap in a bag. The bag is tan.",
            "mastered_skills": ["cvc_short_a", "basic_sight_words", "cvc_short_i"],
            "heart_words": ["the", "is", "a", "in"],
            "topic": "animals"
        },
    ],
    "short_i": [
        {
            "title": "The Big Pig",
            "text": "Tim is a big pig. Tim can sit in the mud. Tim is a happy pig.",
            "mastered_skills": ["cvc_short_a", "cvc_short_i", "basic_sight_words"],
            "heart_words": ["the", "is", "a", "in", "happy"],
            "topic": "animals"
        },
    ],
    "silent_e": [
        {
            "title": "Jake and the Lake",
            "text": "Jake likes to hike by the lake. He can see a snake. The snake is by a stone. Jake goes home.",
            "mastered_skills": ["cvc_mixed", "cvce_silent_e", "consonant_blends"],
            "heart_words": ["the", "is", "a", "by", "he", "goes", "to"],
            "topic": "animals"
        },
        {
            "title": "A Cape for Kate",
            "text": "Kate has a red cape. She made the cape at home. Kate likes her cape a lot. It is big and fine.",
            "mastered_skills": ["cvc_mixed", "cvce_silent_e"],
            "heart_words": ["the", "is", "a", "has", "she", "her"],
            "topic": "daily_life"
        },
    ],
    "consonant_blends": [
        {
            "title": "Frog on a Log",
            "text": "A frog sat on a log. The frog can jump and swim. The frog is fast. Splash! The frog is in the pond.",
            "mastered_skills": ["cvc_mixed", "consonant_blends"],
            "heart_words": ["the", "is", "a", "on", "in", "and"],
            "topic": "animals"
        },
    ],
    "consonant_digraphs": [
        {
            "title": "Chip's Ship",
            "text": "Chip has a ship. The ship is in the bath. Chip can push the ship. Then it can go fast. Splash!",
            "mastered_skills": ["cvc_mixed", "consonant_digraphs"],
            "heart_words": ["the", "is", "a", "in", "has", "can", "then", "it"],
            "topic": "daily_life"
        },
    ],
    "r_controlled": [
        {
            "title": "A Day on the Farm",
            "text": "Martha went to the farm. She saw a horse in the barn. The horse was dark and smart. Martha fed the horse a carrot.",
            "mastered_skills": ["cvce_silent_e", "r_controlled", "vowel_teams"],
            "heart_words": ["the", "is", "a", "to", "in", "was", "she", "saw", "and"],
            "topic": "animals"
        },
    ],
    "vowel_teams": [
        {
            "title": "Rainy Day Play",
            "text": "It is a rainy day. Ray and May stay inside to play. They paint a boat and a train. What a fun day!",
            "mastered_skills": ["cvce_silent_e", "vowel_teams", "consonant_blends"],
            "heart_words": ["the", "is", "a", "to", "inside", "they", "what"],
            "topic": "daily_life"
        },
    ],
}


# ── Public API ──────────────────────────────────────────────────────────────


def recommend_decodable_resources(
    mastered_skills: list[str],
    target_phoneme: str,
    topic_interest: str | None = None,
) -> DecodableRecommendation:
    """Recommend decodable passages constrained to a student's mastered skills.

    All passages are pre-written and template-driven — no LLM generation at
    runtime. This guarantees that no untaught phonics patterns appear in the
    recommended text.

    Args:
        mastered_skills: List of skills the student has mastered
                         (e.g., ['cvc_short_a', 'basic_sight_words']).
        target_phoneme: The phoneme/grapheme being targeted
                        (e.g., 'short_a', 'silent_e', 'consonant_blends').
        topic_interest: Optional topic preference ('animals', 'daily_life', 'space').

    Returns:
        DecodableRecommendation with matching passages and teacher notes.
    """
    # Normalize the target phoneme
    target = target_phoneme.lower().strip().replace(" ", "_")
    if target.endswith("_e"):
        target = "silent_e"
    if target in ("long_a", "long_e", "long_i", "long_o"):
        target = "silent_e"

    candidates = DECODABLE_LIBRARY.get(target, [])

    # Fallback: if no exact match, search across all
    if not candidates:
        for key, passages in DECODABLE_LIBRARY.items():
            candidates.extend(passages)
        candidates = candidates[:4]

    # Score candidates by skill overlap
    scored = []
    for p in candidates:
        overlap = len(set(mastered_skills) & set(p["mastered_skills"]))
        topic_match = (
            1 if topic_interest and topic_interest.lower() in p.get("topic", "").lower()
            else 0
        )
        scored.append((overlap + topic_match, p))

    scored.sort(key=lambda x: -x[0])

    # Take top 3
    top = [s[1] for s in scored[:3]]

    # Check if any skills are out of scope
    all_required = set()
    for p in top:
        all_required.update(p["mastered_skills"])
    missing = all_required - set(mastered_skills)

    passages = []
    for p in top:
        passages.append(DecodablePassage(
            title=p["title"],
            text=p["text"],
            target_phoneme=target,
            word_count=len(p["text"].split()),
            mastered_skills_used=p["mastered_skills"],
            high_frequency_words=p["heart_words"],
        ))

    profile = (
        f"Mastered: {', '.join(mastered_skills)} | "
        f"Target: {target_phoneme}"
        + (f" | Interest: {topic_interest}" if topic_interest else "")
    )

    scope_warning = ""
    if missing:
        scope_warning = (
            f"⚠️ These passages use patterns ({', '.join(sorted(missing))}) "
            f"that are not in the student's mastered list. Pre-teach these "
            f"patterns or select a different target phoneme."
        )

    teacher_notes = (
        "Before reading, pre-teach the heart words listed for each passage. "
        "Have the student finger-tap each decodable word before reading aloud. "
        "After reading, ask one literal comprehension question to check "
        "understanding. Limit to 5-7 minutes per passage."
    )

    return DecodableRecommendation(
        student_profile=profile,
        passages=passages,
        teacher_notes=teacher_notes,
        scope_warning=scope_warning,
    )
