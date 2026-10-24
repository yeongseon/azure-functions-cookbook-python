from pathlib import Path

import yaml

WORKFLOW = Path(__file__).resolve().parents[1] / ".github" / "workflows" / "ci-smoke.yml"
EXPECTED_PATHS = [
    "examples/**",
    "src/**",
    "tests/e2e/**",
    "tests/_isolation.py",
    "tests/__init__.py",
    "Makefile",
    "README.md",
    "pyproject.toml",
    ".github/workflows/ci-smoke.yml",
]


def test_push_and_pull_request_filters_match_smoke_inputs() -> None:
    # Given: the non-required smoke workflow configuration.
    workflow = yaml.load(WORKFLOW.read_text(encoding="utf-8"), Loader=yaml.BaseLoader)

    # When: its automatic-event path filters are inspected.
    triggers = workflow["on"]

    # Then: push and pull requests use the same minimal consumed-input list.
    assert triggers["pull_request"]["paths"] == EXPECTED_PATHS
    assert triggers["push"]["paths"] == EXPECTED_PATHS


def test_e2e_http_job_fails_instead_of_skipping() -> None:
    """Offline: the job running every ``tests/e2e`` test fails on a skipped test (#439)."""
    workflow = yaml.load(WORKFLOW.read_text(encoding="utf-8"), Loader=yaml.BaseLoader)

    assert workflow["jobs"]["e2e-http"]["env"]["PYTEST_ADDOPTS"] == "-p tools.pytest_fail_on_skip"
