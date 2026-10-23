from datetime import UTC, datetime, timedelta
import json
from pathlib import Path
import subprocess
import sys
from unittest.mock import patch

import pytest

from tools import dependency_audit_policy as audit
from tools.security_report import Status


@pytest.fixture
def repository(tmp_path: Path) -> Path:
    (tmp_path / "pyproject.toml").write_text("[project]\ndependencies = []\n")
    for name in ("first", "second"):
        directory = tmp_path / "examples" / name
        directory.mkdir(parents=True)
        (directory / "function_app.py").touch()
        (directory / "pyproject.toml").write_text('[project]\ndependencies = ["demo==1"]\n')
        (directory / "requirements.txt").write_text("demo==1\n")
    (tmp_path / "security").mkdir()
    (tmp_path / "security/dependency-exceptions.json").write_text(
        '{"schema_version":1,"exceptions":[]}'
    )
    return tmp_path


@pytest.mark.parametrize(
    "exception",
    [
        OSError("unavailable"),
        subprocess.TimeoutExpired("pip", 1),
        subprocess.CalledProcessError(1, "pip"),
    ],
)
def test_auditor_setup_failure_is_blocking(repository: Path, exception: Exception) -> None:
    with patch.object(subprocess, "run", side_effect=exception):
        result = audit.audit_scopes(repository, repository / "scratch")
    assert result[0].status == Status.TOOL_ERROR


@pytest.mark.parametrize("failure", [OSError("unavailable"), subprocess.TimeoutExpired("audit", 1)])
def test_audit_failure_is_cached_without_passing_other_scopes(
    repository: Path, failure: Exception
) -> None:
    with patch.object(subprocess, "run", side_effect=[None, None, failure]) as runner:
        result = audit.audit_scopes(repository, repository / "scratch")
    assert [check.status for check in result] == [Status.PASS, Status.TOOL_ERROR, Status.TOOL_ERROR]
    assert runner.call_count == 3
    assert result[1].name != result[2].name


@pytest.mark.parametrize("exception_applies", [False, True])
def test_audit_applies_exact_exceptions_and_reuses_resolved_results(
    repository: Path, exception_applies: bool
) -> None:
    today = datetime.now(UTC).date()
    if exception_applies:
        (repository / "security/dependency-exceptions.json").write_text(
            json.dumps(
                {
                    "schema_version": 1,
                    "exceptions": [
                        {
                            "id": "CVE-2099-0001",
                            "package": "demo",
                            "reason": "Reviewed",
                            "owner": "maintainer",
                            "added": today.isoformat(),
                            "expires": (today + timedelta(days=10)).isoformat(),
                        }
                    ],
                }
            )
        )
    raw = '{"dependencies":[{"name":"demo","version":"1","vulns":[{"id":"CVE-2099-0001"}]}]}'
    with patch.object(
        subprocess, "run", side_effect=[None, None, subprocess.CompletedProcess([], 1, raw)]
    ) as runner:
        result = audit.audit_scopes(repository, repository / "scratch")
    assert [check.status for check in result] == [
        Status.PASS,
        *([Status.PASS if exception_applies else Status.FAIL] * 2),
    ]
    assert result[1].exceptions == result[2].exceptions
    assert runner.call_count == 3
    assert "pip_audit" in runner.call_args.args[0]


def test_missing_inventory_is_incomplete(tmp_path: Path) -> None:
    assert audit.audit_scopes(tmp_path, tmp_path)[0].status == Status.INCOMPLETE


@pytest.mark.parametrize("mutation", ["empty", "drift", "hidden"])
def test_requirement_inventory_boundaries(repository: Path, mutation: str) -> None:
    if mutation == "empty":
        (repository / "security/pyproject.toml").write_text("[project]\ndependencies=[]\n")
        with pytest.raises(ValueError):
            audit.requirement_scopes(repository / "security")
    elif mutation == "drift":
        (repository / "examples/first/requirements.txt").write_text("wrong\n")
        with pytest.raises(ValueError):
            audit.requirement_scopes(repository)
    else:
        hidden = repository / "examples/.hidden"
        hidden.mkdir()
        (hidden / "function_app.py").touch()
        assert len(audit.requirement_scopes(repository)) == 3


@pytest.mark.parametrize("reporting,expected", [(False, 2), (True, 0)])
def test_cli_reporting_preserves_evidence_without_blocking(
    repository: Path, reporting: bool, expected: int
) -> None:
    arguments = [
        "audit",
        "--scratch",
        str(repository / "scratch"),
        "--output",
        str(repository / "results"),
    ]
    if reporting:
        arguments.append("--reporting")
    with (
        patch.object(sys, "argv", arguments),
        patch.object(audit, "ROOT", repository),
        patch.object(subprocess, "run", side_effect=OSError("missing")),
    ):
        assert audit.main() == expected
    assert (
        json.loads((repository / "results/summary.json").read_text())["checks"][0]["status"]
        == "TOOL_ERROR"
    )
