from pathlib import Path

import yaml

WORKFLOW = (
    Path(__file__).resolve().parents[1] / ".github" / "workflows" / "scheduled-trigger-smoke.yml"
)


def test_trigger_smoke_is_scheduled_and_excludes_pull_requests() -> None:
    workflow = yaml.load(WORKFLOW.read_text(encoding="utf-8"), Loader=yaml.BaseLoader)

    assert set(workflow["on"]) == {"schedule", "workflow_dispatch"}
    command = workflow["jobs"]["queue-blob-durable"]["steps"][-1]["run"]
    assert "test_queue_examples.py" in command
    assert "test_blob_examples.py" in command
    assert "test_durable_examples.py" in command
