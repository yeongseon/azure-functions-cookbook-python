from pathlib import Path

import yaml

WORKFLOW = (
    Path(__file__).resolve().parents[1] / ".github" / "workflows" / "scheduled-trigger-smoke.yml"
)


def test_trigger_smoke_is_scheduled_and_excludes_pull_requests() -> None:
    workflow = yaml.load(WORKFLOW.read_text(encoding="utf-8"), Loader=yaml.BaseLoader)

    assert set(workflow["on"]) == {"schedule", "workflow_dispatch"}
    steps = workflow["jobs"]["queue-blob-durable"]["steps"]
    commands = [step["run"] for step in steps if "run" in step]

    # Queue/blob and Durable must run through *separate* commands with their
    # own marker selectors (#177): a single combined "-m e2e" command
    # silently deselects every Durable test, since that suite is marked
    # "smoke" (import-only coverage), not "e2e".
    queue_blob_commands = [c for c in commands if "test_queue_examples.py" in c]
    assert len(queue_blob_commands) == 1
    assert "test_blob_examples.py" in queue_blob_commands[0]
    assert "test_durable_examples.py" not in queue_blob_commands[0]
    assert "-m e2e" in queue_blob_commands[0]

    durable_commands = [c for c in commands if "test_durable_examples.py" in c]
    assert len(durable_commands) == 1
    assert "-m smoke" in durable_commands[0]
    assert "test_queue_examples.py" not in durable_commands[0]
    assert "test_blob_examples.py" not in durable_commands[0]

    # A selection-level guard must run so zero Durable items collected can
    # never silently satisfy this workflow again.
    assert any("verify_scheduled_smoke_selection.py" in c for c in commands)
