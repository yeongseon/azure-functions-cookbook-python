"""Regression tests for scripts/check_ecosystem_counts.py (#460)."""

from __future__ import annotations

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import check_ecosystem_counts as checker  # noqa: E402


def test_documented_counts_match_declared_dependencies() -> None:
    assert checker.find_drift(checker.count_declaring()) == []


def test_drift_is_reported_for_a_wrong_count() -> None:
    counts = checker.count_declaring()
    counts["azure-functions-openapi"] += 1
    problems = checker.find_drift(counts)
    assert any("azure-functions-openapi" in p for p in problems)
    assert len(problems) == 5  # four READMEs and docs/toolkit-usage.md
