from pathlib import Path

import yaml

from tools.verification_manifest import LOCAL_SUITES

WORKFLOW = (
    Path(__file__).resolve().parents[1] / ".github" / "workflows" / "scheduled-trigger-smoke.yml"
)


def test_trigger_smoke_is_scheduled_and_excludes_pull_requests() -> None:
    workflow = yaml.load(WORKFLOW.read_text(encoding="utf-8"), Loader=yaml.BaseLoader)

    assert set(workflow["on"]) == {"schedule", "workflow_dispatch"}
    steps = workflow["jobs"]["queue-blob-durable"]["steps"]
    commands = [step["run"] for step in steps if "run" in step]

    assert commands.count("make integration") == 1
    selections = {family: (path, marker) for family, path, marker in LOCAL_SUITES}
    assert selections["queue"] == ("tests/e2e/test_queue_examples.py", "e2e")
    assert selections["blob"] == ("tests/e2e/test_blob_examples.py", "e2e")
    assert selections["durable-import"] == ("tests/e2e/test_durable_examples.py", "smoke")
    assert any("verify_scheduled_smoke_selection.py" in c for c in commands)


def test_worker_registration_guard_job_runs_the_right_marker_and_file() -> None:
    """The deterministic worker-registration guard (#379) must run in this
    network-dependent, opt-in workflow rather than on every pull request."""
    workflow = yaml.load(WORKFLOW.read_text(encoding="utf-8"), Loader=yaml.BaseLoader)

    job = workflow["jobs"]["worker-registration-guard"]
    commands = [step["run"] for step in job["steps"] if "run" in step]
    assert commands.count("make worker-registration") == 1
    makefile = WORKFLOW.parents[2] / "Makefile"
    assert "worker-registration" in makefile.read_text()
