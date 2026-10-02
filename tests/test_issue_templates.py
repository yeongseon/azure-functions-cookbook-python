from pathlib import Path

import yaml

KNOWN_LABELS = {
    "blocker",
    "bug",
    "chore",
    "ci",
    "documentation",
    "enhancement",
    "needs-triage",
    "priority:critical",
    "priority:high",
    "priority:low",
    "priority:medium",
    "question",
    "test",
}
ISSUE_TEMPLATES = Path(__file__).resolve().parents[1] / ".github" / "ISSUE_TEMPLATE"


def test_issue_forms_only_reference_known_labels() -> None:
    unknown_labels: dict[str, list[str]] = {}

    for form in sorted(ISSUE_TEMPLATES.glob("*.yml")):
        labels = yaml.safe_load(form.read_text()).get("labels", [])
        unknown = sorted(set(labels) - KNOWN_LABELS)
        if unknown:
            unknown_labels[form.name] = unknown

    assert not unknown_labels, f"issue forms reference undefined labels: {unknown_labels}"
