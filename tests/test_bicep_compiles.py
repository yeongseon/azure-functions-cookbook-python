"""Regression guard for #377: every shipped recipe main.bicep must compile
without errors (not just the specific BCP025/BCP327/BCP037 diagnostics this
issue originally reported).

Skips cleanly if the Bicep CLI is not installed -- this is a supplementary
compile-time check, not the sole source of truth; see
tests/test_bicep_linux_plans.py for the targeted, structural (CLI-independent)
Linux-plan and duplicate-properties checks.

The fake-compiler tests below need no Bicep CLI and pin that the checker fails
closed on a crashed compiler and on an empty template inventory (#438).
"""

from __future__ import annotations

import os
from pathlib import Path
import shutil

import pytest

from tools import compile_bicep_templates
from tools.compile_bicep_templates import compile_all_templates


def test_every_recipe_bicep_template_compiles_without_errors() -> None:
    bicep = os.environ.get("BICEP_CLI") or shutil.which("bicep")
    if not bicep:
        pytest.skip("Bicep CLI not installed; set BICEP_CLI or install it to run this check.")

    failures = compile_all_templates(bicep)

    assert failures == [], "\n\n".join(
        f"{label}:\n{diagnostics}" for label, diagnostics in failures
    )


def _compiler(tmp_path: Path, shell_body: str) -> str:
    """A fake ``bicep`` executable whose behaviour is the given ``sh`` snippet."""
    script = tmp_path / "bicep"
    script.write_text(f"#!/bin/sh\n{shell_body}\n")
    script.chmod(0o755)
    return str(script)


@pytest.fixture
def one_template(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    examples = tmp_path / "examples"
    (examples / "recipe").mkdir(parents=True)
    (examples / "recipe" / "main.bicep").write_text("param name string\n")
    monkeypatch.setattr(compile_bicep_templates, "EXAMPLES", examples)


@pytest.mark.usefixtures("one_template")
def test_compiler_that_exits_non_zero_fails_even_without_error_text(tmp_path: Path) -> None:
    """Offline: a crashed compiler is a failure although it never prints ``Error ``."""
    failures = compile_all_templates(_compiler(tmp_path, "echo crashed >&2\nexit 1"))

    assert [label for label, _ in failures] == ["recipe/main.bicep"]


@pytest.mark.usefixtures("one_template")
def test_warnings_with_a_zero_exit_status_still_pass(tmp_path: Path) -> None:
    """Offline: only a non-zero exit or an ``Error `` diagnostic fails; warnings do not."""
    assert compile_all_templates(_compiler(tmp_path, "echo 'Warning no-unused-params'")) == []


def test_no_templates_is_a_failure_not_a_pass(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Offline: an empty template inventory cannot report success."""
    (tmp_path / "empty").mkdir()
    monkeypatch.setattr(compile_bicep_templates, "EXAMPLES", tmp_path / "empty")

    failures = compile_all_templates(_compiler(tmp_path, "exit 0"))

    assert [label for label, _ in failures] == ["examples/**/main.bicep"]


@pytest.mark.usefixtures("one_template")
def test_cli_exits_non_zero_when_the_compiler_crashes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Offline: the CI entry point (``tools/compile_bicep_templates.py``) fails on a crash."""
    monkeypatch.setenv("BICEP_CLI", _compiler(tmp_path, "echo crashed >&2\nexit 1"))

    assert compile_bicep_templates.main() == 1
    assert "1 template(s) failed to compile." in capsys.readouterr().err
