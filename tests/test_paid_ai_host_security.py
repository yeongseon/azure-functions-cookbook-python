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
def test_real_host_indexes_function_auth_and_local_requests_without_keys(tmp_path: Path) -> None:
    # Given a private copied app and unique emulator/host ports, without provider credentials.
    assert shutil.which("func") and shutil.which("azurite")
    project = ROOT / "examples/ai-and-agents/openai_direct_chat"
    for name in ("function_app.py", "host.json"):
        shutil.copy(project / name, tmp_path / name)
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
    env["PATH"] = str(Path(sys.executable).parent) + os.pathsep + env["PATH"]
    env["FUNCTIONS_WORKER_RUNTIME"] = "python"
    with ExitStack() as stack:
        az_log = stack.enter_context((tmp_path / "azurite.log").open("w"))
        host_log = stack.enter_context((tmp_path / "host.log").open("w"))
        azurite = subprocess.Popen(
            [
                "azurite",
                "--silent",
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
        assert bindings and all(binding["authLevel"].lower() == "function" for binding in bindings)
        # Then ordinary Core Tools still allows a keyless fallback request.
        request = Request(
            base + "/api/chat",
            data=b'{"message":"hello"}',
            headers={"Content-Type": "application/json"},
        )
        with urlopen(request, timeout=15) as response:
            assert response.status == 200
            assert json.load(response)["answer"].startswith("Fallback response:")
