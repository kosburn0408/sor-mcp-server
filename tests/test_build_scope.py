"""Tests for scripts/build_scope.py (CSV → SOR_SCOPE_PATH JSON)."""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

from src.engine.scope_sequence import DEFAULT_SEQUENCE

_spec = importlib.util.spec_from_file_location(
    "build_scope", Path(__file__).resolve().parents[1] / "scripts" / "build_scope.py"
)
build_scope = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(build_scope)  # type: ignore[union-attr]


def test_default_round_trip(tmp_path: Path) -> None:
    csv_path = tmp_path / "t.csv"
    build_scope.export_default(csv_path)
    seq, warnings = build_scope.build(csv_path)
    assert seq == DEFAULT_SEQUENCE
    assert warnings == []


def test_teacher_notation(tmp_path: Path) -> None:
    p = tmp_path / "p.csv"
    p.write_text('grade,unit,title,patterns,heart_words\nK,1,start,"m; a; sh; ck",the; a\n1,1,silent e,"a_e; -ed; open syllable",who\n')
    seq, _ = build_scope.build(p)
    assert seq["K"][0]["gpcs"] == ["m", "short_a", "sh", "ck"]
    assert seq["1"][0]["gpcs"] == ["vce_a", "suffix_ed", "open_syllable"]


def test_ambiguous_grapheme_warns(tmp_path: Path) -> None:
    p = tmp_path / "p.csv"
    p.write_text("grade,unit,title,patterns,heart_words\n1,1,teams,ea,\n")
    seq, warnings = build_scope.build(p)
    assert seq["1"][0]["gpcs"] == ["vt_ee"]
    assert any("ea" in w for w in warnings)


def test_unknown_pattern_errors(tmp_path: Path) -> None:
    p = tmp_path / "p.csv"
    p.write_text("grade,unit,title,patterns,heart_words\nK,1,x,zzq,\n")
    with pytest.raises(ValueError, match="Unknown pattern"):
        build_scope.build(p)
