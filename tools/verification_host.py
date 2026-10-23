from __future__ import annotations

from collections.abc import Iterator, Mapping
from contextlib import contextmanager
import json
import os
from pathlib import Path
import shutil
import socket
import subprocess
import sys
import tempfile
import time
import uuid

from tools.verification_process import child, configured, run

ROOT = Path(__file__).resolve().parents[1]
DEV_KEY = "Eby8vdM02xNOcqFlqUwJPLlmEtlCDXJ1OUzFT50uSRZ6IFsuFq2UVErCz4I6tq/K1SZFPTOtr/KBHBeksoGMGw=="


def port() -> int:
    with socket.socket() as stream:
        stream.bind(("127.0.0.1", 0))
        return int(stream.getsockname()[1])


def ready(process: subprocess.Popen[str], ports: tuple[int, ...]) -> None:
    deadline = time.monotonic() + 30
    pending = set(ports)
    while pending and time.monotonic() < deadline:
        if process.poll() is not None:
            raise RuntimeError("Owned Azurite exited before readiness")
        for number in tuple(pending):
            try:
                with socket.create_connection(("127.0.0.1", number), timeout=0.5):
                    pending.remove(number)
            except OSError:
                time.sleep(0.1)
    if pending:
        raise TimeoutError("Owned Azurite did not become ready")


@contextmanager
def azurite(directory: Path) -> Iterator[str]:
    ports = (port(), port(), port())
    connection = (
        f"DefaultEndpointsProtocol=http;AccountName=devstoreaccount1;AccountKey={DEV_KEY};"
        f"BlobEndpoint=http://127.0.0.1:{ports[0]}/devstoreaccount1;"
        f"QueueEndpoint=http://127.0.0.1:{ports[1]}/devstoreaccount1;"
        f"TableEndpoint=http://127.0.0.1:{ports[2]}/devstoreaccount1;"
    )
    with tempfile.TemporaryDirectory(prefix="cookbook-azurite-") as temporary:
        command = [
            "azurite",
            "--silent",
            "--skipApiVersionCheck",
            "--blobHost",
            "127.0.0.1",
            "--queueHost",
            "127.0.0.1",
            "--tableHost",
            "127.0.0.1",
            "--location",
            temporary,
            "--blobPort",
            str(ports[0]),
            "--queuePort",
            str(ports[1]),
            "--tablePort",
            str(ports[2]),
        ]
        with child(command, directory / "logs/azurite.log") as process:
            ready(process, ports)
            print(f"Owned Azurite pid={process.pid} ports={ports}; temporary storage")
            with configured(
                {
                    "AZURITE_CONNECTION_STRING": connection,
                    "AzureWebJobsStorage": connection,
                    "VERIFICATION_OWNED_HOST": "1",
                    "VERIFICATION_LOG_DIR": str(directory / "logs"),
                }
            ):
                yield connection


@contextmanager
def host(example: str, extra: Mapping[str, str] | None = None) -> Iterator[str]:
    import requests

    number = port()
    connection = os.environ["AZURITE_CONNECTION_STRING"]
    values = {
        "AzureWebJobsStorage": connection,
        "FUNCTIONS_WORKER_RUNTIME": "python",
        "StorageConnection": connection,
        "PYTHON_ISOLATE_WORKER_DEPENDENCIES": "1",
    }
    values.update(extra or {})
    values = {
        key: connection if value == "UseDevelopmentStorage=true" else value
        for key, value in values.items()
    }
    with tempfile.TemporaryDirectory(prefix="cookbook-host-") as temporary:
        project = Path(temporary) / "app"
        shutil.copytree(
            ROOT / "examples" / example,
            project,
            ignore=shutil.ignore_patterns(".venv", "__pycache__", ".python_packages", "*.db"),
        )
        (project / "local.settings.json").write_text(
            json.dumps({"IsEncrypted": False, "Values": values})
        )
        log = (
            Path(os.environ["VERIFICATION_LOG_DIR"])
            / f"{example.replace('/', '-')}-{uuid.uuid4().hex[:8]}.log"
        )
        interpreter = Path(sys.executable)
        if os.environ.get("VERIFICATION_ISOLATED_RECIPES") == "1":
            environment = Path(temporary) / "venv"
            for command in (
                [sys.executable, "-m", "venv", str(environment)],
                [
                    str(environment / "bin/python"),
                    "-m",
                    "pip",
                    "install",
                    "-r",
                    str(project / "requirements.txt"),
                ],
            ):
                if run(command, log.with_suffix(".install.log"), 300):
                    raise RuntimeError(f"Recipe requirements installation failed for {example}")
            interpreter = environment / "bin/python"
            values["VIRTUAL_ENV"] = str(environment)
        values["PATH"] = str(interpreter.parent) + os.pathsep + os.environ["PATH"]
        with (
            configured(values),
            child(
                ["func", "start", "--python", "--port", str(number)],
                log,
                project,
            ) as process,
        ):
            base = f"http://127.0.0.1:{number}"
            deadline = time.monotonic() + 120
            while time.monotonic() < deadline:
                if process.poll() is not None:
                    raise RuntimeError(f"Owned host exited for {example}")
                try:
                    response = requests.get(base + "/admin/host/status", timeout=2)
                    if response.status_code == 200 and response.json().get("state") == "Running":
                        print(f"Owned host pid={process.pid} port={number} recipe={example}")
                        yield base
                        return
                except (requests.RequestException, ValueError, OSError):
                    time.sleep(0.2)
            raise TimeoutError(f"Host indexing/readiness timeout for {example}")
