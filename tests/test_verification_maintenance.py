import os
from pathlib import Path
import subprocess
import sys
import time
from unittest.mock import patch

import pytest

from tools import verification_host as host
from tools import verification_lanes as lanes

ROOT = Path(__file__).resolve().parents[1]


def test_maintenance_uses_existing_python_without_creating_hatch_environment(
    tmp_path: Path,
) -> None:
    environment = {**os.environ, "HATCH_DATA_DIR": str(tmp_path / "hatch"), "CI": ""}
    for target in ("doctor", "report", "clean"):
        result = subprocess.run(
            ["make", "-n", target, "HATCH=false", f"MAINTENANCE_PYTHON={sys.executable}"],
            cwd=ROOT,
            env=environment,
            capture_output=True,
            text=True,
            check=True,
        )
        assert "hatch run" not in result.stdout
    subprocess.run(
        ["make", "doctor", "HATCH=false", f"MAINTENANCE_PYTHON={sys.executable}"],
        cwd=ROOT,
        env=environment,
        capture_output=True,
        check=False,
    )
    assert not (tmp_path / "hatch").exists()


def test_quality_failure_saves_log_and_summary(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    summary = tmp_path / "job.md"
    monkeypatch.setenv("GITHUB_STEP_SUMMARY", str(summary))
    result = lanes.task(
        "check", [sys.executable, "-c", "print('password=CANARY_quality');raise SystemExit(7)"]
    )
    assert result.exit_code == 7
    assert result.status == "FAIL"
    assert (tmp_path / "test-results/check/summary.json").exists()
    assert "CANARY_quality" not in (tmp_path / "test-results/check/logs/runner.log").read_text()
    assert "check: FAIL" in summary.read_text()


def test_host_readiness_retries_timeout_then_success(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from collections.abc import Iterator
    from contextlib import contextmanager
    from unittest.mock import Mock

    import requests

    monkeypatch.setenv("AZURITE_CONNECTION_STRING", "storage")
    monkeypatch.setenv("VERIFICATION_LOG_DIR", str(tmp_path))
    process = Mock()
    process.poll.return_value = None
    response = Mock()
    response.status_code = 200
    response.json.return_value = {"state": "Running"}

    @contextmanager
    def child(*args: object) -> Iterator[Mock]:
        yield process

    with (
        patch.object(host, "child", child),
        patch.object(requests, "get", side_effect=[TimeoutError(), response]),
        patch.object(time, "sleep"),
    ):
        with host.host("apis-and-ingress/hello_http_minimal") as url:
            assert url.startswith("http://127.0.0.1:")


def test_host_smoke_installs_only_shipped_recipe_requirements(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from collections.abc import Iterator
    from contextlib import contextmanager
    from unittest.mock import Mock

    import requests

    monkeypatch.setenv("AZURITE_CONNECTION_STRING", "storage")
    monkeypatch.setenv("VERIFICATION_LOG_DIR", str(tmp_path))
    monkeypatch.setenv("VERIFICATION_ISOLATED_RECIPES", "1")
    process = Mock()
    process.poll.return_value = None
    response = Mock()
    response.status_code = 200
    response.json.return_value = {"state": "Running"}
    paths: list[str] = []

    @contextmanager
    def child(*args: object) -> Iterator[Mock]:
        paths.append(os.environ["PATH"])
        yield process

    with (
        patch.object(host, "child", child),
        patch.object(host, "run", return_value=0) as install,
        patch.object(requests, "get", return_value=response),
    ):
        with host.host("apis-and-ingress/hello_http_minimal"):
            pass
    commands = [call.args[0] for call in install.call_args_list]
    assert commands[0][1:3] == ["-m", "venv"]
    assert commands[1][1:5] == ["-m", "pip", "install", "-r"]
    assert commands[1][-1].endswith("app/requirements.txt")
    assert paths[0].split(os.pathsep)[0].endswith("venv/bin")


def test_known_secret_is_masked_before_patterns(monkeypatch: pytest.MonkeyPatch) -> None:
    from tools.verification_evidence import redact

    monkeypatch.setenv("MY_API_TOKEN", 'prefix;CANARY_exact \\"quoted\\"')
    assert "CANARY_exact" not in redact(os.environ["MY_API_TOKEN"])
    assert "CANARY_exact" not in redact(__import__("json").dumps(os.environ["MY_API_TOKEN"]))
