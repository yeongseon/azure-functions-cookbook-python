import importlib
from pathlib import Path
import runpy
import subprocess
from unittest.mock import patch

import pytest

from tools import compile_bicep_templates as bicep
from tools import lint_hatch_matrix as matrix
from tools import lint_workflow_pins as pins
from tools import verify_scheduled_smoke_selection as selection


@pytest.mark.parametrize(
    "reference,errors",
    [
        ("./local", 0),
        ("owner/action", 1),
        ("owner/action@v1", 1),
        ("owner/action@v1 # pin-exempt: deliberate", 0),
        ("owner/action@" + "a" * 40, 1),
        ("owner/action@" + "a" * 40 + " # v1", 0),
    ],
)
def test_pin_hygiene_rejects_mutable_and_undocumented_refs(reference: str, errors: int) -> None:
    assert len(pins.check_pin_hygiene("name: check\nuses: " + reference, "test.yml")) == errors


@pytest.mark.parametrize("valid", [False, True])
def test_workflow_pin_cli_scans_checkout(tmp_path: Path, valid: bool) -> None:
    workflows = tmp_path / ".github/workflows"
    workflows.mkdir(parents=True)
    (workflows / "test.yml").write_text("uses: ./local" if valid else "uses: owner/action@v1")
    with patch.object(pins, "_repo_root", return_value=tmp_path):
        assert bool(pins.lint()) != valid
        assert pins.main() == (0 if valid else 1)


def test_missing_workflows_are_reported(tmp_path: Path) -> None:
    assert pins.lint(tmp_path)
    assert matrix.lint(tmp_path)
    (tmp_path / "pyproject.toml").write_text("")
    assert matrix.lint(tmp_path) == []


@pytest.mark.parametrize(
    "code,output,expected",
    [
        (0, "file.py: 3\nignored: text", 3),
        (5, "", 0),
        (1, "13 tests collected / 7 deselected / 6 selected", 6),
    ],
)
def test_collection_counts_selected_tests(code: int, output: str, expected: int) -> None:
    with patch.object(
        subprocess, "run", return_value=subprocess.CompletedProcess([], code, output, "")
    ):
        assert selection._collected_count([]) == expected


def test_collection_tool_crash_fails() -> None:
    with (
        patch.object(
            subprocess,
            "run",
            return_value=subprocess.CompletedProcess([], 2, "", "failure"),
        ),
        pytest.raises(SystemExit),
    ):
        selection._collected_count([])


@pytest.mark.parametrize("count,expected", [(0, 1), (2, 0)])
def test_scheduled_selection_cli_requires_every_suite(count: int, expected: int) -> None:
    with patch.object(selection, "_collected_count", return_value=count):
        assert selection.main() == expected


@pytest.mark.parametrize(
    "diagnostics,expected",
    [("Warning warning", []), ("Error BCP025", [("demo/main.bicep", "Error BCP025")])],
)
def test_bicep_compiler_records_real_diagnostics(
    tmp_path: Path, diagnostics: str, expected: list[tuple[str, str]]
) -> None:
    template = tmp_path / "demo/main.bicep"
    template.parent.mkdir()
    template.touch()
    with (
        patch.object(bicep, "EXAMPLES", tmp_path),
        patch.object(
            subprocess,
            "run",
            return_value=subprocess.CompletedProcess([], 0, "", diagnostics),
        ),
    ):
        assert bicep.compile_all_templates("bicep") == expected


@pytest.mark.parametrize(
    "available,failures,expected",
    [(None, [], 1), ("bicep", [], 0), ("bicep", [("demo", "Error")], 1)],
)
def test_bicep_cli_exit_codes(
    available: str | None, failures: list[tuple[str, str]], expected: int
) -> None:
    with (
        patch.object(bicep, "_bicep_cli", return_value=available),
        patch.object(bicep, "compile_all_templates", return_value=failures),
    ):
        assert bicep.main() == expected


def test_bicep_cli_resolves_explicit_path(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("BICEP_CLI", "custom-bicep")
    assert bicep._bicep_cli() == "custom-bicep"


def test_matrix_parser_handles_blank_duplicate_and_nonversion_items() -> None:
    assert matrix.matrix_python_versions(
        'python-version:\n\n  - "3.11"\n  - "3.11"\n  - nope\n'
    ) == ["3.11"]
    assert (
        matrix.check_workflow(
            'python-version: ["3.11", "3.12"]\nmake install\npython -m pytest',
            "ci.yml",
            {"default": "3.11"},
        )
        == []
    )


@pytest.mark.parametrize("errors,expected", [([], 0), (["drift"], 1)])
def test_matrix_cli_reports_errors(errors: list[str], expected: int) -> None:
    with patch.object(matrix, "lint", return_value=errors):
        assert matrix.main() == expected


@pytest.mark.parametrize(
    "module",
    [
        "tools.check_pr_format",
        "tools.compile_bicep_templates",
        "tools.dependency_audit_policy",
        "tools.lint_hatch_matrix",
        "tools.lint_workflow_pins",
        "tools.recipe_security",
        "tools.security_evidence",
        "tools.verify_scheduled_smoke_selection",
    ],
)
def test_script_guard_invokes_cli(module: str) -> None:
    source = importlib.util.find_spec(module)
    assert source and source.origin
    with patch("sys.argv", [source.origin]), patch("builtins.print"), pytest.raises(SystemExit):
        if module == "tools.dependency_audit_policy":
            with patch("subprocess.run", side_effect=OSError("offline")):
                runpy.run_path(source.origin, run_name="__main__")
        elif module == "tools.security_evidence":
            with patch("sys.argv", [source.origin, "semgrep"]):
                runpy.run_path(source.origin, run_name="__main__")
        elif module == "tools.verify_scheduled_smoke_selection":
            with patch("subprocess.run", return_value=subprocess.CompletedProcess([], 5, "", "")):
                runpy.run_path(source.origin, run_name="__main__")
        else:
            runpy.run_path(source.origin, run_name="__main__")
