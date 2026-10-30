"""Detect three-cueing (MSV) prompting language.

Three-cueing prompts steer students to guess words from pictures, context or
first letters instead of decoding them. They usually appear in teacher
prompts, lesson scripts, guided-reading notes and student directions, not in
the story text itself.

Each rule has a regex, the cue it relies on, why it is a problem, and a
decoding-focused replacement prompt. Matching is deterministic, so a teacher
can see exactly which words triggered a flag.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

DECODE_PROMPT = "Point to each letter or letter team, say the sounds, and blend them."


@dataclass(frozen=True)
class CueingRule:
    id: str
    pattern: str
    cue: str  # "meaning" | "structure" | "visual_first_letter" | "picture" | "skip"
    severity: str  # "high" | "medium"
    why: str
    replacement: str


RULES: tuple[CueingRule, ...] = (
    CueingRule(
        "picture", r"\b(look|check)\s+(at\s+)?(the\s+)?(picture|illustration|image)s?\b",
        "picture", "high",
        "Directs the student to guess the word from the picture instead of the print.",
        "Look at the word. " + DECODE_PROMPT,
    ),
    CueingRule(
        "picture_clue", r"\b(picture|illustration)\s+(clue|help|support)s?\b",
        "picture", "high",
        "Treats the picture as a word-identification strategy.",
        DECODE_PROMPT,
    ),
    CueingRule(
        "makes_sense", r"\b(what|which)\s+(word\s+)?(would|could|might)\s+(make|makes)\s+sense\b|\bdoes\s+(that|it)\s+make\s+sense\b",
        "meaning", "high",
        "Asks the student to predict a word from meaning rather than read it.",
        "Read the word sound by sound. Then ask: does that match what the letters say?",
    ),
    CueingRule(
        "sounds_right", r"\bdoes\s+(that|it)\s+sound\s+right\b",
        "structure", "high",
        "Asks the student to judge a guess by sentence structure instead of the letters.",
        "Check the word: " + DECODE_PROMPT,
    ),
    CueingRule(
        "looks_right", r"\bdoes\s+(that|it)\s+look\s+right\b",
        "visual_first_letter", "medium",
        "Usually means 'does your guess roughly match the letters', which rewards partial visual guessing.",
        "Let's check every sound: " + DECODE_PROMPT,
    ),
    CueingRule(
        "fit_context", r"\b(what|which)\s+word\s+(would|could|might)\s+(fit|go|belong)\b|\bthink\s+of\s+a\s+word\s+that\s+(would\s+)?(fit|make)",
        "meaning", "high",
        "Asks the student to supply a word from context.",
        DECODE_PROMPT,
    ),
    CueingRule(
        "first_letter", r"\b(look|start)\s+(at|with)\s+the\s+first\s+(letter|sound)\b.*\b(guess|think|what\s+word)\b|\bget\s+your\s+mouth\s+ready\b",
        "visual_first_letter", "medium",
        "Encourages using only the first letter plus context to guess the rest of the word.",
        "Read all the way through the word: " + DECODE_PROMPT,
    ),
    CueingRule(
        "skip", r"\bskip\s+(it|the\s+word|that\s+word)\b|\bread\s+(on|ahead|the\s+rest\s+of\s+the\s+sentence)\s+and\s+come\s+back\b",
        "skip", "high",
        "Teaches skipping a word and filling it in from context.",
        "Stay on the word. " + DECODE_PROMPT,
    ),
    CueingRule(
        "guess", r"\b(make\s+a\s+guess|take\s+a\s+guess|guess\s+the\s+word|good\s+guess)\b",
        "meaning", "high",
        "Explicitly rewards guessing.",
        DECODE_PROMPT,
    ),
    CueingRule(
        "msv", r"\b(three|3)[-\s]?cueing\b|\bMSV\b|\bmeaning,\s*structure,?\s*(and\s+)?visual\b",
        "meaning", "high",
        "References the three-cueing (MSV) model directly.",
        "Replace MSV prompts with decoding prompts: " + DECODE_PROMPT,
    ),
)

_COMPILED = [(r, re.compile(r.pattern, re.IGNORECASE)) for r in RULES]


def detect_cueing(text: str) -> list[dict[str, Any]]:
    """Return one flag per matched three-cueing prompt."""
    flags: list[dict[str, Any]] = []
    if not text:
        return flags
    for rule, rx in _COMPILED:
        for m in rx.finditer(text):
            flags.append({
                "rule": rule.id,
                "matched_text": m.group(0),
                "position": m.start(),
                "cue": rule.cue,
                "severity": rule.severity,
                "why": rule.why,
                "suggested_prompt": rule.replacement,
            })
    flags.sort(key=lambda f: f["position"])
    return flags
