from pathlib import Path

import pytest
import yaml

pytestmark = pytest.mark.repo_infra

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
    """Offline: the non-required smoke workflow's push and PR path filters are identical."""
    workflow = yaml.load(WORKFLOW.read_text(encoding="utf-8"), Loader=yaml.BaseLoader)

    triggers = workflow["on"]

    assert triggers["pull_request"]["paths"] == EXPECTED_PATHS
    assert triggers["push"]["paths"] == EXPECTED_PATHS


def test_e2e_http_job_fails_instead_of_skipping() -> None:
    """Offline: the job running every ``tests/e2e`` test fails on a skipped test (#439)."""
    workflow = yaml.load(WORKFLOW.read_text(encoding="utf-8"), Loader=yaml.BaseLoader)

    assert workflow["jobs"]["e2e-http"]["env"]["PYTEST_ADDOPTS"] == "-p tools.pytest_fail_on_skip"
