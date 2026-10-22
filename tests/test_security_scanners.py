from __future__ import annotations

import json
from pathlib import Path

import pytest

from tools.security_evidence import classify_bandit, semgrep_evidence
from tools.security_report import Status


def bandit_payload(files: list[str], findings: list[dict[str, str | int]]) -> str:
    return json.dumps(
        {
            "metrics": {"_totals": {"loc": 10}, **{f: {} for f in files}},
            "errors": [],
            "results": findings,
        }
    )


def test_bandit_inventory_mismatch_is_incomplete() -> None:
    assert (
        classify_bandit(bandit_payload([], []), 0, {"examples/app.py"}).status == Status.INCOMPLETE
    )


def test_bandit_finding_has_only_redacted_fields() -> None:
    raw = bandit_payload(
        ["examples/app.py"],
        [
            {
                "test_id": "B307",
                "filename": "examples/app.py",
                "line_number": 9,
                "issue_severity": "HIGH",
                "code": "fake-secret-canary",
            }
        ],
    )
    result = classify_bandit(raw, 1, {"examples/app.py"})
    assert result.status == Status.FAIL
    assert "fake-secret-canary" not in repr(result)


@pytest.mark.parametrize("raw,code", [("{}", 0), ("invalid", 0), ("{}", 2)])
def test_bandit_bad_output_is_tool_error(raw: str, code: int) -> None:
    assert classify_bandit(raw, code, {"examples/app.py"}).status == Status.TOOL_ERROR


def test_semgrep_action_success_is_not_claimed_complete_scan() -> None:
    assert semgrep_evidence("success").status == Status.INCOMPLETE
    assert semgrep_evidence("failure").status == Status.TOOL_ERROR


def test_structure_scan_rejects_settings_secret_without_echoing_it(tmp_path: Path) -> None:
    from tools.security_structure import check_structure

    example = tmp_path / "examples/test/demo"
    example.mkdir(parents=True)
    (example / "local.settings.json.example").write_text(
        json.dumps({"Values": {"AZURE_OPENAI_KEY": "a9b7c5d3" * 4}})
    )
    result = check_structure(tmp_path)
    assert result.status == Status.FAIL
    assert "a9b7c5d3" not in repr(result)


def test_structure_scan_allows_placeholders_and_development_storage(tmp_path: Path) -> None:
    from tools.security_structure import check_structure

    example = tmp_path / "examples/test/demo"
    example.mkdir(parents=True)
    (example / "local.settings.json.example").write_text(
        json.dumps(
            {
                "Values": {
                    "AZURE_OPENAI_KEY": "replace-me",
                    "AzureWebJobsStorage": "UseDevelopmentStorage=true",
                }
            }
        )
    )
    assert check_structure(tmp_path).status == Status.PASS


@pytest.mark.parametrize(
    "setting",
    [
        'OPENAI_API_KEY="sk-' + "9a7b5c3d" * 5 + '"',
        'DATABASE_PASSWORD="' + "1a3b5c7d" * 4 + '"',
        'AZURE_OPENAI_KEY="' + "fake9a7b" * 4 + '"',
    ],
)
def test_settings_keys_cannot_bypass_scan_by_prefix(tmp_path: Path, setting: str) -> None:
    from tools.security_structure import check_structure

    example = tmp_path / "examples/test/demo"
    example.mkdir(parents=True)
    (example / ".env.example").write_text(setting)
    assert check_structure(tmp_path).status == Status.FAIL
