"""Tests for loading a school's own scope and sequence."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.tools import scope_engine
from src.tools.decodability import MANDATORY_HEART_WORDS, check_decodability
from src.tools.scope_engine import (
    analyze_word,
    configure_scope,
    load_scope_file,
    reset_scope,
    scope_for,
    validate_scope_config,
)

EXAMPLE = Path(__file__).resolve().parent.parent / "examples" / "custom_scope.json"


@pytest.fixture(autouse=True)
def restore_default_scope():
    yield
    reset_scope()


def test_example_file_is_valid() -> None:
    assert validate_scope_config(json.loads(EXAMPLE.read_text())) == []


def test_custom_sequence_changes_what_is_decodable() -> None:
    assert analyze_word("rain", scope_for("1", None))["status"] == "off_scope"
    load_scope_file(str(EXAMPLE))
    assert analyze_word("rain", scope_for("1", None))["status"] == "decodable"
    # Default grade 1 already teaches "sh" at unit 2 of 10; this school teaches it too.
    assert analyze_word("ship", scope_for("1", None))["status"] == "decodable"


def test_custom_units_per_grade_gate_groups() -> None:
    load_scope_file(str(EXAMPLE))
    assert scope_engine.UNITS_PER_GRADE == 6
    # Unit 1 of 6 in grade 1 teaches only the first group (ff ll ss zz ck).
    assert analyze_word("sh" + "ip", scope_for("1", 1))["status"] == "off_scope"
    assert analyze_word("sh" + "ip", scope_for("1", 2))["status"] == "decodable"


def test_heart_words_and_checker_follow_the_custom_file() -> None:
    load_scope_file(str(EXAMPLE))
    assert "and" in MANDATORY_HEART_WORDS
    assert "said" in MANDATORY_HEART_WORDS
    assert "pull" not in MANDATORY_HEART_WORDS
    result = check_decodability("The cat said and.", "1")
    assert result["scope_name"].startswith("Example school")


def test_reset_restores_defaults() -> None:
    default_name = scope_engine.SCOPE_NAME
    load_scope_file(str(EXAMPLE))
    reset_scope()
    assert scope_engine.SCOPE_NAME == default_name
    assert scope_engine.UNITS_PER_GRADE == 10
    assert "pull" in MANDATORY_HEART_WORDS
    assert analyze_word("rain", scope_for("1", None))["status"] == "off_scope"


@pytest.mark.parametrize(
    "config, fragment",
    [
        ([], "JSON object"),
        ({}, "grades"),
        ({"grades": {"7": {}}}, "not supported"),
        ({"grades": {"K": {"groups": [["A1"]]}}}, "lowercase"),
        ({"grades": {"K": {"groups": [["@nonsense"]]}}}, "unknown rule"),
        ({"grades": {"K": {"groups": [[]]}}}, "non-empty"),
        ({"grades": {"K": {"heart_words": ["ok", 5]}}}, "heart_words"),
        ({"grades": {"K": {}}, "units_per_grade": 0}, "units_per_grade"),
    ],
)
def test_invalid_configs_are_reported(config, fragment: str) -> None:
    problems = validate_scope_config(config)
    assert any(fragment in p for p in problems), problems
    with pytest.raises(ValueError):
        configure_scope(config)


def test_missing_or_broken_file_gives_a_clear_error(tmp_path) -> None:
    with pytest.raises(ValueError, match="not found"):
        load_scope_file(str(tmp_path / "nope.json"))
    bad = tmp_path / "bad.json"
    bad.write_text("{not json")
    with pytest.raises(ValueError, match="not valid JSON"):
        load_scope_file(str(bad))


def test_a_failed_load_leaves_the_current_scope_untouched() -> None:
    before = {k: [list(g) for g in v] for k, v in scope_engine.SCOPE_GROUPS.items()}
    with pytest.raises(ValueError):
        configure_scope({"grades": {"K": {"groups": [["@nonsense"]]}}})
    assert before == scope_engine.SCOPE_GROUPS


def test_server_cli_rejects_a_bad_scope_file(tmp_path) -> None:
    import subprocess
    import sys

    bad = tmp_path / "bad.json"
    bad.write_text('{"grades": {"K": {"groups": [["@nonsense"]]}}}')
    root = Path(__file__).resolve().parent.parent
    proc = subprocess.run(
        [sys.executable, str(root / "server.py"), "--scope-file", str(bad), "--seed-only"],
        capture_output=True, text=True, cwd=root, timeout=60,
    )
    assert proc.returncode == 2
    assert "unknown rule" in proc.stderr
