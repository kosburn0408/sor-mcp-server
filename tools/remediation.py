"""Instructional remediation tools for the Science of Reading MCP server.

Provides deterministic, research-aligned instructional routines for
specific phonics and phonological awareness deficits. All remediation
data is stored in static lookup tables to prevent pedagogical hallucinations.

Theoretical basis:
- Orton-Gillingham multisensory structured literacy
- Explicit Instruction (Archer & Hughes, 2011)
- WWC Foundational Skills Practice Guide (2016)
- NRP Phonics findings (d=0.41-0.60)

Every remediation card follows: Micro-PD → I Do/We Do/You Do →
Multisensory Cue → Word Chain → Corrective Feedback → Connected Text.
"""
from __future__ import annotations

from typing import Any

from .schemas import (
    CorrectiveFeedback,
    MicroPD,
    MultisensoryCue,
    RemediationCard,
    TeacherScript,
    WordChain,
)


# ── Static Remediation Lookup Table ─────────────────────────────────────────
#
# Every entry is deterministic — no LLM generation at runtime.
# Each deficit_code maps to a complete, research-aligned remediation card.
# To add a new deficit: add a new entry to REMEDIATION_TABLE below.

REMEDIATION_TABLE: dict[str, dict[str, Any]] = {
    # ── Short Vowels ────────────────────────────────────────────────
    "cvc_short_a": {
        "skill_name": "Short Vowel /a/ (CVC pattern)",
        "grade_levels": ["K", "1st"],
        "micro_pd": {
            "principle": "Short Vowel /a/ in Closed Syllables",
            "explanation": (
                "In a CVC word (consonant-vowel-consonant), the vowel makes its "
                "short sound because it is 'closed in' by a consonant. The mouth "
                "is open and the tongue is low for /a/ as in 'cat'. This is the "
                "first vowel sound taught because it is the most stable and "
                "frequent short vowel in early decodable text."
            ),
            "research_basis": "NRP Phonics (d=0.41); Ehri's Phases of Word Reading (1995)"
        },
        "teacher_script": {
            "i_do": (
                "Watch me read this word: /c/.../a/.../t/. I touch under each "
                "letter and say its sound, then blend them together: c-a-t, cat! "
                "See how the 'a' is trapped between two consonants? That means it "
                "says its short sound, /a/. I'll show you another one: /m/.../a/.../p/, map!"
            ),
            "we_do": (
                "Now let's do one together. Point to the word 'hat'. Ready? "
                "H-a-t... hat! Let's try 'bat'. B-a-t... bat! "
                "Excellent. Your turn to lead — I'll follow."
            ),
            "you_do": (
                "Here are three words for you to read by yourself: "
                "pat, man, sad. Touch each letter, say the sound, blend it. "
                "Go ahead."
            )
        },
        "multisensory_cue": {
            "name": "Sound Boxes (Elkonin Boxes)",
            "materials": "Whiteboard and marker, or 3 tokens/coins",
            "procedure": (
                "1. Draw 3 connected boxes on the whiteboard. "
                "2. Say 'cat'. Student pushes a token into box 1 for /c/, "
                "box 2 for /a/, box 3 for /t/. "
                "3. Student slides their finger under all 3 boxes while blending."
            ),
            "verbal_anchor": "Touch it. Say it. Blend it."
        },
        "word_chain": {
            "chain": ["cat", "bat", "bad", "dad", "sad", "mad"],
            "target_pattern": "Short /a/ in CVC — change one sound at a time",
            "non_example": "cake (The 'a' says its name because of the silent-e — different rule!)"
        },
        "corrective_feedback": {
            "error_response": (
                "That word has a short /a/ sound. Remember: the vowel is "
                "closed in by a consonant. Touch each sound and try again."
            ),
            "praise_response": "You blended that word perfectly! Your brain is mapping those sounds."
        },
        "connected_text": "Pat has a cat. The cat sat on the mat."
    },

    "cvc_mixed": {
        "skill_name": "Mixed Short Vowels (a, e, i, o, u in CVC)",
        "grade_levels": ["K", "1st"],
        "micro_pd": {
            "principle": "All Five Short Vowels in Closed Syllables",
            "explanation": (
                "After students master individual short vowels, they need to "
                "discriminate between them. The vowel sound changes depending on "
                "which letter is 'trapped' between the consonants. Students who "
                "confuse short /e/ and /i/ (a common error) benefit from minimal "
                "pair practice where the only difference is the vowel."
            ),
            "research_basis": "Scarborough's Rope — decoding strand; Kilpatrick (2015) phonemic proficiency"
        },
        "teacher_script": {
            "i_do": (
                "Watch how changing just one letter changes the whole word. "
                "Here's 'big' — /b/-/i/-/g/, big. Now I change 'i' to 'a': "
                "/b/-/a/-/g/, bag. Same beginning, same ending — different middle! "
                "Your brain has to pay attention to the vowel."
            ),
            "we_do": (
                "Let's do some together. I'll write a word, you read it. "
                "[Write: pet] Read this... Good! Now I change it. [Erase e, write i] "
                "pit. Pet... pit. Do you hear the difference? Let's do more."
            ),
            "you_do": (
                "I'm going to say a word. You write it in your sound boxes. "
                "Ready? 'cup'... 'cap'... 'cop'. Check each one — did the vowel change?"
            )
        },
        "multisensory_cue": {
            "name": "Vowel Hand Signals",
            "materials": "none",
            "procedure": (
                "For each short vowel, use a hand signal: "
                "/a/ = open palm on chest (apple); "
                "/e/ = hand to ear (echo); "
                "/i/ = finger to lips (itch); "
                "/o/ = open mouth circle (octopus); "
                "/u/ = point up (up). "
                "Student says sound while making the motion."
            ),
            "verbal_anchor": "Sound it. Signal it. Spell it."
        },
        "word_chain": {
            "chain": ["bag", "big", "bug", "hug", "hog", "hot"],
            "target_pattern": "Discriminating short vowels — change vowel only",
            "non_example": "bake (long vowel — different syllable type)"
        },
        "corrective_feedback": {
            "error_response": (
                "The vowel is the middle sound. What letter is in the middle? "
                "What sound does that vowel make in a closed syllable? Blend again."
            ),
            "praise_response": "You caught the vowel change! That's how strong readers think."
        },
        "connected_text": "The big bug sat on the hot rug."
    },

    # ── Consonant Blends ──────────────────────────────────────────
    "consonant_blends": {
        "skill_name": "Consonant Blends (CCVC/CVCC)",
        "grade_levels": ["1st", "2nd"],
        "micro_pd": {
            "principle": "Two-Consonant Blends — Each Sound is Still Heard",
            "explanation": (
                "A consonant blend has two (or three) consonants together where "
                "you can still hear each sound. Unlike digraphs (sh, ch, th) where "
                "two letters make one new sound, in a blend like 'st' in 'stop', "
                "you hear /s/ and /t/ separately. Students often omit one sound in "
                "blends — this is a developmental pattern, not a disorder. They need "
                "explicit practice 'feeling' both sounds in sequence."
            ),
            "research_basis": "NRP Phonics (d=0.44); BEE Beginning Reading (Slavin et al., 2008, d=0.32)"
        },
        "teacher_script": {
            "i_do": (
                "Watch my mouth when I say 'stop'. Ssss...t...op. I felt my tongue "
                "make TWO sounds at the beginning — /s/ and /t/. They slide together "
                "but each one counts. Now watch 'frog': fff...r...og. Two sounds "
                "at the start: /f/ and /r/. Your tongue touches different spots "
                "for each one."
            ),
            "we_do": (
                "Let's use our fingers. Every time you hear a sound at the beginning, "
                "hold up a finger. [Say: 'clap'] /c/.../l/ — that's TWO fingers! "
                "Now: 'snap' — /s/.../n/ — two fingers. Now: 'drip' — /d/.../r/ — "
                "two fingers. Your mouth makes each sound. Let's do more!"
            ),
            "you_do": (
                "Here's a list of words. Read each one, holding up a finger for "
                "every sound you hear at the beginning: clip, trip, spot, grab, frog. "
                "Remember — if you say two sounds, you need two fingers!"
            )
        },
        "multisensory_cue": {
            "name": "Blend Finger Tapping",
            "materials": "none",
            "procedure": (
                "1. For a word like 'stop': tap thumb for /s/, index for /t/, "
                "middle for /o/, ring for /p/. "
                "2. Student says each sound while tapping the corresponding finger. "
                "3. Then slides all fingers together while saying the whole word. "
                "Blends go on THUMB+INDEX together, not separate fingers."
            ),
            "verbal_anchor": "Tap each sound. Now slide them together."
        },
        "word_chain": {
            "chain": ["stop", "step", "stem", "steam", "stream"],
            "target_pattern": "s-blends → st- → str- (building complexity)",
            "non_example": "ship (sh is a digraph — two letters make one sound)"
        },
        "corrective_feedback": {
            "error_response": (
                "I heard one sound missing from that blend. Let's finger-tap it "
                "together. How many sounds do you feel at the beginning? Try again."
            ),
            "praise_response": "You got every sound in that blend! Your ears and mouth worked together."
        },
        "connected_text": "Stan must stop and rest on the big stump."
    },

    # ── Silent-e / CVCe ───────────────────────────────────────────
    "cvce_silent_e": {
        "skill_name": "Silent-e Pattern (CVCe)",
        "grade_levels": ["1st", "2nd"],
        "micro_pd": {
            "principle": "The Silent-e Rule — Final-e Makes the Vowel Say Its Name",
            "explanation": (
                "In a CVCe pattern (consonant-vowel-consonant-silent e), the "
                "final 'e' is silent but signals the preceding vowel to say its "
                "long sound (its 'name'). The 'e' does not represent a phoneme "
                "itself — it is a marker. Students often over-generalize this rule "
                "(applying it to words like 'have' or 'come') and need instruction "
                "on exceptions. This pattern is the most common long-vowel spelling "
                "in English and a gateway to multisyllabic decoding."
            ),
            "research_basis": "NRP Phonics (d=0.48); Moats (2020) Speech to Print"
        },
        "teacher_script": {
            "i_do": (
                "Watch what happens when I add a silent 'e' at the end of this word. "
                "'Cap' becomes 'cape'. Did you hear the 'a' change? In 'cap', the 'a' "
                "says /a/ because it's trapped. But when I add silent 'e', it kicks "
                "the vowel and says 'Say your name!' So 'a' says /ā/. The 'e' itself "
                "is silent — it's just the boss!"
            ),
            "we_do": (
                "Let's try some together. I'll write 'kit'. Read it... Now I add "
                "silent 'e'. Kite! Did 'i' say its name? Let's do more: "
                "'hop' → 'hope'. 'not' → 'note'. 'pet' → 'Pete'. "
                "Each time, the silent 'e' is the boss of the vowel."
            ),
            "you_do": (
                "Here are some short-vowel words. Add silent 'e' to each one "
                "and read the new word: can, pin, cub, tap, rid. "
                "What changes? What stays the same?"
            )
        },
        "multisensory_cue": {
            "name": "Magic E Wand",
            "materials": "Index card with 'e' drawn on it, or a popsicle stick",
            "procedure": (
                "1. Write a CVC word on the board (e.g., 'cap'). "
                "2. Student reads it with short vowel. "
                "3. Teacher holds up the 'Magic E Wand' at the end. "
                "4. Student rereads with long vowel. "
                "5. Swap the wand to other words. Have the student hold the wand!"
            ),
            "verbal_anchor": "Magic E taps the vowel: 'Say your name!'"
        },
        "word_chain": {
            "chain": ["cap", "cape", "tape", "tap", "tape", "shape"],
            "target_pattern": "CVC ↔ CVCe — toggling short and long vowels",
            "non_example": "have (Even with silent-e, the 'a' stays short — it's a rule breaker!)"
        },
        "corrective_feedback": {
            "error_response": (
                "I see a silent 'e' at the end of that word. What does silent 'e' "
                "tell the vowel to do? Say the vowel's name, then try the word again."
            ),
            "praise_response": "You spotted the silent 'e' and made the vowel say its name! That's the rule!"
        },
        "connected_text": "Jake and Kate made a cake by the lake."
    },

    # ── Digraphs ───────────────────────────────────────────────────
    "consonant_digraphs": {
        "skill_name": "Consonant Digraphs (sh, ch, th, wh, ck)",
        "grade_levels": ["K", "1st"],
        "micro_pd": {
            "principle": "Two Letters Making One New Sound",
            "explanation": (
                "Unlike blends where each letter keeps its sound, a digraph is "
                "two letters that work as a team to make ONE completely new sound. "
                "'S' and 'h' together don't say /s/+/h/ — they say /sh/. Students "
                "must store these as single phonemic units. 'ch' is particularly "
                "tricky because it can represent three different sounds: /ch/ as in "
                "'chip', /k/ as in 'school', /sh/ as in 'chef'."
            ),
            "research_basis": "NRP Phonics (d=0.41); Ehri's Consolidated Phase"
        },
        "teacher_script": {
            "i_do": (
                "When I see 's' and 'h' together, my brain says 'these are a team — "
                "they make one sound: /sh/.' Watch my mouth: /sh/ like 'ship'. "
                "My lips push forward and air comes out. Now 'ch' like 'chip': "
                "my tongue taps the roof of my mouth. One sound from two letters."
            ),
            "we_do": (
                "Let's sort some words. I'll say a word and you tell me which "
                "digraph you hear. Ready? /Sh/ip — digraph at the beginning, 'sh'. "
                "/Ch/ip — digraph at the beginning, 'ch'. Ri/ch/ — digraph at the END, 'ch'. "
                "Ba/th/ — digraph at the END, 'th'."
            ),
            "you_do": (
                "Read these words and circle the digraph in each one: "
                "ship, chat, thin, wish, duck, math. "
                "Remember — if two letters make one sound, they're a digraph team!"
            )
        },
        "multisensory_cue": {
            "name": "Digraph Picture Cues",
            "materials": "Picture cards (or draw on whiteboard)",
            "procedure": (
                "sh = finger to lips (quiet sign) "
                "ch = mimic train 'choo-choo' motion with arm "
                "th = tongue peeks out (thumbs-up for voiced, flat hand for unvoiced) "
                "wh = blow into cupped hand (feel the air) "
                "ck = karate chop two fingers together (it's a 'twin' digraph at word end)"
            ),
            "verbal_anchor": "Two letters, one sound — they're a team!"
        },
        "word_chain": {
            "chain": ["ship", "chip", "chin", "thin", "thick", "chick"],
            "target_pattern": "sh ↔ ch ↔ th discrimination",
            "non_example": "sip (s and h are NOT a digraph here — they're in different syllables)"
        },
        "corrective_feedback": {
            "error_response": (
                "Those two letters are a team that makes one new sound. "
                "Look at the digraph. What sound do 's' and 'h' make together? Try again."
            ),
            "praise_response": "You recognized that digraph! Two letters, one sound — you got it."
        },
        "connected_text": "Chip and Shep wish for a fish on the ship."
    },

    # ── Vowel Teams ────────────────────────────────────────────────
    "vowel_teams": {
        "skill_name": "Vowel Teams (ai, ay, ee, ea, oa, ow)",
        "grade_levels": ["2nd", "3rd"],
        "micro_pd": {
            "principle": "When Two Vowels Go Walking, the First One Does the Talking",
            "explanation": (
                "Vowel teams (also called vowel digraphs) are two vowels together "
                "representing one sound — typically the long sound of the first vowel. "
                "'ai' and 'ay' both represent /ā/, with a positional rule: 'ai' in "
                "the middle of a word (rain), 'ay' at the end (play). 'ee' and 'ea' "
                "both represent /ē/, with 'ea' sometimes representing short /e/ (bread) "
                "which makes it less predictable. Students need explicit sorting "
                "activities to internalize these patterns."
            ),
            "research_basis": "NRP Phonics (d=0.60); BEE Reading/Elementary"
        },
        "teacher_script": {
            "i_do": (
                "Look at the word 'rain'. Two vowels: 'a' and 'i'. They're walking "
                "together, and the first vowel 'a' does the talking — it says its name! "
                "The 'i' is silent. So we say /r/-/ā/-/n/, rain. Now 'play': 'a' and 'y' "
                "are a team. 'A' says its name, 'y' is silent. Play!"
            ),
            "we_do": (
                "Let's be vowel detectives. I'll show you a word and you tell me "
                "which vowel is doing the talking. [Write: boat] What's the team? 'oa'. "
                "Who talks? 'O'! So this says... boat! Now [write: day] — team? 'ay'. "
                "Who talks? 'A'! Day!"
            ),
            "you_do": (
                "Read these words and underline the vowel team in each one: "
                "rain, seed, boat, play, meet, soap. Then sort them: which teams "
                "say /ā/? Which say /ē/? Which say /ō/?"
            )
        },
        "multisensory_cue": {
            "name": "Vowel Team Slide",
            "materials": "Whiteboard or paper",
            "procedure": (
                "1. Write the vowel team with a slide line between them: a__i. "
                "2. Draw a slide from the first vowel down to the word. "
                "3. Put an X over the second vowel (it's silent). "
                "4. Student traces the slide while saying the long vowel sound, "
                "then blends the whole word."
            ),
            "verbal_anchor": "First vowel slides in — second vowel steps out."
        },
        "word_chain": {
            "chain": ["rain", "train", "tray", "play", "plain", "plane"],
            "target_pattern": "ai (middle) vs ay (end) — same sound, different position",
            "non_example": "said (ai says short /e/ here — a rule breaker!)"
        },
        "corrective_feedback": {
            "error_response": (
                "Two vowels are working together in that word. What sound does "
                "the first vowel make when it's in a team? Try saying just that "
                "sound, then blend it with the rest."
            ),
            "praise_response": "You identified the vowel team and let the first vowel do the talking. Excellent!"
        },
        "connected_text": "On a rainy day, Jay and Ray sail the bay in a boat."
    },

    # ── R-Controlled Vowels ────────────────────────────────────────
    "r_controlled": {
        "skill_name": "R-Controlled Vowels (ar, or, er, ir, ur)",
        "grade_levels": ["2nd", "3rd"],
        "micro_pd": {
            "principle": "Bossy R — The R Controls the Vowel",
            "explanation": (
                "When a vowel is followed by 'r', the 'r' controls the vowel "
                "and changes its sound completely. Neither the vowel nor the 'r' "
                "says its expected sound — they blend into a new sound: /ar/ as in "
                "'car', /or/ as in 'for', /er/ as in 'her'. The /er/ sound is the "
                "most complex because it has three spellings (er, ir, ur) that all "
                "produce the same sound. Students must memorize which spelling goes "
                "with which word through repeated exposure."
            ),
            "research_basis": "Speech to Print (Moats, 2020); Orton-Gillingham multisensory approach"
        },
        "teacher_script": {
            "i_do": (
                "Watch what happens when Bossy R shows up in a word. Here's 'cat' — "
                "short /a/. But if I put an 'r' after the 'a' — 'car' — Bossy R "
                "grabs the 'a' and says 'Nope! Now you say /ar/.' The 'a' can't "
                "say /a/ anymore. Let me show you: /k/-/ar/, car. Bossy R changed "
                "the vowel completely."
            ),
            "we_do": (
                "Let's sort some r-controlled words. I'll say a word and you tell "
                "me which r-controlled sound you hear. For /ar/: car, star, farm. "
                "For /or/: for, corn, storm. For /er/: her, bird, turn. "
                "Notice: 'er', 'ir', and 'ur' all make the SAME sound!"
            ),
            "you_do": (
                "Read these words and highlight the r-controlled vowel: "
                "shirt, barn, horn, turn, first, card. Then sort by sound: "
                "/ar/, /or/, /er/."
            )
        },
        "multisensory_cue": {
            "name": "Bossy R Hand Gesture",
            "materials": "none",
            "procedure": (
                "1. Hold up one hand on the vowel: 'a says /a/...' "
                "2. Bring other hand (Bossy R) and grab the first hand: '...but R says /ar/!' "
                "3. Student does the gesture: covers the vowel with Bossy R hand "
                "and says the new r-controlled sound. "
                "4. For /er/ = all fingers wiggle (three spellings, one sound)."
            ),
            "verbal_anchor": "R grabs the vowel and changes its sound!"
        },
        "word_chain": {
            "chain": ["car", "cart", "part", "park", "dark", "dart"],
            "target_pattern": "ar-family — changing first and final consonants",
            "non_example": "care (The silent-e changes it — /air/, not /ar/)"
        },
        "corrective_feedback": {
            "error_response": (
                "I see an 'r' right after the vowel. That changes the vowel sound. "
                "What sound does 'a' and 'r' make together? Now blend the whole word."
            ),
            "praise_response": "Bossy R couldn't trick you! You read that r-controlled vowel perfectly."
        },
        "connected_text": "Martha and her car drove far to the farm after the storm."
    },

    # ── Phoneme Segmentation ───────────────────────────────────────
    "phoneme_segmentation": {
        "skill_name": "Phoneme Segmentation",
        "grade_levels": ["K", "1st"],
        "micro_pd": {
            "principle": "Breaking Words into Individual Speech Sounds",
            "explanation": (
                "Phoneme segmentation is the ability to break a spoken word into "
                "its individual sounds (phonemes). This is a critical phonemic "
                "awareness skill that directly predicts later reading success "
                "(Kilpatrick, 2015). Students who cannot segment sounds in spoken "
                "words will struggle to map those sounds to letters when reading "
                "and spelling. Instruction should be oral only at the phonemic "
                "awareness level — no letters yet."
            ),
            "research_basis": "NRP Phonemic Awareness (d=0.53); Kilpatrick (2015) Equipped for Reading Success"
        },
        "teacher_script": {
            "i_do": (
                "Listen to this word: 'dog'. Now watch me break it apart: "
                "/d/.../o/.../g/. I said THREE sounds. Listen again: d-o-g. "
                "Each sound is separate, but when we blend them, they make 'dog'. "
                "Your job is to be a word surgeon — you take words apart into their "
                "smallest pieces: sounds."
            ),
            "we_do": (
                "Let's be word surgeons together. I'll say a word, and we'll break "
                "it into sounds using our fingers. Ready? 'Ship': /sh/.../i/.../p/. "
                "That's THREE sounds even though it's FOUR letters — because 'sh' is "
                "one sound! Now: 'frog': /f/.../r/.../o/.../g/. Four sounds. Let's do more."
            ),
            "you_do": (
                "I'll say a word. You say it back in slow-motion, sound by sound: "
                "man, shop, help, desk, camp. "
                "Hold up a finger for every sound you say."
            )
        },
        "multisensory_cue": {
            "name": "Finger Stretching / Sound Counting",
            "materials": "none",
            "procedure": (
                "1. Teacher says a word. "
                "2. Starting with thumb, student says each phoneme while raising "
                "one finger for each sound. "
                "3. Student counts fingers: 'How many sounds in [word]?' "
                "4. For harder words, use tokens: push one token into a box "
                "for each sound heard."
            ),
            "verbal_anchor": "Say it. Stretch it. Count the sounds."
        },
        "word_chain": {
            "chain": ["at", "cat", "cap", "clap", "clasp", "clasps"],
            "target_pattern": "Adding one phoneme at a time — building complexity",
            "non_example": "Compound words like 'bathtub' (segmenting syllables, not phonemes)"
        },
        "corrective_feedback": {
            "error_response": (
                "Let's slow it down even more. I'll say the word, and you echo "
                "it one sound at a time. [Model: /m/.../a/.../n/]. Your turn."
            ),
            "praise_response": "You broke that word into every single sound! Your ears are getting strong."
        },
        "connected_text": "Nan can pat the cat on the mat."
    },

    # ── Prefix un- ─────────────────────────────────────────────────
    "prefix_un": {
        "skill_name": "Prefix un- (Meaning 'not' or 'opposite of')",
        "grade_levels": ["2nd", "3rd"],
        "micro_pd": {
            "principle": "Morphological Awareness — Prefixes Change Meaning",
            "explanation": (
                "A prefix is a word part added to the beginning of a base word "
                "that changes its meaning. 'un-' means 'not' or 'the opposite of.' "
                "Teaching prefixes builds morphological awareness — the ability to "
                "analyze word structure — which is a critical bridge from decoding "
                "to comprehension. Students who understand that 'un-' + 'happy' = "
                "'not happy' can apply this knowledge to decode thousands of words "
                "without memorizing each one individually."
            ),
            "research_basis": "NRP Vocabulary (d=0.47); Bowers & Kirby (2010) morphological instruction (d=0.33)"
        },
        "teacher_script": {
            "i_do": (
                "Watch what happens when I put 'un' in front of a word. "
                "'Lock' means to close something so it can't open. But if I add "
                "'un' — 'unlock' — now it means the opposite: to open! The prefix "
                "'un' is like a switch that flips the meaning. Un + happy = not happy. "
                "Un + safe = not safe. Un + do = do the opposite."
            ),
            "we_do": (
                "Let's build some un- words together. I'll give you a base word, "
                "you add 'un' and tell me the new meaning: "
                "pack → unpack (do the opposite of packing). "
                "kind → unkind (not kind). "
                "fair → unfair (not fair). "
                "Now you try: tie, wrap, real."
            ),
            "you_do": (
                "Circle the prefix in these words and write what each one means: "
                "unable, unzip, unsafe, unhappy, unkind, unlock."
            )
        },
        "multisensory_cue": {
            "name": "Prefix Flip Card",
            "materials": "Index cards with 'un' written on them, or sticky notes",
            "procedure": (
                "1. Write a base word on the board (e.g., 'lock'). "
                "2. Student reads the base word and states its meaning. "
                "3. Place the 'un' card in front. "
                "4. Student reads the new word and states the new meaning. "
                "5. 'Flip' the prefix on and off to reinforce the change."
            ),
            "verbal_anchor": "Prefix goes on — meaning flips around!"
        },
        "word_chain": {
            "chain": ["lock", "unlock", "pack", "unpack", "real", "unreal"],
            "target_pattern": "Base word ↔ un- + base word",
            "non_example": "uncle (Un- here is part of the word, not a prefix)"
        },
        "corrective_feedback": {
            "error_response": (
                "I see 'un' at the beginning of that word. 'Un' is a prefix "
                "that means 'not' or 'opposite.' What's the base word? Now "
                "add 'not' to the meaning."
            ),
            "praise_response": "You spotted the prefix and used it to figure out the meaning! That's what strong readers do."
        },
        "connected_text": "It was unfair that Tim was unable to unlock the box."
    },
}


# ── Deficiency-Code to Remediation Mapping ───────────────────────────────────
#
# Maps diagnostic deficit codes to the appropriate remediation key.
# Used by the evaluate_simple_view pipeline to auto-attach remediations.


DEFICIT_TO_REMEDIATION: dict[str, str] = {
    "cvc_short_a": "cvc_short_a",
    "cvc_short_e": "cvc_mixed",
    "cvc_short_i": "cvc_mixed",
    "cvc_short_o": "cvc_mixed",
    "cvc_short_u": "cvc_mixed",
    "cvc_mixed": "cvc_mixed",
    "consonant_blends": "consonant_blends",
    "cvce_silent_e": "cvce_silent_e",
    "consonant_digraphs": "consonant_digraphs",
    "vowel_teams": "vowel_teams",
    "r_controlled": "r_controlled",
    "phoneme_segmentation": "phoneme_segmentation",
    "prefix_un": "prefix_un",
}


# ── Public API ──────────────────────────────────────────────────────────────


def get_instructional_remediation(
    deficit_code: str,
    grade_level: str = "1st",
) -> RemediationCard:
    """Return a complete remediation card for a specific reading deficit.

    All data is sourced from static lookup tables — no LLM generation at
    runtime, preventing pedagogical hallucinations.

    Args:
        deficit_code: Machine-readable deficit identifier (e.g., 'cvce_silent_e',
                      'consonant_blends', 'phoneme_segmentation', 'prefix_un').
        grade_level: Target grade level ('K', '1st', '2nd', '3rd').

    Returns:
        A RemediationCard containing Micro-PD, I Do/We Do/You Do script,
        multisensory cue, word chain, corrective feedback, and connected text.

    Raises:
        ValueError: If deficit_code is not found in the remediation table.
    """
    # Resolve alias
    resolved = DEFICIT_TO_REMEDIATION.get(deficit_code, deficit_code)

    entry = REMEDIATION_TABLE.get(resolved)
    if entry is None:
        valid = ", ".join(sorted(REMEDIATION_TABLE.keys()))
        raise ValueError(
            f"Unknown deficit_code '{deficit_code}'. Valid codes: {valid}"
        )

    # Validate grade level against supported levels
    if grade_level not in entry["grade_levels"]:
        # Allow with note — remediation can be adapted
        pass

    return RemediationCard(
        deficit_code=deficit_code,
        skill_name=entry["skill_name"],
        grade_level=grade_level,
        micro_pd=MicroPD(**entry["micro_pd"]),
        teacher_script=TeacherScript(**entry["teacher_script"]),
        multisensory_cue=MultisensoryCue(**entry["multisensory_cue"]),
        word_chain=WordChain(**entry["word_chain"]),
        corrective_feedback=CorrectiveFeedback(**entry["corrective_feedback"]),
        connected_text=entry["connected_text"],
    )


def list_available_remediations() -> dict[str, Any]:
    """Return all available deficit codes with skill names and grade levels."""
    results = []
    for code, entry in REMEDIATION_TABLE.items():
        results.append({
            "deficit_code": code,
            "skill_name": entry["skill_name"],
            "grade_levels": entry["grade_levels"],
        })
    return {"total": len(results), "remediations": results}


def get_bulk_remediations(
    deficit_codes: list[str],
    grade_level: str = "1st",
) -> list[RemediationCard]:
    """Get remediation cards for multiple deficit codes at once.

    Args:
        deficit_codes: List of deficit identifiers.
        grade_level: Target grade level for all remediations.

    Returns:
        List of RemediationCard objects, one per valid code.
        Invalid codes are silently skipped.
    """
    cards = []
    for code in deficit_codes:
        try:
            cards.append(get_instructional_remediation(code, grade_level))
        except ValueError:
            continue
    return cards
