"""Guards for the CI package-download audit (#459): docs/ci-package-downloads.md and the
``main`` axis of ``e2e-toolkit.yml``. Offline."""

from __future__ import annotations

from importlib import metadata
import json
from pathlib import Path
import re
from typing import Any

import pytest
import yaml

from tools import verify_toolkit_source as source

pytestmark = pytest.mark.repo_infra

ROOT = Path(__file__).resolve().parents[1]
WORKFLOWS = ROOT / ".github" / "workflows"
AUDIT = ROOT / "docs" / "ci-package-downloads.md"
E2E = WORKFLOWS / "e2e-toolkit.yml"

# A step that can fetch packages from PyPI.
_INSTALLS = re.compile(
    r"pip install|pip-audit|make install|make security-dependencies|make security\b|hatch"
)
# A schedule-triggered workflow only needs a row when it installs the toolkit or resolves its
# requirements; these install nothing from PyPI beyond a scanner or YAML parser.
_NO_TOOLKIT = {"codeql.yml", "snapshot-audit.yml", "stale.yml", "sbom.yml"}


def _load(path: Path) -> dict[Any, Any]:
    return yaml.safe_load(path.read_text(encoding="utf-8"))  # type: ignore[no-any-return]


def _scheduled() -> dict[str, dict[Any, Any]]:
    found = {}
    for path in sorted(WORKFLOWS.glob("*.yml")):
        workflow = _load(path)
        triggers = workflow.get("on") or workflow.get(True) or {}
        if isinstance(triggers, dict) and "schedule" in triggers:
            found[path.name] = workflow
    return found


def _audit_rows() -> dict[str, str]:
    """Map workflow file name to the table rows that mention it."""
    rows: dict[str, str] = {}
    for line in AUDIT.read_text(encoding="utf-8").splitlines():
        if line.startswith("|"):
            for name in re.findall(r"`([\w-]+\.yml)`", line):
                rows[name] = rows.get(name, "") + line
    return rows


def test_every_scheduled_workflow_that_installs_packages_is_audited() -> None:
    rows = _audit_rows()
    missing = []
    for name, workflow in _scheduled().items():
        runs = "\n".join(
            step.get("run", "") for job in workflow["jobs"].values() for step in job["steps"]
        )
        if name not in _NO_TOOLKIT and _INSTALLS.search(runs) and name not in rows:
            missing.append(name)
    assert not missing, f"add {missing} to docs/ci-package-downloads.md (audit table)"


def test_audit_rows_name_only_schedule_triggered_workflows() -> None:
    stale = sorted(set(_audit_rows()) - set(_scheduled()))
    assert not stale, f"docs/ci-package-downloads.md names workflows without a schedule: {stale}"


def test_audit_states_the_retention_decisions() -> None:
    text = AUDIT.read_text(encoding="utf-8")
    assert "**Retained.**" in text
    assert "downloads, not unique users" in text.replace("**", "")


def _e2e_steps() -> list[dict[str, Any]]:
    return _load(E2E)["jobs"]["e2e"]["steps"]  # type: ignore[no-any-return]


def test_main_axis_installs_sibling_sources_before_the_cookbook_dependencies() -> None:
    steps = _e2e_steps()
    names = [step["name"] for step in steps]
    sibling = names.index("Install toolkit libraries from sibling main branches")
    cookbook = names.index("Install cookbook dependencies")
    assert sibling < cookbook
    assert steps[sibling]["if"] == "matrix.toolkit-source == 'main'"
    assert "if" not in steps[cookbook]
    run = steps[sibling]["run"]
    assert "--no-deps" not in run
    assert "--force-reinstall" not in run
    assert len(re.findall(r"@ git\+https://github\.com/yeongseon/", run)) == 6


def test_axis_is_verified_after_installation_and_before_any_test() -> None:
    steps = _e2e_steps()
    names = [step["name"] for step in steps]
    verify = names.index("Verify the toolkit packages come from the axis under test")
    assert names.index("Install cookbook dependencies") < verify
    assert verify < names.index("Run OpenAPI convergence and byte-consistency guards")
    assert "tools/verify_toolkit_source.py" in steps[verify]["run"]
    assert steps[verify]["env"]["AXIS"] == "${{ matrix.toolkit-source }}"


def test_toolkit_package_list_matches_the_cookbook_dev_extra() -> None:
    pyproject = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    declared = {
        name
        for name in re.findall(r'"(azure-functions-[a-z]+)[>=<]', pyproject)
        if name != "azure-functions-durable"
    }
    assert set(source.TOOLKIT_PACKAGES) == declared


def _fake_distribution(direct_url: str | None) -> Any:
    class _Distribution:
        def read_text(self, filename: str) -> str | None:
            assert filename == "direct_url.json"
            return direct_url

    return _Distribution()


@pytest.mark.parametrize(
    ("direct_url", "expected"),
    [
        (None, "index"),
        (json.dumps({"url": "https://x", "vcs_info": {"vcs": "git"}}), "git"),
        (json.dumps({"url": "file:///tmp/x", "dir_info": {}}), "other-direct-url"),
    ],
)
def test_installed_source_classifies_the_install(
    monkeypatch: pytest.MonkeyPatch, direct_url: str | None, expected: str
) -> None:
    monkeypatch.setattr(metadata, "distribution", lambda _name: _fake_distribution(direct_url))
    assert source.installed_source("anything") == expected


def test_check_flags_the_wrong_source_and_missing_packages(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    git = json.dumps({"vcs_info": {"vcs": "git"}})
    sources = {"a": git, "b": None}

    def distribution(name: str) -> Any:
        if name not in sources:
            raise metadata.PackageNotFoundError(name)
        return _fake_distribution(sources[name])

    monkeypatch.setattr(metadata, "distribution", distribution)
    monkeypatch.setattr(metadata, "version", lambda _name: "1.0")

    assert source.check("main", ["a"]) == []
    assert source.check("latest", ["b"]) == []
    assert source.check("main", ["a", "b", "c"]) == [
        "b==1.0: installed from index, expected git",
        "c: not installed",
    ]
    assert source.check("latest", ["a"]) == ["a==1.0: installed from git, expected index"]
    assert "a==1.0 installed from git" in capsys.readouterr().out


def test_main_reports_usage_and_exit_codes(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    assert source.main([]) == 2
    assert source.main(["other"]) == 2
    monkeypatch.setattr(source, "check", lambda axis: [f"{axis}: bad"])
    assert source.main(["main"]) == 1
    assert "::error::main: bad" in capsys.readouterr().err
    monkeypatch.setattr(source, "check", lambda axis: [])
    assert source.main(["latest"]) == 0
