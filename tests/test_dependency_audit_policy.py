from __future__ import annotations

import json

import pytest

from tools.dependency_audit_policy import classify_audit, requirement_scopes
from tools.recipe_security import ROOT
from tools.security_report import Status


def test_root_closure_is_explicitly_empty_not_dev_extras() -> None:
    scopes = requirement_scopes(ROOT)
    assert scopes["root-runtime"] == ()
    assert len(scopes) == 83


def test_unknown_severity_advisory_blocks() -> None:
    raw = json.dumps(
        {
            "dependencies": [
                {
                    "name": "demo",
                    "version": "1.0",
                    "vulns": [{"id": "CVE-2099-0001", "description": "fake-secret-canary"}],
                }
            ]
        }
    )
    result = classify_audit(raw, 1)
    assert result.status == Status.FAIL
    assert result.findings[0].severity == "UNKNOWN"
    assert "fake-secret-canary" not in repr(result)


@pytest.mark.parametrize(
    "raw,code,status",
    [
        ('{"dependencies": []}', 0, Status.INCOMPLETE),
        ('{"dependencies": [{"name":"demo", "skip_reason":"local"}]}', 0, Status.INCOMPLETE),
        ("{}", 0, Status.TOOL_ERROR),
        ('{"dependencies": []}', 2, Status.TOOL_ERROR),
        ('{"dependencies": [{"name":"demo","version":"1","vulns":[]}]}', 0, Status.PASS),
    ],
)
def test_audit_outcomes_are_fail_closed(raw: str, code: int, status: Status) -> None:
    assert classify_audit(raw, code).status == status
