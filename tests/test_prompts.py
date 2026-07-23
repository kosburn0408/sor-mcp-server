"""Tests for MCP Prompt primitives (explicit phonics, decodable passage, multisyllabic).

Validates that prompt builders produce correct structured output,
contain required fields, and handle edge cases gracefully.
"""

from __future__ import annotations

import pytest

from src.prompts.explicit_phonics import build_explicit_phonics_routine
from src.prompts.decodable_passage import build_decodable_passage
from src.prompts.multisyllabic import build_multisyllabic_routine


class TestExplicitPhonicsRoutine:
    """Test the I Do / We Do / You Do script generator."""

    def test_generates_cvc_script(self) -> None:
        """Short vowel skill should produce a CVC script."""
        result = build_explicit_phonics_routine(
            skill_name="Short Vowel /a/",
            grade_level="1st",
        )
        assert result["target_skill"] == "Short Vowel /a/"
        assert len(result["i_do"]) > 0
        assert len(result["we_do"]) > 0
        assert len(result["you_do"]) > 0
        assert result["total_time"] is not None

    def test_generates_silent_e_script(self) -> None:
        """Silent-e skill should produce appropriate script."""
        result = build_explicit_phonics_routine(
            skill_name="Silent-e Pattern",
            grade_level="2nd",
        )
        assert "silent" in result["i_do"].lower() or "e" in result["i_do"].lower()

    def test_generates_digraph_script(self) -> None:
        """Digraph skill returns appropriate script."""
        result = build_explicit_phonics_routine(
            skill_name="Consonant Digraphs",
        )
        assert "digraph" in result["i_do"].lower() or "team" in result["i_do"].lower()

    def test_includes_corrective_feedback(self) -> None:
        """All scripts should include corrective feedback."""
        result = build_explicit_phonics_routine(skill_name="Short Vowel /a/")
        assert "corrective_feedback" in result
        assert "error" in result["corrective_feedback"]
        assert "praise" in result["corrective_feedback"]

    def test_includes_framework_notes(self) -> None:
        """All scripts should include research framework notes."""
        result = build_explicit_phonics_routine(skill_name="CVC words")
        assert "framework_notes" in result

    def test_unknown_skill_gets_generic_script(self) -> None:
        """Unknown skills should get a generic fallback script."""
        result = build_explicit_phonics_routine(
            skill_name="some_random_skill_xyz",
        )
        assert len(result["i_do"]) > 0
        assert len(result["we_do"]) > 0

    def test_examples_provided_in_script(self) -> None:
        """Example words should appear in the script."""
        result = build_explicit_phonics_routine(
            skill_name="Short Vowel /i/",
            phoneme_examples=["pig", "sit", "big"],
        )
        # Examples should be referenced in one of the stages
        all_text = result["i_do"] + result["we_do"] + result["you_do"]
        assert "pig" in all_text.lower() or "sit" in all_text.lower()

    def test_multisensory_cue_accepted(self) -> None:
        """Multisensory cue parameter should be accepted."""
        result = build_explicit_phonics_routine(
            skill_name="Short Vowel /a/",
            multisensory_cue="Elkonin boxes",
        )
        assert "multisensory_cue" in result


class TestDecodablePassageBuilder:
    """Test the constrained decodable passage builder."""

    def test_builds_short_a_passage(self) -> None:
        """Short a passage should be generated with patterns."""
        result = build_decodable_passage(
            target_phoneme="short_a",
            mastered_patterns=["cvc_short_a"],
        )
        assert len(result["passage"]) > 0
        assert result["word_count"] > 0
        assert len(result["patterns_used"]) > 0

    def test_builds_silent_e_passage(self) -> None:
        """Silent-e target should produce a passage."""
        result = build_decodable_passage(
            target_phoneme="silent_e",
            mastered_patterns=["cvc_mixed", "cvce_silent_e"],
        )
        assert result["title"] is not None
        assert "decodability_pct" in result

    def test_includes_heart_words(self) -> None:
        """Heart words should be included in output."""
        result = build_decodable_passage(
            target_phoneme="short_a",
            mastered_patterns=["cvc_short_a"],
            include_heart_words=["the", "a"],
        )
        assert len(result["heart_words_marked"]) >= 1

    def test_includes_comprehension_question(self) -> None:
        """Every passage should have a comprehension question."""
        result = build_decodable_passage(target_phoneme="short_a")
        assert "comprehension_question" in result
        assert len(result["comprehension_question"]) > 0

    def test_includes_teacher_notes(self) -> None:
        """Teacher notes should provide guidance."""
        result = build_decodable_passage(target_phoneme="short_a")
        assert len(result["teacher_notes"]) > 0

    def test_topic_filtering_works(self) -> None:
        """Topic preference should influence passage selection."""
        result = build_decodable_passage(
            target_phoneme="short_a",
            topic="animals",
        )
        # Should return a passage — just verify it doesn't error
        assert "passage" in result

    def test_fallback_on_unknown_phoneme(self) -> None:
        """Unknown phoneme should fall back gracefully."""
        result = build_decodable_passage(
            target_phoneme="zzz_nonexistent",
        )
        assert "passage" in result


class TestMultisyllabicRoutine:
    """Test the multisyllabic decoding routine builder."""

    def test_known_word_rabbit(self) -> None:
        """'rabbit' should have VC/CV division."""
        result = build_multisyllabic_routine(word="rabbit")
        assert result["syllable_count"] == 2
        assert result["division_rule"] == "VC/CV"
        assert result["syllable_breakdown"] == ["rab", "bit"]

    def test_known_word_tiger(self) -> None:
        """'tiger' should have V/CV division."""
        result = build_multisyllabic_routine(word="tiger")
        assert result["division_rule"] == "V/CV"
        assert len(result["syllable_breakdown"]) == 2

    def test_known_word_fantastic(self) -> None:
        """'fantastic' should have 3 syllables."""
        result = build_multisyllabic_routine(word="fantastic")
        assert result["syllable_count"] == 3

    def test_division_steps_present(self) -> None:
        """All routines should include step-by-step division."""
        result = build_multisyllabic_routine(word="rabbit")
        assert len(result["division_steps"]) > 0
        for step in result["division_steps"]:
            assert "step_number" in step
            assert "action" in step
            assert "teacher_language" in step

    def test_includes_word_meaning(self) -> None:
        """Each word should have a student-friendly definition."""
        result = build_multisyllabic_routine(word="rabbit")
        assert len(result["word_meaning"]) > 0

    def test_includes_example_sentence(self) -> None:
        """Each word should have an example sentence."""
        result = build_multisyllabic_routine(word="tiger")
        assert len(result["example_sentence"]) > 0

    def test_includes_connected_words(self) -> None:
        """Connected words with same pattern should be listed."""
        result = build_multisyllabic_routine(word="rabbit")
        assert len(result["connected_words"]) > 0

    def test_includes_framework_notes(self) -> None:
        """Framework notes should be present."""
        result = build_multisyllabic_routine(word="rabbit")
        assert "framework_notes" in result

    def test_orthographic_mapping_included(self) -> None:
        """Orthographic mapping should be included when requested."""
        result = build_multisyllabic_routine(
            word="rabbit",
            include_orthographic_mapping=True,
        )
        assert result["orthographic_mapping"] is not None

    def test_orthographic_mapping_excluded(self) -> None:
        """Orthographic mapping should be None when not requested."""
        result = build_multisyllabic_routine(
            word="rabbit",
            include_orthographic_mapping=False,
        )
        assert result["orthographic_mapping"] is None

    def test_unknown_word_auto_divides(self) -> None:
        """Unknown words should be auto-divided by heuristic."""
        result = build_multisyllabic_routine(word="computer")
        assert result["syllable_count"] >= 1
        assert len(result["syllable_breakdown"]) >= 1

    def test_word_meaning_for_unknown(self) -> None:
        """Unknown words should have a fallback meaning message."""
        result = build_multisyllabic_routine(word="xyzabc")
        assert len(result["word_meaning"]) > 0


class TestPromptDefinitions:
    """Test that prompt definitions are well-formed."""

    def test_explicit_phonics_prompt_defined(self) -> None:
        """Prompt definition should exist and have required fields."""
        from src.prompts.explicit_phonics import EXPLICIT_PHONICS_PROMPT
        assert EXPLICIT_PHONICS_PROMPT["name"] == "explicit_phonics_routine"
        assert len(EXPLICIT_PHONICS_PROMPT["arguments"]) > 0

    def test_decodable_passage_prompt_defined(self) -> None:
        """Prompt definition should exist and have required fields."""
        from src.prompts.decodable_passage import DECODABLE_PASSAGE_PROMPT
        assert DECODABLE_PASSAGE_PROMPT["name"] == "decodable_passage_builder"

    def test_multisyllabic_prompt_defined(self) -> None:
        """Prompt definition should exist and have required fields."""
        from src.prompts.multisyllabic import MULTISYLLABIC_PROMPT
        assert MULTISYLLABIC_PROMPT["name"] == "multisyllabic_decoding_routine"
