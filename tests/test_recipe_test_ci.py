from pathlib import Path

_ROOT = Path(__file__).parents[1]
_WORKFLOW = _ROOT / ".github" / "workflows" / "ci-test.yml"


def test_ci_runs_discovered_recipe_test_suites() -> None:
    # Given: recipe test suites discovered below examples.
    suites = sorted((_ROOT / "examples").glob("*/*/tests"))

    # When: the required CI workflow is inspected.
    workflow = _WORKFLOW.read_text()

    # Then: CI delegates automatic per-recipe execution to the repository runner.
    assert suites
    assert "python scripts/run_recipe_tests.py" in workflow
    assert "needs: [quality, test, recipe-tests]" in workflow
