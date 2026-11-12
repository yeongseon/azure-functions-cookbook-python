from pathlib import Path
from typing import Any

import yaml

WORKFLOW = Path(__file__).resolve().parents[1] / ".github" / "workflows" / "snapshot-audit.yml"


def _load() -> Any:
    # BaseLoader keeps the YAML 1.1 ``on`` key a string.
    return yaml.load(WORKFLOW.read_text(encoding="utf-8"), Loader=yaml.BaseLoader)


def test_audit_runs_on_release_schedule_pr_and_dispatch() -> None:
    triggers = _load()["on"]
    assert isinstance(triggers, dict)
    assert triggers["release"]["types"] == ["published"]
    assert "schedule" in triggers and "pull_request" in triggers
    assert "workflow_dispatch" in triggers


def test_audit_is_read_only_and_never_touches_pypi_or_secrets() -> None:
    text = WORKFLOW.read_text(encoding="utf-8")
    workflow = _load()
    assert workflow["permissions"] == {"contents": "read"}
    assert "secrets." not in text
    assert not {"gh-action-pypi-publish", "twine", "hatch publish"} & set(text.split())
    assert "pypi.org" not in text and "id-token" not in text
    commands = "\n".join(step.get("run", "") for step in workflow["jobs"]["audit"]["steps"])
    assert "python -m tools.audit_snapshots" in commands
    assert "gh release create" not in commands and "git push" not in commands
