"""Offline tests for ``tools/recipe_host_smoke.py`` and the ``host-smoke`` job contract.

The real Core Tools run happens in the required ``host-smoke`` CI job. These tests use a fake
``func`` executable so the harness logic (index check, failure markers, response checks, evidence)
is covered without Core Tools or Azurite.
"""

from __future__ import annotations

import json
from pathlib import Path
import stat
import sys
import textwrap
from typing import Any

import pytest
import yaml

from tools import recipe_host_smoke as smoke

pytestmark = pytest.mark.repo_infra

_ROOT = Path(__file__).parents[1]
_WORKFLOW = _ROOT / ".github" / "workflows" / "ci-test.yml"

_INDEXED_LOG = """\
Azure Functions Core Tools
Core Tools Version:       4.6.0+abc (64-bit)
Function Runtime Version: 4.1045.200.1

Functions:

\thello: [GET] http://localhost:7071/api/hello

For detailed output, run func with --verbose flag.
"""


def test_indexed_functions_parses_the_functions_section() -> None:
    assert smoke.indexed_functions(_INDEXED_LOG) == ["hello: [GET] http://localhost:7071/api/hello"]
    assert smoke.runtime_version(_INDEXED_LOG) == "4.1045.200.1"


def test_indexed_functions_is_empty_without_a_functions_section() -> None:
    log = "Worker process started and initialized.\nFor detailed output, run func with --verbose\n"
    assert smoke.indexed_functions(log) == []
    assert smoke.runtime_version(log) is None


def test_failure_marker_detects_zero_job_functions() -> None:
    assert smoke.failure_marker("x\nGenerating 0 job function(s)\n") == "Generating 0 job function"
    assert smoke.failure_marker(_INDEXED_LOG) is None


@pytest.mark.parametrize(
    ("status", "body", "message"),
    [(500, "boom", "expected HTTP 200, got 500"), (200, "nothing", "missing \\['Hello'\\]")],
)
def test_check_response_rejects_wrong_status_or_body(status: int, body: str, message: str) -> None:
    with pytest.raises(smoke.HostSmokeError, match=message):
        smoke.check_response(status, body, 200, ["Hello"])


def test_check_response_accepts_expected_answer() -> None:
    smoke.check_response(202, '{"status": "accepted"}', 202, ["accepted"])


_FAKE_FUNC = textwrap.dedent(
    """\
    #!{python}
    import http.server, os, sys
    if "--version" in sys.argv:
        print("9.9.9")
        raise SystemExit(0)
    port = int(sys.argv[sys.argv.index("--port") + 1])
    mode = os.environ.get("FAKE_FUNC_MODE", "ok")
    if mode == "crash":
        raise SystemExit(3)
    if mode == "zero":
        print("Generating 0 job function(s)", flush=True)
    else:
        banner = "Function Runtime Version: 4.0.0\\n\\nFunctions:\\n\\n\\thello: [GET] x\\n"
        print(banner, flush=True)
    class Handler(http.server.BaseHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200); self.end_headers(); self.wfile.write(b"Hello from fake")
        def do_POST(self):
            self.send_response(202); self.end_headers(); self.wfile.write(b"accepted")
        def log_message(self, *args): pass
    http.server.HTTPServer(("127.0.0.1", port), Handler).serve_forever()
    """
)


@pytest.fixture
def fake_host(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """A recipe dir with a fake venv python, and a fake ``func`` first on PATH."""
    recipe = tmp_path / "recipe"
    (recipe / ".venv" / "bin").mkdir(parents=True)
    (recipe / "function_app.py").write_text("")
    (recipe / ".venv" / "bin" / "python").symlink_to(sys.executable)
    bindir = tmp_path / "bin"
    bindir.mkdir()
    func = bindir / "func"
    func.write_text(_FAKE_FUNC.format(python=sys.executable))
    func.chmod(func.stat().st_mode | stat.S_IEXEC)
    monkeypatch.setenv("PATH", f"{bindir}:{Path(sys.executable).parent}:/usr/bin:/bin")
    monkeypatch.setattr(
        smoke,
        "installed_packages",
        lambda python: {"azure-functions": "1.0"},  # noqa: ARG005
    )
    return recipe


def _args(recipe: Path, *extra: str) -> list[str]:
    return [
        "--recipe-dir",
        str(recipe),
        "--route",
        "/api/hello",
        "--no-azurite",
        "--startup-timeout",
        "20",
        *extra,
    ]


def test_main_writes_evidence_for_a_passing_host(fake_host: Path, tmp_path: Path) -> None:
    evidence = tmp_path / "out" / "evidence.json"

    code = smoke.main(_args(fake_host, "--expect-body", "Hello", "--evidence", str(evidence)))

    record = json.loads(evidence.read_text())
    assert code == 0
    assert record["result"] == "passed"
    assert record["versions"]["core_tools"] == "9.9.9"
    assert record["versions"]["function_runtime"] == "4.0.0"
    assert record["indexed_functions"] == ["hello: [GET] x"]
    assert record["packages"] == {"azure-functions": "1.0"}
    assert record["response"]["status"] == 200


def test_main_sends_a_post_body_and_checks_the_status(fake_host: Path) -> None:
    args = _args(fake_host, "--method", "POST", "--body", "{}", "--expect-status", "202")
    assert smoke.main([*args, "--expect-body", "accepted"]) == 0


@pytest.mark.parametrize(
    ("mode", "message"),
    [("zero", "Generating 0 job function"), ("crash", "exited early with code 3")],
)
def test_main_fails_when_the_host_is_unhealthy(
    fake_host: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    mode: str,
    message: str,
) -> None:
    monkeypatch.setenv("FAKE_FUNC_MODE", mode)
    evidence = tmp_path / "evidence.json"

    code = smoke.main(_args(fake_host, "--evidence", str(evidence)))

    assert code == 1
    assert message in capsys.readouterr().err
    assert json.loads(evidence.read_text())["result"] == "failed"


def test_main_fails_on_an_unexpected_body(fake_host: Path) -> None:
    assert smoke.main(_args(fake_host, "--expect-body", "absent", "--startup-timeout", "6")) == 1


@pytest.mark.parametrize(
    "build",
    [
        lambda root: root / "missing",
        lambda root: root / "recipe",
    ],
    ids=["no-function-app", "no-venv"],
)
def test_main_rejects_an_incomplete_recipe_directory(
    tmp_path: Path, build: object, capsys: pytest.CaptureFixture[str]
) -> None:
    (tmp_path / "recipe").mkdir()
    (tmp_path / "recipe" / "function_app.py").write_text("")
    target = build(tmp_path)  # type: ignore[operator]

    assert smoke.main(["--recipe-dir", str(target), "--route", "/x", "--no-azurite"]) == 1
    assert capsys.readouterr().err.startswith("host-smoke FAILED")


def test_main_rejects_a_zero_min_functions(fake_host: Path) -> None:
    assert smoke.main(_args(fake_host, "--min-functions", "0")) == 1


def test_a_port_squatter_on_10000_is_not_mistaken_for_azurite(
    fake_host: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(smoke, "_port_open", lambda port: True)
    code = smoke.main(
        ["--recipe-dir", str(fake_host), "--route", "/api/hello", "--startup-timeout", "5"]
    )
    assert code == 1
    assert "port 10000 is already in use" in capsys.readouterr().err


def _workflow() -> dict[str, Any]:
    return yaml.safe_load(_WORKFLOW.read_text())  # type: ignore[no-any-return]


def test_host_smoke_matrix_entries_are_complete_and_cover_major_integrations() -> None:
    """Offline: every matrix recipe names a route, method and expected content."""
    matrix = _workflow()["jobs"]["host-smoke"]["strategy"]["matrix"]["recipe"]
    for entry in matrix:
        assert {"name", "path", "route", "method", "expect"} <= set(entry), entry
        assert (_ROOT / entry["path"] / "function_app.py").is_file(), entry
        assert entry["route"].startswith("/api/"), entry
        assert (entry["method"] == "POST") == ("body" in entry), entry
    names = {entry["name"] for entry in matrix}
    assert {"personal-langgraph-agent", "doctor-diagnostics", "queue-producer-binding"} <= names
    assert len(names) == len(matrix)


def test_host_smoke_job_runs_the_harness_and_uploads_evidence() -> None:
    """Offline: the job runs the harness without swallowing errors and always uploads evidence."""
    workflow = _workflow()
    job = workflow["jobs"]["host-smoke"]
    steps = job["steps"]
    run_text = "\n".join(step.get("run", "") for step in steps)
    assert "python tools/recipe_host_smoke.py" in run_text
    assert "|| true" not in run_text
    upload = next(step for step in steps if "upload-artifact" in step.get("uses", ""))
    assert upload["if"] == "always()"
    assert upload["with"]["if-no-files-found"] == "error"
    assert "permissions" not in job  # inherits the read-only workflow default
    assert workflow["permissions"] == {"contents": "read"}
