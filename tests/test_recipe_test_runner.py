"""Tests for ``scripts/run_recipe_tests.py``: the per-recipe lane must fail closed (#438)."""

from __future__ import annotations

import importlib.util
import os
from pathlib import Path
import subprocess
import sys
import time
from typing import Any

import pytest

pytestmark = pytest.mark.repo_infra

_SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "run_recipe_tests.py"
_spec = importlib.util.spec_from_file_location("run_recipe_tests", _SCRIPT)
assert _spec and _spec.loader
runner = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(runner)

_REAL_POPEN = subprocess.Popen


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

    def popen(command: list[str], **kwargs: Any) -> subprocess.Popen[bytes]:
        commands.append(command)
        return _REAL_POPEN([sys.executable, *command[command.index("python") + 1 :]], **kwargs)

    monkeypatch.setattr(subprocess, "Popen", popen)
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


def test_hanging_suite_is_killed_with_its_children_and_named(
    examples: Path,
    uv_commands: list[list[str]],
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """Offline: a hung suite fails by name and its grandchild process does not survive."""
    pid_file = tmp_path / "grandchild.pid"
    body = (
        "import subprocess, sys, time\n\n"
        "def test_hang():\n"
        "    child = subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(600)'])\n"
        f"    open({str(pid_file)!r}, 'w').write(str(child.pid))\n"
        "    time.sleep(600)\n"
    )
    _recipe(examples, "hung", body)
    monkeypatch.setenv("RECIPE_TEST_TIMEOUT_SECONDS", "5")

    assert runner.main() == 1

    assert "category/hung: suite timed out after 5s" in capsys.readouterr().err
    grandchild = int(pid_file.read_text())
    with pytest.raises(ProcessLookupError):
        for _ in range(50):
            os.kill(grandchild, 0)
            time.sleep(0.1)
        os.kill(grandchild, 0)
        os.kill(grandchild, 9)
        pytest.fail("grandchild survived the timeout")


@pytest.mark.parametrize("value", ["abc", "0", "-3"])
def test_invalid_timeout_override_is_rejected(value: str, monkeypatch: pytest.MonkeyPatch) -> None:
    """Offline: a malformed timeout cannot silently disable the bound."""
    monkeypatch.setenv("RECIPE_TEST_TIMEOUT_SECONDS", value)

    with pytest.raises(SystemExit):
        runner.suite_timeout()
