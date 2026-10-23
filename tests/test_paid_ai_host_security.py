"""Opt-in real host indexing check; local key bypass is not Azure enforcement evidence."""

from __future__ import annotations

from contextlib import ExitStack
import json
import os
from pathlib import Path
import shutil
import signal
import socket
import subprocess
import sys
import threading
from urllib.error import URLError
from urllib.request import Request, urlopen

import pytest

ROOT = Path(__file__).resolve().parents[1]
RECIPES = ("openai_direct_chat", "ai_image_generation", "streaming_ai_response")


@pytest.fixture(scope="module", params=RECIPES)
def recipe_environment(
    request: pytest.FixtureRequest, tmp_path_factory: pytest.TempPathFactory
) -> tuple[str, Path]:
    name = str(request.param)
    environment = tmp_path_factory.mktemp(name) / "venv"
    subprocess.run([sys.executable, "-m", "venv", str(environment)], check=True)
    subprocess.run(
        [
            str(environment / "bin/python"),
            "-m",
            "pip",
            "install",
            "-r",
            str(ROOT / "examples/ai-and-agents" / name / "requirements.txt"),
        ],
        check=True,
        capture_output=True,
    )
    return name, environment


def free_port() -> int:
    with socket.socket() as connection:
        connection.bind(("127.0.0.1", 0))
        return int(connection.getsockname()[1])


def stop(process: subprocess.Popen[str]) -> None:
    if process.poll() is None:
        os.killpg(process.pid, signal.SIGTERM)
        try:
            process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            os.killpg(process.pid, signal.SIGKILL)
            process.wait(timeout=10)


@pytest.mark.skipif(
    os.getenv("COOKBOOK_RUN_PAID_AI_HOST") != "true", reason="opt-in Core Tools/Azurite"
)
@pytest.mark.parametrize("setting", [None, "true", "True"])
def test_real_host_indexes_function_auth_and_local_requests_without_keys(
    tmp_path: Path, recipe_environment: tuple[str, Path], setting: str | None
) -> None:
    # Given a private copied app and unique emulator/host ports, without provider credentials.
    assert shutil.which("func") and shutil.which("azurite")
    name, environment = recipe_environment
    project = ROOT / "examples/ai-and-agents" / name
    for filename in ("function_app.py", "host.json"):
        shutil.copy(project / filename, tmp_path / filename)
    if name == "openai_direct_chat" and setting is None:
        for filename in ("conftest.py", "sitecustomize.py"):
            (tmp_path / filename).write_text("raise RuntimeError('UNREQUESTED_AUTO_IMPORT')\n")
    ports = [free_port() for _ in range(4)]
    storage = (
        "DefaultEndpointsProtocol=http;AccountName=devstoreaccount1;"
        "AccountKey=Eby8vdM02xNOcqFlqUwJPLlmEtlCDXJ1OUzFT50uSRZ6IFsuFq2UVErCz4I6tq/"
        "K1SZFPTOtr/KBHBeksoGMGw==;"
        f"BlobEndpoint=http://127.0.0.1:{ports[0]}/devstoreaccount1;"
        f"QueueEndpoint=http://127.0.0.1:{ports[1]}/devstoreaccount1;"
        f"TableEndpoint=http://127.0.0.1:{ports[2]}/devstoreaccount1;"
    )
    (tmp_path / "local.settings.json").write_text(
        json.dumps(
            {
                "IsEncrypted": False,
                "Values": {
                    "AzureWebJobsStorage": storage,
                    "FUNCTIONS_WORKER_RUNTIME": "python",
                },
            }
        )
    )
    env = {
        key: value
        for key, value in os.environ.items()
        if not key.startswith("AZURE_OPENAI") and key not in {"COOKBOOK_PUBLIC_DEMO", "OPENAI_LOG"}
    }
    env["PATH"] = str(environment / "bin") + os.pathsep + env["PATH"]
    env["VIRTUAL_ENV"] = str(environment)
    if setting is not None:
        env["COOKBOOK_PUBLIC_DEMO"] = setting
    env["FUNCTIONS_WORKER_RUNTIME"] = "python"
    with ExitStack() as stack:
        az_log = stack.enter_context((tmp_path / "azurite.log").open("w"))
        host_log = stack.enter_context((tmp_path / "host.log").open("w"))
        azurite = subprocess.Popen(
            [
                "azurite",
                "--silent",
                "--skipApiVersionCheck",
                "--location",
                str(tmp_path / "storage"),
                "--blobPort",
                str(ports[0]),
                "--queuePort",
                str(ports[1]),
                "--tablePort",
                str(ports[2]),
            ],
            stdout=az_log,
            stderr=subprocess.STDOUT,
            text=True,
            start_new_session=True,
        )
        stack.callback(stop, azurite)
        host = subprocess.Popen(
            ["func", "start", "--python", "--port", str(ports[3])],
            cwd=tmp_path,
            env=env,
            stdout=host_log,
            stderr=subprocess.STDOUT,
            text=True,
            start_new_session=True,
        )
        stack.callback(stop, host)
        base = f"http://127.0.0.1:{ports[3]}"
        # When the real worker publishes indexing metadata, inspect its binding declaration.
        metadata = None
        for _ in range(120):
            assert host.poll() is None, "Host exited before indexing; inspect private test log"
            try:
                with urlopen(base + "/admin/functions", timeout=2) as response:
                    metadata = json.load(response)
                if metadata:
                    break
            except (URLError, TimeoutError):
                threading.Event().wait(0.5)
        assert metadata, "Host did not expose indexed functions"
        bindings = [
            binding
            for item in metadata
            for binding in item["config"]["bindings"]
            if binding["type"] == "httpTrigger"
        ]
        expected = "anonymous" if setting == "true" else "function"
        assert bindings and all(binding["authLevel"].lower() == expected for binding in bindings)
        host_log.flush()
        output = (tmp_path / "host.log").read_text()
        print(
            json.dumps(
                {
                    "recipe": name,
                    "setting": setting,
                    "auth": expected,
                    "logger_warning_visible": "Public paid-AI demo enabled" in output,
                    "ports": ports,
                }
            )
        )
        # Then ordinary Core Tools still allows a keyless fallback request.
        route, payload = (
            ("/api/images/generate", b'{"prompt":"hello"}')
            if name == "ai_image_generation"
            else (
                "/api/stream" if name == "streaming_ai_response" else "/api/chat",
                b'{"message":"hello"}',
            )
        )
        request = Request(
            base + route,
            data=payload,
            headers={"Content-Type": "application/json"},
        )
        with urlopen(request, timeout=15) as response:
            assert response.status == 200
            assert response.read()
