"""E2E test fixtures — Azurite emulator + Azure Functions host lifecycle."""

from __future__ import annotations

from contextlib import contextmanager
import importlib
import json
import os
from pathlib import Path
import shutil
import signal
import socket
import subprocess
import sys
import tempfile
import time
from types import ModuleType
from typing import Generator

import pytest

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
EXAMPLES_ROOT = PROJECT_ROOT / "examples"

AZURITE_CONN_STR = (
    "DefaultEndpointsProtocol=http;"
    "AccountName=devstoreaccount1;"
    "AccountKey=Eby8vdM02xNOcqFlqUwJPLlmEtlCDXJ1OUzFT50uSRZ6IFsuFq2UVErCz4I6tq/"
    "K1SZFPTOtr/KBHBeksoGMGw==;"
    "BlobEndpoint=http://127.0.0.1:10000/devstoreaccount1;"
    "QueueEndpoint=http://127.0.0.1:10001/devstoreaccount1;"
    "TableEndpoint=http://127.0.0.1:10002/devstoreaccount1;"
)

LOCAL_SETTINGS = {
    "IsEncrypted": False,
    "Values": {
        "AzureWebJobsStorage": "UseDevelopmentStorage=true",
        "FUNCTIONS_WORKER_RUNTIME": "python",
    },
}

FUNC_HOST_STARTUP_TIMEOUT = 90  # seconds — func start can be slow
AZURITE_STARTUP_TIMEOUT = 15


def _allocate_port() -> int:
    """Find and return a free port by binding to port 0."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("", 0))
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        return s.getsockname()[1]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def wait_for_port(port: int, host: str = "127.0.0.1", timeout: int = 60) -> None:
    """Block until *host:port* accepts a TCP connection or *timeout* expires."""
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            with socket.create_connection((host, port), timeout=2):
                return
        except (ConnectionRefusedError, OSError, socket.timeout):
            time.sleep(0.5)
    raise TimeoutError(f"Port {port} not ready after {timeout}s")


def _kill_process_group(proc: subprocess.Popen[bytes]) -> None:
    """Kill the entire process group so child workers are also terminated."""
    try:
        pgid = os.getpgid(proc.pid)
        os.killpg(pgid, signal.SIGTERM)
    except (ProcessLookupError, OSError):
        pass
    try:
        proc.wait(timeout=5)
    except subprocess.TimeoutExpired:
        try:
            pgid = os.getpgid(proc.pid)
            os.killpg(pgid, signal.SIGKILL)
        except (ProcessLookupError, OSError):
            pass


def _write_local_settings(
    example_dir: Path,
    extra_values: dict[str, str] | None = None,
) -> Path:
    """Write a local.settings.json for Azurite into *example_dir*."""
    settings = json.loads(json.dumps(LOCAL_SETTINGS))  # deep copy
    if extra_values:
        settings["Values"].update(extra_values)
    settings_path = example_dir / "local.settings.json"
    settings_path.write_text(json.dumps(settings, indent=2))
    return settings_path


def _remove_local_settings(example_dir: Path) -> None:
    """Remove the generated local.settings.json."""
    settings_path = example_dir / "local.settings.json"
    if settings_path.exists():
        settings_path.unlink()


# ---------------------------------------------------------------------------
# Azurite session fixture
# ---------------------------------------------------------------------------


@pytest.fixture(scope="session")
def azurite() -> Generator[subprocess.Popen[bytes], None, None]:
    """Start Azurite once for the entire test session."""
    tmpdir = tempfile.mkdtemp(prefix="azurite_")
    proc = subprocess.Popen(
        [
            "azurite",
            "--silent",
            "--skipApiVersionCheck",
            "--location",
            tmpdir,
            "--debug",
            os.path.join(tmpdir, "debug.log"),
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    try:
        wait_for_port(10000, timeout=AZURITE_STARTUP_TIMEOUT)
    except TimeoutError:
        proc.terminate()
        shutil.rmtree(tmpdir, ignore_errors=True)
        pytest.fail("Azurite failed to start within timeout")

    yield proc

    proc.terminate()
    try:
        proc.wait(timeout=5)
    except subprocess.TimeoutExpired:
        proc.kill()
    shutil.rmtree(tmpdir, ignore_errors=True)


# ---------------------------------------------------------------------------
# func host context manager (used by per-example fixtures)
# ---------------------------------------------------------------------------


@contextmanager
def run_func_host(
    example_path: str,
    port: int | None = None,
    timeout: int = FUNC_HOST_STARTUP_TIMEOUT,
    env_vars: dict[str, str] | None = None,
) -> Generator[str, None, None]:
    """Context manager: start ``func start`` for *example_path*, yield base URL.

    Parameters
    ----------
    example_path:
        Relative path under ``examples/`` (e.g. ``"http/hello_http_minimal"``).
    port:
        HTTP port for the host.  Auto-allocated when *None*.
    timeout:
        Max seconds to wait for the host to become ready.
    env_vars:
        Extra environment variables to inject into the func host process.

    Yields
    ------
    str
        Base URL like ``"http://127.0.0.1:7071"``.
    """
    if port is None:
        port = _allocate_port()

    example_dir = EXAMPLES_ROOT / example_path
    if not example_dir.is_dir():
        pytest.fail(f"Example directory does not exist: {example_dir}")

    _write_local_settings(example_dir, extra_values=env_vars)

    env = os.environ.copy()
    env["AzureWebJobsStorage"] = "UseDevelopmentStorage=true"
    env["FUNCTIONS_WORKER_RUNTIME"] = "python"
    if env_vars:
        env.update(env_vars)

    proc = subprocess.Popen(
        ["func", "start", "--port", str(port)],
        cwd=str(example_dir),
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        preexec_fn=os.setsid,
    )

    try:
        wait_for_port(port, timeout=timeout)
    except TimeoutError:
        # Capture output for debugging
        stdout_data = b""
        try:
            stdout_data, _ = proc.communicate(timeout=3)
        except subprocess.TimeoutExpired:
            _kill_process_group(proc)
        _remove_local_settings(example_dir)
        output = stdout_data.decode(errors="replace")[-2000:]
        pytest.fail(
            f"func host for {example_path} failed to start on port {port} "
            f"within {timeout}s.\nOutput tail:\n{output}"
        )

    base_url = f"http://127.0.0.1:{port}"
    try:
        yield base_url
    finally:
        _kill_process_group(proc)
        _remove_local_settings(example_dir)


def ensure_azurite_queue(queue_name: str) -> None:
    """Create a queue in Azurite if it doesn't already exist."""
    from azure.storage.queue import QueueServiceClient

    svc = QueueServiceClient.from_connection_string(AZURITE_CONN_STR)
    try:
        svc.create_queue(queue_name)
    except Exception:  # noqa: BLE001
        pass  # queue already exists


def ensure_azurite_container(container_name: str) -> None:
    """Create a blob container in Azurite if it doesn't already exist."""
    from azure.storage.blob import BlobServiceClient

    svc = BlobServiceClient.from_connection_string(AZURITE_CONN_STR)
    try:
        svc.create_container(container_name)
    except Exception:  # noqa: BLE001
        pass  # container already exists


# ---------------------------------------------------------------------------
# Durable polling helper
# ---------------------------------------------------------------------------


def poll_durable_status(
    status_url: str,
    timeout: int = 60,
    poll_interval: float = 2.0,
) -> dict:
    """Poll a Durable Functions status URL until terminal state or timeout.

    Returns the final status payload dict.
    """
    import requests

    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        resp = requests.get(status_url, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            runtime_status = data.get("runtimeStatus", "")
            if runtime_status in ("Completed", "Failed", "Terminated", "Canceled"):
                return data
        time.sleep(poll_interval)

    pytest.fail(f"Durable orchestration did not complete within {timeout}s: {status_url}")
    return {}  # unreachable but satisfies type checker


# ---------------------------------------------------------------------------
# Module import helper (shared by smoke & durable tests)
# ---------------------------------------------------------------------------


def import_function_app(example_path: str) -> ModuleType:
    """Import a function_app.py module from an example directory.

    Uses importlib to load the module by file path, avoiding sys.path
    pollution and module name collisions between examples.
    """
    example_dir = EXAMPLES_ROOT / example_path
    function_app_file = example_dir / "function_app.py"

    if not function_app_file.exists():
        pytest.fail(f"function_app.py not found: {function_app_file}")

    example_dir_str = str(example_dir)
    original_path = sys.path.copy()
    original_modules = set(sys.modules.keys())

    try:
        sys.path.insert(0, example_dir_str)

        # Clear any cached 'app' module to avoid cross-example conflicts
        modules_to_remove = [k for k in sys.modules if k == "app" or k.startswith("app.")]
        for mod_key in modules_to_remove:
            del sys.modules[mod_key]

        spec = importlib.util.spec_from_file_location(
            f"function_app_{example_path.replace('/', '_')}",
            function_app_file,
        )
        if spec is None or spec.loader is None:
            pytest.fail(f"Could not create import spec for {function_app_file}")

        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
    finally:
        sys.path = original_path
        # Clean up loaded app.* modules to prevent leakage
        new_modules = set(sys.modules.keys()) - original_modules
        for mod_key in new_modules:
            if mod_key == "app" or mod_key.startswith("app."):
                del sys.modules[mod_key]
