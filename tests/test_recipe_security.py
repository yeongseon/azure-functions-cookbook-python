from __future__ import annotations

from dataclasses import replace
from datetime import UTC, datetime, timedelta
import json
from pathlib import Path

import pytest

from tools.recipe_routes import routes
from tools.recipe_security import ROOT, check_manifest, inventory
from tools.security_exceptions import apply_policy
from tools.security_report import Check, Finding, Status, identifier, write_report


def test_real_manifest_covers_all_examples() -> None:
    result = check_manifest(ROOT)
    assert result.status == Status.PASS, result.findings
    assert result.counts["discovered"] == result.counts["classified"] == 82


@pytest.fixture
def sample(tmp_path: Path) -> Path:
    project = tmp_path / "examples/ai-and-agents/openai_direct_chat"
    project.mkdir(parents=True)
    (project / "function_app.py").write_text(
        "app = func.FunctionApp(http_auth_level=func.AuthLevel.FUNCTION)\n"
        "@app.route(route='chat')\ndef chat(req): return req\n"
    )
    (tmp_path / "security").mkdir()
    manifest = {
        "schema_version": 1,
        "recipes": {
            "examples/ai-and-agents/openai_direct_chat": {
                "category": "paid-backend",
                "reason": "Paid model boundary",
                "routes": ["chat=FUNCTION"],
            },
        },
    }
    (tmp_path / "security/recipe-security-manifest.json").write_text(json.dumps(manifest))
    return tmp_path


def test_paid_anonymous_mutation_fails(sample: Path) -> None:
    path = sample / "examples/ai-and-agents/openai_direct_chat/function_app.py"
    path.write_text(path.read_text().replace("AuthLevel.FUNCTION", "AuthLevel.ANONYMOUS"))
    result = check_manifest(sample)
    assert result.status == Status.FAIL
    assert "PAID_BACKEND_PUBLIC" in {finding.id for finding in result.findings}


def test_unclassified_example_mutation_fails(sample: Path) -> None:
    project = sample / "examples/new/anonymous"
    project.mkdir(parents=True)
    (project / "function_app.py").write_text(
        "app = func.FunctionApp()\n"
        "@app.route(route='new', auth_level=func.AuthLevel.ANONYMOUS)\ndef new(req): return req\n"
    )
    assert check_manifest(sample).status == Status.FAIL


def test_missing_classification_mutation_fails(sample: Path) -> None:
    (sample / "security/recipe-security-manifest.json").write_text('{"recipes": {}}')
    assert check_manifest(sample).status == Status.FAIL


def test_empty_inventory_never_passes(tmp_path: Path) -> None:
    (tmp_path / "security").mkdir()
    (tmp_path / "security/recipe-security-manifest.json").write_text('{"recipes": {}}')
    assert check_manifest(tmp_path).status == Status.FAIL


def test_blueprint_override_retains_route_level_auth(tmp_path: Path) -> None:
    (tmp_path / "function_app.py").write_text(
        "from app.health import bp\n"
        "app = func.FunctionApp(http_auth_level=func.AuthLevel.FUNCTION)\n"
        "app.register_functions(bp)\n"
    )
    (tmp_path / "app").mkdir()
    (tmp_path / "app/health.py").write_text(
        "bp = func.Blueprint()\n"
        "@bp.route(route='health', auth_level=func.AuthLevel.ANONYMOUS)\n"
        "def health(req): return req\n"
        "@bp.route(route='private')\ndef private(req): return req\n"
    )
    assert [(r.handler, r.auth) for r in routes(tmp_path, tmp_path)] == [
        ("health", "ANONYMOUS"),
        ("private", "FUNCTION"),
    ]


def test_untrusted_demo_variable_is_not_assumed_safe(tmp_path: Path) -> None:
    (tmp_path / "function_app.py").write_text(
        "PUBLIC_DEMO = True\n"
        "app = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS "
        "if PUBLIC_DEMO else func.AuthLevel.FUNCTION)\n"
        "@app.route(route='chat')\ndef chat(req): return req\n"
    )
    assert routes(tmp_path, tmp_path)[0].auth == "UNKNOWN"


def test_scanning_never_executes_example(sample: Path) -> None:
    path = sample / "examples/ai-and-agents/openai_direct_chat/function_app.py"
    path.write_text("raise RuntimeError('must not execute')\n" + path.read_text())
    assert inventory(sample)


@pytest.mark.parametrize("expiry", [-1, 91])
def test_invalid_exception_cannot_suppress_finding(tmp_path: Path, expiry: int) -> None:
    today = datetime.now(UTC).date()
    policy = tmp_path / "policy.json"
    policy.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "exceptions": [
                    {
                        "id": "B307",
                        "file": "examples/demo.py",
                        "line": 1,
                        "owner": "maintainer",
                        "reason": "Review",
                        "added": today.isoformat(),
                        "expires": (today + timedelta(days=expiry)).isoformat(),
                    }
                ],
            }
        )
    )
    check = Check("bandit", Status.FAIL, findings=(Finding("B307", "examples/demo.py", 1),))
    assert apply_policy(check, policy).status == Status.TOOL_ERROR


def test_exception_only_matches_exact_location(tmp_path: Path) -> None:
    today = datetime.now(UTC).date()
    policy = tmp_path / "policy.json"
    policy.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "exceptions": [
                    {
                        "id": "B307",
                        "file": "examples/demo.py",
                        "line": 1,
                        "owner": "maintainer",
                        "reason": "Reviewed demo",
                        "added": today.isoformat(),
                        "expires": (today + timedelta(days=30)).isoformat(),
                    }
                ],
            }
        )
    )
    check = Check("bandit", Status.FAIL, findings=(Finding("B307", "examples/demo.py", 1),))
    assert apply_policy(check, policy).status == Status.PASS
    assert (
        apply_policy(
            replace(check, findings=(Finding("B307", "examples/demo.py", 2),)), policy
        ).status
        == Status.FAIL
    )


@pytest.mark.parametrize(
    "status,code",
    [(Status.PASS, 0), (Status.FAIL, 1), (Status.TOOL_ERROR, 2), (Status.INCOMPLETE, 3)],
)
def test_evidence_preserves_distinct_outcomes(tmp_path: Path, status: Status, code: int) -> None:
    assert write_report([Check("scanner", status)], tmp_path) == code
    assert json.loads((tmp_path / "summary.json").read_text())["checks"][0]["status"] == status


@pytest.mark.parametrize(
    "unsafe", ["https://secret.invalid/key", "../outside", "/tmp/raw", "secret\n"]
)
def test_evidence_identifiers_reject_raw_sensitive_content(unsafe: str) -> None:
    with pytest.raises(ValueError):
        identifier(unsafe)
