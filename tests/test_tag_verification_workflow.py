from pathlib import Path

import yaml

WORKFLOW = Path(__file__).resolve().parents[1] / ".github" / "workflows" / "tag-verification.yml"


def test_tag_verification_covers_release_artifact_contract() -> None:
    workflow = yaml.load(WORKFLOW.read_text(encoding="utf-8"), Loader=yaml.BaseLoader)

    assert workflow["on"]["push"]["tags"] == ["v*"]
    steps = workflow["jobs"]["build"]["steps"]
    commands = "\n".join(step.get("run", "") for step in steps)
    assert "python -m build" in commands
    assert "Requires-Python: >=3.11,<3.15" in commands
    assert "pip check" in commands
    assert "Python 3.10 unexpectedly installed" in commands
