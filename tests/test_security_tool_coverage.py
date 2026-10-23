from collections.abc import Callable
from datetime import UTC, datetime, timedelta
import json
from pathlib import Path
import subprocess
import sys
from unittest.mock import patch

import pytest

from tools import recipe_security as manifest
from tools import security_evidence as evidence
from tools import security_report as report
from tools import security_structure as structure
from tools.security_exceptions import apply_policy, read_rules


@pytest.mark.parametrize(
    "parse,value",
    [
        (report.mapping, []),
        (report.sequence, {}),
        (report.text, ""),
        (report.integer, True),
        (report.integer, -1),
    ],
)
def test_evidence_boundary_rejects_invalid_values(
    parse: Callable[[report.JSON], report.JSON], value: report.JSON
) -> None:
    with pytest.raises(ValueError):
        parse(value)


def test_report_writes_only_to_redirected_job_summary(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    summary = tmp_path / "job.md"
    monkeypatch.setenv("GITHUB_STEP_SUMMARY", str(summary))
    assert report.write_report([report.Check("test", report.Status.INCOMPLETE)], tmp_path) == 3
    assert "INCOMPLETE" in summary.read_text()


@pytest.mark.parametrize("mutation", ["version", "duplicate", "inexact", "line"])
def test_exception_schema_is_exact(tmp_path: Path, mutation: str) -> None:
    rule = {
        "id": "B101",
        "file": "app.py",
        "line": 1,
        "owner": "owner",
        "reason": "reason",
        "added": datetime.now(UTC).date().isoformat(),
        "expires": (datetime.now(UTC).date() + timedelta(days=10)).isoformat(),
    }
    rules = [rule]
    policy = {"schema_version": 1, "exceptions": rules}
    if mutation == "version":
        policy["schema_version"] = 2
    elif mutation == "duplicate":
        rules.append(rule)
    elif mutation == "inexact":
        rule["package"] = "demo"
    else:
        rule["line"] = 0
    path = tmp_path / "policy.json"
    path.write_text(json.dumps(policy))
    with pytest.raises(ValueError):
        read_rules(path, datetime.now(UTC).date())


def test_incomplete_scan_cannot_be_made_passing_by_exception(tmp_path: Path) -> None:
    path = tmp_path / "policy.json"
    path.write_text('{"schema_version":1,"exceptions":[]}')
    assert (
        apply_policy(report.Check("scan", report.Status.INCOMPLETE), path).status
        == report.Status.INCOMPLETE
    )


@pytest.mark.parametrize(
    "code,severity,status",
    [(2, "HIGH", report.Status.TOOL_ERROR), (1, "invalid", report.Status.TOOL_ERROR)],
)
def test_bandit_rejects_inconsistent_execution(
    code: int, severity: str, status: report.Status
) -> None:
    raw = json.dumps(
        {
            "metrics": {"_totals": {"loc": 1}, "app.py": {}},
            "results": [
                {
                    "test_id": "B101",
                    "filename": "app.py",
                    "line_number": 1,
                    "issue_severity": severity,
                }
            ],
            "errors": [],
        }
    )
    assert evidence.classify_bandit(raw, code, {"app.py"}).status == status


@pytest.mark.parametrize("suppressed", [False, True])
def test_bandit_scans_expanded_inventory_and_rejects_unreviewed_suppressions(
    tmp_path: Path, suppressed: bool
) -> None:
    for folder in ("examples/demo", "scripts", "tools"):
        directory = tmp_path / folder
        directory.mkdir(parents=True)
        (directory / "app.py").write_text("x = 1" + (" # nosec" if suppressed else ""))
    policy = tmp_path / "security"
    policy.mkdir()
    (policy / "bandit-exceptions.json").write_text('{"schema_version":1,"exceptions":[]}')
    files = ["examples/demo/app.py", "scripts/app.py", "tools/app.py"]
    raw = json.dumps(
        {
            "metrics": {"_totals": {"loc": 3}, **{name: {} for name in files}},
            "results": [],
            "errors": [],
        }
    )
    with patch.object(
        subprocess, "run", return_value=subprocess.CompletedProcess([], 0, raw)
    ) as runner:
        result = evidence.run_bandit(tmp_path)
    assert result.status == (report.Status.INCOMPLETE if suppressed else report.Status.PASS)
    assert set(files).issubset(runner.call_args.args[0])


def test_bandit_execution_failure_is_tool_error(tmp_path: Path) -> None:
    with patch.object(subprocess, "run", side_effect=OSError("missing")):
        assert evidence.run_bandit(tmp_path).status == report.Status.TOOL_ERROR


def test_static_cli_collects_all_checks(tmp_path: Path) -> None:
    check = report.Check("test", report.Status.PASS)
    with (
        patch.object(sys, "argv", ["scan", "all", "--output", str(tmp_path)]),
        patch.object(evidence, "check_manifest", return_value=check),
        patch.object(evidence, "run_bandit", return_value=check),
        patch.object(evidence, "check_structure", return_value=check),
    ):
        assert evidence.main() == 0
    assert len(json.loads((tmp_path / "summary.json").read_text())["checks"]) == 3


@pytest.mark.parametrize("code,status", [(0, report.Status.PASS), (1, report.Status.TOOL_ERROR)])
def test_structure_shell_parser_is_blocking(
    tmp_path: Path, code: int, status: report.Status
) -> None:
    directory = tmp_path / "tools"
    directory.mkdir()
    (directory / "test.sh").touch()
    with patch.object(subprocess, "run", return_value=subprocess.CompletedProcess([], code)):
        assert structure.check_structure(tmp_path).status == status


def test_structure_io_failure_is_tool_error(tmp_path: Path) -> None:
    directory = tmp_path / "infra"
    directory.mkdir()
    (directory / "main.bicep").write_bytes(b"\xff")
    assert structure.check_structure(tmp_path).status == report.Status.TOOL_ERROR


def test_structure_reports_public_networking_without_blocking(tmp_path: Path) -> None:
    directory = tmp_path / "infra"
    directory.mkdir()
    (directory / "main.bicep").write_text("publicNetworkAccess: 'Enabled'\n")
    assert structure.check_structure(tmp_path).counts["public_network_demo"] == 1


@pytest.mark.parametrize(
    "category,declaration,finding",
    [
        ("invalid", "chat=FUNCTION", "CATEGORY"),
        ("protected", "chat=ANONYMOUS", "MISCLASSIFIED_ANONYMOUS"),
        ("paid-backend", "chat=UNKNOWN", "UNRESOLVED_AUTH"),
        ("non-http", "chat=FUNCTION", "CATEGORY_DRIFT"),
    ],
)
def test_manifest_policy_rejects_invalid_classification(
    tmp_path: Path, category: str, declaration: str, finding: str
) -> None:
    directory = tmp_path / "security"
    directory.mkdir()
    (directory / "recipe-security-manifest.json").write_text(
        json.dumps(
            {
                "recipes": {
                    "examples/demo": {
                        "category": category,
                        "reason": "reason",
                        "routes": [declaration],
                    },
                    "examples/stale": {},
                }
            }
        )
    )
    with patch.object(manifest, "inventory", return_value={"examples/demo": [declaration]}):
        result = manifest.check_manifest(tmp_path)
    assert finding in {item.id for item in result.findings}
    assert "STALE_RECIPE" in {item.id for item in result.findings}


def test_missing_manifest_is_tool_error(tmp_path: Path) -> None:
    assert manifest.check_manifest(tmp_path).status == report.Status.TOOL_ERROR
