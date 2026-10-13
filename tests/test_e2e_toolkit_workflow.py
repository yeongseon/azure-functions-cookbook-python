from pathlib import Path

import yaml

WORKFLOW = Path(__file__).resolve().parents[1] / ".github" / "workflows" / "e2e-toolkit.yml"


def test_toolkit_matrix_listens_for_releases_and_runs_convergence() -> None:
    workflow = yaml.load(WORKFLOW.read_text(encoding="utf-8"), Loader=yaml.BaseLoader)

    assert workflow["on"]["repository_dispatch"]["types"] == ["sibling-release"]
    steps = workflow["jobs"]["e2e"]["steps"]
    convergence = next(
        step
        for step in steps
        if step["name"] == "Run OpenAPI convergence and byte-consistency guards"
    )
    assert "tests/test_openapi_endpoint_convergence.py" in convergence["run"]
    assert "tests/test_db_input_output_openapi.py" in convergence["run"]
