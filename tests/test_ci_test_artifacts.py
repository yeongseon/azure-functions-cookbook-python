"""Guards for the required test jobs' evidence upload and log hygiene (#428)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

_ROOT = Path(__file__).resolve().parents[1]
_WORKFLOWS = _ROOT / ".github" / "workflows"
_CI_TEST = yaml.safe_load((_WORKFLOWS / "ci-test.yml").read_text(encoding="utf-8"))
_ARTIFACT_ACTION = "actions/upload-artifact@"


def _steps(job: str) -> list[dict[str, Any]]:
    steps: list[dict[str, Any]] = _CI_TEST["jobs"][job]["steps"]
    return steps


def _uploads(job: str) -> list[dict[str, Any]]:
    return [step for step in _steps(job) if str(step.get("uses", "")).startswith(_ARTIFACT_ACTION)]


def _paths(upload: dict[str, Any]) -> list[str]:
    return str(upload["with"]["path"]).split()


def test_matrix_test_job_uploads_junit_and_coverage_even_when_tests_fail() -> None:
    """Offline: every matrix cell uploads JUnit and coverage XML on success and on failure."""
    run = next(step for step in _steps("test") if step.get("name", "").startswith("Run tests"))
    (upload,) = _uploads("test")
    steps = _steps("test")

    assert "--junitxml=test-results/junit.xml" in run["run"]
    assert "--cov-report=xml" in run["run"]
    assert set(_paths(upload)) == {"test-results/junit.xml", "coverage.xml"}
    assert upload["if"] == "always()"
    assert steps.index(upload) > steps.index(run)
    # One artifact per matrix cell, so parallel cells never overwrite each other.
    assert "matrix.python-version" in upload["with"]["name"]
    assert "matrix.resolution" in upload["with"]["name"]


def test_recipe_test_job_uploads_junit_even_when_a_suite_fails() -> None:
    """Offline: the per-recipe job asks the runner for JUnit files and uploads them always."""
    run = next(
        step for step in _steps("recipe-tests") if "run_recipe_tests.py" in step.get("run", "")
    )
    (upload,) = _uploads("recipe-tests")

    directory = run["env"]["RECIPE_TEST_JUNIT_DIR"]
    assert _paths(upload) == [f"{directory}/*.xml"]
    assert upload["if"] == "always()"
    assert _steps("recipe-tests").index(upload) > _steps("recipe-tests").index(run)


def test_test_steps_expose_no_secrets_and_never_dump_locals() -> None:
    """Offline: no secret reaches a test step and no workflow runs pytest with --showlocals."""
    for step in _steps("test") + _steps("recipe-tests"):
        if "pytest" in step.get("run", "") or "run_recipe_tests" in step.get("run", ""):
            assert "secrets." not in yaml.safe_dump(step), step.get("name")

    for workflow in sorted(_WORKFLOWS.glob("*.yml")):
        document = yaml.safe_load(workflow.read_text(encoding="utf-8"))
        for job in document["jobs"].values():
            for step in job.get("steps", []):
                command = str(step.get("run", ""))
                if "pytest" in command:
                    assert not {"--showlocals", "-l"} & set(command.split()), (
                        workflow.name,
                        step.get("name"),
                    )


def test_artifact_uploads_keep_the_default_least_privilege_token() -> None:
    """Offline: uploading needs no permission beyond the workflow's `contents: read`."""
    assert _CI_TEST["permissions"] == {"contents": "read"}
    assert all("permissions" not in job for job in _CI_TEST["jobs"].values())
