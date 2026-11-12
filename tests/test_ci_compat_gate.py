"""Contract tests for the pre-merge toolkit compatibility gate (#427).

Offline: the classifier that scopes the ``toolkit-compat`` job, the job definition in
``ci-test.yml`` (fork-safe, SHA-pinned, fail-closed) and its aggregation by ``ci-required``.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
import re
import subprocess
import sys
import textwrap
from typing import Any

import pytest
import yaml

pytestmark = pytest.mark.repo_infra

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github" / "workflows" / "ci-test.yml"
COMPAT_SCRIPT = ROOT / "tools" / "ci_classify_compat.sh"
WRAPPER = ROOT / "tools" / "ci_classify_workflow.sh"


def _classify(files: list[str]) -> str:
    result = subprocess.run(
        ["bash", str(COMPAT_SCRIPT)],
        input="\n".join(files) + ("\n" if files else ""),
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    return result.stdout.strip()


@pytest.mark.parametrize(
    "files",
    [
        ["tests/e2e/test_package_runtime.py"],
        ["tests/e2e/conftest.py"],
        ["tests/test_openapi_endpoint_convergence.py"],
        ["examples/apis-and-ingress/full_stack_crud_api/function_app.py"],
        ["examples/apis-and-ingress/full_stack_crud_api/requirements.txt"],
        ["examples/ai-and-agents/personal_langgraph_agent/app/services/graph.py"],
        ["pyproject.toml"],
        ["constraints-min.txt"],
        ["tools/pytest_fail_on_skip.py"],
        ["tools/compat_report.py"],
        [".github/workflows/ci-test.yml"],
        [".github/workflows/e2e-toolkit.yml"],
        ["README.md", "constraints-min.txt"],
    ],
)
def test_integration_sensitive_paths_require_the_gate(files: list[str]) -> None:
    assert _classify(files) == "compat_required=true"


@pytest.mark.parametrize(
    "files",
    [
        ["README.md"],
        ["docs/testing.md"],
        ["examples/messaging-and-pubsub/queue_producer/function_app.py"],
        ["examples/apis-and-ingress/hello_http_minimal/README.md"],
        ["src/azure_functions_python_cookbook/recipes.py"],
        ["tests/test_recipes.py"],
        ["tools/lint_workflow_pins.py"],
        [".github/workflows/docs.yml"],
        ["CHANGELOG.md", "docs/index.md"],
    ],
)
def test_unrelated_or_docs_only_changes_skip_the_gate(files: list[str]) -> None:
    assert _classify(files) == "compat_required=false"


def test_empty_change_list_fails_closed() -> None:
    assert _classify([]) == "compat_required=true"


def _wrapper_output(tmp_path: Path, event: str, files: str) -> dict[str, str]:
    """Run the workflow wrapper with a fake git that lists *files* as the changed paths."""
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    fake_git = bin_dir / "git"
    fake_git.write_text(
        "#!/usr/bin/env bash\n"
        'case "$1" in\n'
        "  cat-file|merge-base) exit 0 ;;\n"
        f"  diff) printf '{files}'; exit 0 ;;\n"
        "  *) exit 99 ;;\n"
        "esac\n",
        encoding="utf-8",
    )
    fake_git.chmod(0o755)
    output = tmp_path / "github-output.txt"
    env = {
        **os.environ,
        "PATH": f"{bin_dir}:{os.environ['PATH']}",
        "EVENT_NAME": event,
        "BASE_SHA": "base",
        "HEAD_SHA": "head",
        "BEFORE_SHA": "before",
        "SHA": "after",
        "GITHUB_OUTPUT": str(output),
    }
    done = subprocess.run(
        ["bash", str(WRAPPER)], cwd=ROOT, env=env, check=False, capture_output=True, text=True
    )
    assert done.returncode == 0, done.stderr
    # GitHub keeps the last value written for a repeated key.
    return dict(line.split("=", 1) for line in output.read_text(encoding="utf-8").splitlines())


def test_wrapper_runs_the_gate_for_a_pull_request_touching_pins(tmp_path: Path) -> None:
    out = _wrapper_output(tmp_path, "pull_request", "constraints-min.txt\\n")
    assert out["full_required"] == "true"
    assert out["compat_required"] == "true"


def test_wrapper_skips_the_gate_for_a_docs_only_pull_request(tmp_path: Path) -> None:
    out = _wrapper_output(tmp_path, "pull_request", "docs/testing.md\\n")
    assert out["full_required"] == "false"
    assert out["compat_required"] == "false"


def test_wrapper_never_runs_the_gate_on_push(tmp_path: Path) -> None:
    out = _wrapper_output(tmp_path, "push", "constraints-min.txt\\n")
    assert out["full_required"] == "true"
    assert out["compat_required"] == "false"


def _workflow() -> dict[str, Any]:
    return yaml.safe_load(WORKFLOW.read_text(encoding="utf-8"))  # type: ignore[no-any-return]


def test_toolkit_compat_job_is_scoped_fork_safe_and_pinned() -> None:
    workflow = _workflow()
    # PyYAML reads the `on` key as boolean True.
    raw: dict[Any, Any] = workflow
    triggers: dict[str, Any] = raw.get("on") or raw[True]
    assert "pull_request_target" not in triggers
    assert workflow["permissions"] == {"contents": "read"}

    job = workflow["jobs"]["toolkit-compat"]
    assert "permissions" not in job
    assert "compat_required == 'true'" in job["if"]
    assert job["needs"] == "changes"
    assert job["env"]["PYTEST_ADDOPTS"] == "-p tools.pytest_fail_on_skip"
    text = json.dumps(job)
    assert "secrets." not in text
    assert "-c constraints-min.txt" in text
    assert "-m compat tests/e2e" in text
    for step in job["steps"]:
        if "uses" in step:
            assert re.fullmatch(r"[\w./-]+@[0-9a-f]{40}", step["uses"]), step["uses"]
    upload = next(s for s in job["steps"] if "upload-artifact" in s.get("uses", ""))
    assert upload["if"] == "always()"
    assert upload["with"]["if-no-files-found"] == "error"
    report = next(s for s in job["steps"] if "compat_report.py" in s.get("run", ""))
    assert report["if"] == "always()"
    assert "--min-tests" in report["run"]


def test_ci_required_aggregates_the_compat_job() -> None:
    needs = _workflow()["jobs"]["ci-required"]["needs"]
    assert "toolkit-compat" in needs


def _evaluator() -> str:
    run = _workflow()["jobs"]["ci-required"]["steps"][0]["run"]
    match = re.search(r"python3 - <<'EVAL'\n(.*)\nEVAL", run, re.DOTALL)
    assert match
    return textwrap.dedent(match.group(1))


_MATRIX = ("quality", "test", "recipe-tests", "artifact-python310-negative", "host-smoke")


def _results(*, full: bool, compat: bool, compat_result: str, docs: bool = False) -> dict[str, Any]:
    wanted = "success" if full else "skipped"
    return {
        "changes": {
            "result": "success",
            "outputs": {
                "docs_only": str(not full).lower(),
                "docs_changed": str(docs or not full).lower(),
                "full_required": str(full).lower(),
                "compat_required": str(compat).lower(),
            },
        },
        **{job: {"result": wanted} for job in _MATRIX},
        "toolkit-compat": {"result": compat_result},
        "docs-check": {"result": "success" if docs or not full else "skipped"},
    }


def _run_evaluator(results: dict[str, Any]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-c", _evaluator()],
        env={**os.environ, "RESULTS": json.dumps(results)},
        capture_output=True,
        text=True,
        check=False,
    )


@pytest.mark.parametrize(
    ("results", "passes"),
    [
        (_results(full=True, compat=True, compat_result="success"), True),
        (_results(full=True, compat=False, compat_result="skipped"), True),
        (_results(full=False, compat=False, compat_result="skipped"), True),
        (_results(full=True, compat=True, compat_result="failure"), False),
        (_results(full=True, compat=True, compat_result="skipped"), False),
        (_results(full=True, compat=True, compat_result="cancelled"), False),
        (_results(full=True, compat=False, compat_result="success"), False),
    ],
    ids=[
        "compat-ok",
        "compat-not-needed",
        "docs-only",
        "fail",
        "skipped",
        "cancelled",
        "unexpected",
    ],
)
def test_ci_required_enforces_the_compat_expectation(results: dict[str, Any], passes: bool) -> None:
    done = _run_evaluator(results)
    assert (done.returncode == 0) is passes, done.stdout + done.stderr


def test_ci_required_rejects_a_changes_job_without_the_compat_output() -> None:
    results = _results(full=True, compat=False, compat_result="skipped")
    del results["changes"]["outputs"]["compat_required"]
    assert _run_evaluator(results).returncode != 0
