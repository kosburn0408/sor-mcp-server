"""MCP Prompt: explicit_phonics_routine — I Do/We Do/You Do script.

Returns an MCP prompt message that instructs the LLM to generate a
structured explicit phonics routine with multisensory cues.
"""

from __future__ import annotations


EXPLICIT_PHONICS_PROMPT = """You are a Science of Reading-aligned explicit phonics instructor.

Generate a complete I Do / We Do / You Do explicit phonics routine for teaching
the phoneme: "{target_phoneme}" at grade level: {grade}.

Structure your response EXACTLY as follows:

## I DO (Teacher Model) — ~2 minutes
"Watch me and listen..."
- Say the target phoneme clearly
- Show the grapheme (letter/letters) that represent the sound
- Model blending the sound into example words
- Use a multisensory cue: {multisensory}
- Think aloud: "When I see these letters, I say {target_phoneme}"

## WE DO (Guided Practice) — ~2 minutes
"Let's do this together..."
- Ask students to say the sound WITH you
- Point to the grapheme together and say the sound
- Blend 3-4 example words as a group
- Use hand signals / tapping / Elkonin boxes together

## YOU DO (Independent Practice) — ~3 minutes
"Your turn..."
- Show the grapheme — students say the sound independently
- Dictate 3-5 words for students to write
- Students read a short word list or decodable sentence
- Provide corrective feedback: "That part is right. Let's look at this part again..."

## WORD CHAIN
List a 5-word chain that manipulates one phoneme at a time:
1. (start word with target phoneme)
2. (change one sound)
3. (change one sound)
4. (change one sound)
5. (change one sound)

## CORRECTIVE FEEDBACK SCRIPT
If a student says the wrong sound:
1. "I heard you say ___. Let's look again."
2. Point to the grapheme: "This letter says {target_phoneme}."
3. "Now you try: what does this letter say?"
4. "Yes! {target_phoneme}. Let's try the word again."

## MULTISENSORY CUE
Recommended technique: {multisensory}
How to implement: (2-3 sentence description)

## FRAMEWORK ALIGNMENT
- Simple View of Reading: This builds decoding automaticity
- National Reading Panel: Explicit phonics instruction (effect size 0.41)
- Scarborough's Rope: Strengthens the phonological awareness strand

DO NOT include:
- "Look at the picture to figure it out"
- "Does it make sense?"
- "Skip the word and come back"
- Any guessing or 3-cueing strategies"""


async def explicit_phonics_routine(
    target_phoneme: str,
    grade: str = "1",
    multisensory: str = "finger tapping",
) -> str:
    """Generate a structured MCP prompt for an explicit phonics routine.

    Returns an MCP prompt message instructing the LLM to produce an
    I Do / We Do / You Do script with multisensory cues aligned to
    Science of Reading research.

    Args:
        target_phoneme: The target phoneme to teach (e.g., '/a/', '/sh/', '/ā/').
        grade: Grade level (K, 1, 2, 3, 4, 5).
        multisensory: Multisensory technique (default: 'finger tapping').
            Options: finger tapping, Elkonin boxes, sky writing, arm blending,
            sand tray, magnets, sound boxes.

    Returns:
        MCP prompt message string for the LLM.
    """
    return EXPLICIT_PHONICS_PROMPT.format(
        target_phoneme=target_phoneme,
        grade=grade,
        multisensory=multisensory,
    )
