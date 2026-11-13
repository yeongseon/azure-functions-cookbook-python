"""Guard docs/compatibility.md against drift from the manifests and recorded CI evidence (#467)."""

from __future__ import annotations

import json
from pathlib import Path
import re
import subprocess
import sys
from typing import Any

from packaging.specifiers import SpecifierSet
import pytest
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import gen_compat_table as gen  # noqa: E402

pytestmark = pytest.mark.repo_infra

ROOT = Path(__file__).resolve().parents[1]
TAGS = {"installed", "host-tested"}


def _evidence() -> dict[str, Any]:
    data: dict[str, Any] = json.loads(
        (ROOT / "docs" / "compat-evidence.json").read_text(encoding="utf-8")
    )
    return data


def test_generated_page_matches_the_committed_file() -> None:
    expected = gen.render(gen.inventory(), _evidence())
    assert (ROOT / "docs" / "compatibility.md").read_text(encoding="utf-8") == expected


def test_changing_a_declared_range_changes_the_page() -> None:
    inv = gen.inventory()
    inv["root"]["pydantic"] = ">=2.99,<3"
    assert gen.render(inv, _evidence()) != gen.render(gen.inventory(), _evidence())


def test_evidence_for_older_manifests_is_flagged_not_hidden() -> None:
    # Independent of how old the committed evidence is: the committed page is checked against the
    # committed evidence by test_generated_page_matches_the_committed_file, and evidence can only be
    # re-recorded from a green CI run on the new manifests.
    inventory = gen.inventory()
    stale = {**_evidence(), "inventory_digest": "0" * 16}
    current = {**_evidence(), "inventory_digest": gen.digest(inventory)}
    assert "Evidence is older than the manifests" in gen.render(inventory, stale)
    assert "Evidence is older than the manifests" not in gen.render(inventory, current)


def test_evidence_records_real_runs_with_dates_and_links() -> None:
    evidence = _evidence()
    assert evidence["schema"] == 1 and evidence["runs"]
    for run in evidence["runs"]:
        assert re.fullmatch(r"[0-9a-f]{40}", run["head_sha"])
        assert run["url"].endswith(f"/actions/runs/{run['run_id']}")
        for job in run["jobs"]:
            assert job["tag"] in TAGS
            assert re.fullmatch(r"\d{4}-\d{2}-\d{2}", job["date"])
            assert job["python"].startswith("3.")


def test_installed_versions_respect_the_declared_ranges() -> None:
    inv = gen.inventory()
    for run in _evidence()["runs"]:
        for job in run["jobs"]:
            for name, version in job["installed"].items():
                rng = inv["root"].get(name)
                if rng and "minimum" not in job["name"]:
                    assert SpecifierSet(rng).contains(version, prereleases=True), (
                        job["name"],
                        name,
                    )
            if "minimum" in job["name"]:
                for name, pin in inv["min_pins"].items():
                    assert job["installed"].get(name) in (None, pin), (job["name"], name)


def test_recorded_jobs_exist_in_the_workflow() -> None:
    workflow = yaml.safe_load((ROOT / ".github/workflows/ci-test.yml").read_text(encoding="utf-8"))
    matrix = workflow["jobs"]["host-smoke"]["strategy"]["matrix"]["recipe"]
    smoke = {entry["name"] for entry in matrix}
    pythons = set(workflow["jobs"]["test"]["strategy"]["matrix"]["python-version"])
    for run in _evidence()["runs"]:
        for job in run["jobs"]:
            if job["name"].startswith("Recipe host smoke"):
                assert re.search(r"\((.+)\)", job["name"]).group(1) in smoke  # type: ignore[union-attr]
            elif job["name"].startswith("Test ("):
                assert job["python"] in pythons


def test_page_is_linked_from_navigation_and_readmes() -> None:
    assert "compatibility.md" in (ROOT / "mkdocs.yml").read_text(encoding="utf-8")
    for name in ("README.md", "README.ko.md", "README.ja.md", "README.zh-CN.md"):
        assert "docs/compatibility.md" in (ROOT / name).read_text(encoding="utf-8")


def test_log_parsing_extracts_tracked_versions_only() -> None:
    log = (
        "job\tstep\t2026-01-01T00:00:00Z Successfully installed azure-functions-1.26.0 "
        "pydantic-2.14.3 pydantic-core-2.50.4 azure-functions-db-0.9.0 cffi-2.1.1\n"
        "job\tstep\t2026-01-01T00:00:01Z azure-functions-openapi        0.31.0\n"
        "job\tstep\t2026-01-01T00:00:02Z unrelated  1.0\n"
    )
    assert gen._installed(log) == {
        "azure-functions": "1.26.0",
        "pydantic": "2.14.3",
        "azure-functions-db": "0.9.0",
        "azure-functions-openapi": "0.31.0",
    }


def test_lower_bound_parsing() -> None:
    assert str(gen._lower_bound(">=1.22.1,<3")) == "1.22.1"
    assert gen._lower_bound("(unpinned)") is None
    assert gen._lower_bound("<3") is None
    with pytest.raises(ValueError):
        gen._split("???")


class _Done:
    returncode = 0


def _fake_gh(conclusion: str = "success") -> Any:
    run = {
        "workflowName": "Test and Coverage",
        "url": "https://github.com/x/y/actions/runs/7",
        "headSha": "a" * 40,
        "jobs": [
            {
                "name": "Test (Py 3.12, latest deps)",
                "conclusion": conclusion,
                "databaseId": 1,
                "completedAt": "2026-02-03T04:05:06Z",
            },
            {"name": "docs-check", "conclusion": "success", "databaseId": 2, "completedAt": "x"},
        ],
    }

    def fake(*args: str) -> str:
        if "--json" in args:
            return json.dumps(run)
        return "Z Successfully installed pydantic-2.14.3\nSuccessfully set up CPython (3.12.16)\n"

    return fake


def test_record_builds_evidence_from_a_run(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(gen, "_gh", _fake_gh())
    monkeypatch.setattr(subprocess, "run", lambda *a, **k: _Done())
    evidence = gen.record(["7"])
    job = evidence["runs"][0]["jobs"][0]
    assert evidence["runs"][0]["run_id"] == 7 and len(evidence["runs"][0]["jobs"]) == 1
    assert (job["tag"], job["python"], job["date"]) == ("installed", "3.12", "2026-02-03")
    assert job["installed"] == {"pydantic": "2.14.3"}


def test_record_refuses_failed_jobs_and_manifest_drift(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(subprocess, "run", lambda *a, **k: _Done())
    monkeypatch.setattr(gen, "_gh", _fake_gh("failure"))
    with pytest.raises(SystemExit, match="did not succeed"):
        gen.record(["7"])

    class _Drift:
        returncode = 1

    monkeypatch.setattr(gen, "_gh", _fake_gh())
    monkeypatch.setattr(subprocess, "run", lambda *a, **k: _Drift())
    with pytest.raises(SystemExit, match="manifests changed"):
        gen.record(["7"])
