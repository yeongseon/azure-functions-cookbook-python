"""Contract for the library / repository-infrastructure test split (#468).

``repo_infra`` marks tests of repository tooling (``tools/``, ``scripts/``, workflows, Makefile,
packaging, generated artifacts). The two lanes must partition the default suite exactly, so
nothing is dropped, and CI must run both lanes plus the unchanged combined coverage gate.
"""

from __future__ import annotations

from pathlib import Path
import subprocess
import sys
import tomllib

import pytest
import yaml

pytestmark = pytest.mark.repo_infra

ROOT = Path(__file__).resolve().parents[1]
EXCLUDED = "e2e or smoke or worker_registration"
LIBRARY = f"not ({EXCLUDED} or repo_infra)"
INFRA = f"repo_infra and not ({EXCLUDED})"


def _collect(expression: str | None) -> set[str]:
    command = [sys.executable, "-m", "pytest", "--collect-only", "-q", "-o", "addopts="]
    command += ["--continue-on-collection-errors"]
    command += ["-p", "no:cacheprovider", "tests"]
    if expression is not None:
        command[command.index("tests") : command.index("tests")] = ["-m", expression]
    result = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, check=False)
    return {
        line for line in result.stdout.splitlines() if line.startswith("tests/") and "::" in line
    }


def test_repo_infra_marker_is_registered() -> None:
    config = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    markers = config["tool"]["pytest"]["ini_options"]["markers"]
    assert any(marker.startswith("repo_infra:") for marker in markers)


def test_lanes_partition_the_default_suite() -> None:
    """The library lane and the infrastructure lane together are exactly the default selection."""
    default = _collect(f"not ({EXCLUDED})")
    library, infra = _collect(LIBRARY), _collect(INFRA)

    assert library and infra
    assert library.isdisjoint(infra)
    assert library | infra == default


def test_hatch_lanes_use_the_same_selections() -> None:
    scripts = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))["tool"]["hatch"][
        "envs"
    ]["default"]["scripts"]

    assert f"-m '{LIBRARY}'" in scripts["test-library"]
    assert f"-m '{INFRA}'" in scripts["test-infra"]
    assert scripts["test"] == "pytest -v tests"  # the full suite, unchanged


def test_ci_runs_both_lanes_and_keeps_every_coverage_gate() -> None:
    workflow = yaml.safe_load((ROOT / ".github/workflows/ci-test.yml").read_text(encoding="utf-8"))
    runs = [step.get("run", "") for step in workflow["jobs"]["test"]["steps"]]

    assert any(f"pytest -m '{LIBRARY}'" in run for run in runs)
    assert any(f"pytest -m '{INFRA}'" in run and "--cov-append" in run for run in runs)
    for gate in (
        "coverage report --include='src/*' --fail-under=95",
        "coverage report --include='tools/*' --fail-under=95",
    ):
        assert gate in runs
    # The combined gate (fail_under from pyproject) runs after both lanes.
    assert runs.index("coverage report") > max(
        index for index, run in enumerate(runs) if run.startswith("pytest -m")
    )
    # The former single run is gone: no step runs the whole suite unpartitioned.
    assert not [run for run in runs if run.startswith("pytest ") and " -m " not in run]


def test_combined_coverage_threshold_is_still_configured() -> None:
    config = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))["tool"][
        "coverage"
    ]

    assert config["report"]["fail_under"] == 95
    assert config["run"]["source"] == ["src/azure_functions_python_cookbook", "tools"]


def test_ci_required_aggregates_the_test_job() -> None:
    workflow = yaml.safe_load((ROOT / ".github/workflows/ci-test.yml").read_text(encoding="utf-8"))

    assert "test" in workflow["jobs"]["ci-required"]["needs"]
    assert "pull_request" in workflow[True]  # PyYAML parses the `on:` key as True


def test_makefile_exposes_both_lanes_without_changing_test() -> None:
    plan = subprocess.run(
        ["make", "-n", "--no-print-directory", "-C", str(ROOT), "test-library", "test-infra"],
        capture_output=True,
        text=True,
        check=True,
    ).stdout

    assert "run test-library" in plan
    assert "run test-infra" in plan
