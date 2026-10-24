"""Tests for ``scripts/run_recipe_tests.py``: the per-recipe lane must fail closed (#438)."""

from __future__ import annotations

import importlib.util
from pathlib import Path
import subprocess
import sys
from typing import Any

import pytest

_SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "run_recipe_tests.py"
_spec = importlib.util.spec_from_file_location("run_recipe_tests", _SCRIPT)
assert _spec and _spec.loader
runner = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(runner)

_REAL_RUN = subprocess.run


def _recipe(examples: Path, name: str, test_body: str, *, pyproject: bool = True) -> None:
    tests = examples / "category" / name / "tests"
    tests.mkdir(parents=True)
    (tests / "test_recipe.py").write_text(test_body)
    if pyproject:
        (tests.parent / "pyproject.toml").write_text('[project]\nname = "recipe"\nversion = "0"\n')


@pytest.fixture
def examples(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    root = tmp_path / "examples"
    root.mkdir()
    monkeypatch.setattr(runner, "EXAMPLES", root)
    return root


@pytest.fixture
def uv_commands(monkeypatch: pytest.MonkeyPatch) -> list[list[str]]:
    """Record every ``uv run`` command and run its pytest part on this interpreter.

    uv only builds the recipe's environment; pytest, the plugin and the exit status are real.
    """
    commands: list[list[str]] = []

    def run(command: list[str], **kwargs: Any) -> subprocess.CompletedProcess[bytes]:
        commands.append(command)
        return _REAL_RUN([sys.executable, *command[command.index("python") + 1 :]], **kwargs)

    monkeypatch.setattr(subprocess, "run", run)
    return commands


def test_passing_suite_runs_isolated_on_the_invoking_interpreter(
    examples: Path, uv_commands: list[list[str]], capsys: pytest.CaptureFixture[str]
) -> None:
    """Offline: a passing suite exits 0 in an isolated env built on ``sys.executable``."""
    _recipe(examples, "ok", "def test_ok(): ...\n")

    assert runner.main() == 0

    (command,) = uv_commands
    assert command[command.index("--python") + 1] == sys.executable
    assert "--isolated" in command
    assert "Recipe tests passed for 1 projects." in capsys.readouterr().out


def test_suite_with_only_skipped_tests_fails(
    examples: Path, uv_commands: list[list[str]], capsys: pytest.CaptureFixture[str]
) -> None:
    """Offline: a suite that skips its tests is reported as failed, never as passed."""
    _recipe(examples, "skipped", "import pytest\n\n@pytest.mark.skip\ndef test_x(): ...\n")

    assert runner.main() == 1
    assert "category/skipped: suite failed" in capsys.readouterr().err


def test_suite_without_pyproject_is_reported_and_never_silently_dropped(
    examples: Path, uv_commands: list[list[str]], capsys: pytest.CaptureFixture[str]
) -> None:
    """Offline: tests that cannot be run for lack of ``pyproject.toml`` fail the lane."""
    _recipe(examples, "orphan", "def test_x(): ...\n", pyproject=False)

    assert runner.main() == 1
    assert "category/orphan: has tests but no pyproject.toml" in capsys.readouterr().err
    assert uv_commands == []


def test_zero_suites_is_a_failure_not_a_pass(
    examples: Path, uv_commands: list[list[str]], capsys: pytest.CaptureFixture[str]
) -> None:
    """Offline: an inventory with no recipe suites cannot report success."""
    assert runner.main() == 1
    assert "no recipe test suites found" in capsys.readouterr().err
