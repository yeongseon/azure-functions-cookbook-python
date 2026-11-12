from pathlib import Path

import yaml

_ROOT = Path(__file__).parents[1]
_WORKFLOW = _ROOT / ".github" / "workflows" / "ci-test.yml"


def test_ci_runs_discovered_recipe_test_suites() -> None:
    """Offline: required CI delegates all discovered recipe test suites to the runner script."""
    suites = sorted((_ROOT / "examples").glob("*/*/tests"))

    workflow = _WORKFLOW.read_text()
    jobs = yaml.safe_load(workflow)["jobs"]

    assert suites
    assert "python scripts/run_recipe_tests.py" in workflow
    assert set(jobs["ci-required"]["needs"]) == {
        "changes",
        "quality",
        "test",
        "recipe-tests",
        "artifact-python310-negative",
        "host-smoke",
        "docs-check",
    }
