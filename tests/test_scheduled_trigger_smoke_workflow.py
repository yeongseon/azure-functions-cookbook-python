import os
from pathlib import Path
import shlex
import subprocess
import sys

import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = REPO_ROOT / ".github" / "workflows" / "scheduled-trigger-smoke.yml"


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


def test_worker_registration_guard_job_runs_the_right_marker_and_file() -> None:
    """The deterministic worker-registration guard (#379) must run in this
    network-dependent, opt-in workflow rather than on every pull request."""
    workflow = yaml.load(WORKFLOW.read_text(encoding="utf-8"), Loader=yaml.BaseLoader)

    job = workflow["jobs"]["worker-registration-guard"]
    commands = [step["run"] for step in job["steps"] if "run" in step]
    guard_commands = [c for c in commands if "test_worker_registration_guard.py" in c]

    assert len(guard_commands) == 1
    assert "-m worker_registration" in guard_commands[0]


def test_worker_registration_guard_job_installs_worker_requirements_and_fails_on_skips() -> None:
    """Offline: the guard job installs the worker's requirements and the fail-on-skip plugin."""
    workflow = yaml.load(WORKFLOW.read_text(encoding="utf-8"), Loader=yaml.BaseLoader)

    job = workflow["jobs"]["worker-registration-guard"]
    install = next(step["run"] for step in job["steps"] if "pip install -e" in step.get("run", ""))

    for pin in ("grpcio~=1.70.0", "protobuf~=5.29.0", "python-dateutil~=2.9.0"):
        assert pin in install
    assert job["env"]["PYTEST_ADDOPTS"] == "-p tools.pytest_fail_on_skip"


def test_worker_registration_guard_job_command_exits_non_zero_when_the_worker_cannot_be_cloned(
    tmp_path: Path,
) -> None:
    """Offline: without git, the job's own command exits 1 instead of reporting 15 skips (#437)."""
    workflow = yaml.load(WORKFLOW.read_text(encoding="utf-8"), Loader=yaml.BaseLoader)
    job = workflow["jobs"]["worker-registration-guard"]
    command = next(
        step["run"]
        for step in job["steps"]
        if "test_worker_registration_guard.py" in step.get("run", "")
    )
    argv = shlex.split(command)
    assert argv[:3] == ["python", "-m", "pytest"]  # puts the repository root on sys.path
    # An empty PATH hides git, so the pinned worker can never be cloned.
    env = {**os.environ, **job["env"], "PATH": str(tmp_path)}

    result = subprocess.run(
        [sys.executable, *argv[1:]],
        cwd=REPO_ROOT,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 1, result.stdout
    assert "Could not clone azure-functions-python-worker" in result.stdout
