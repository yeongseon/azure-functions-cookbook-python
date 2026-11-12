"""Run one recipe on a real Azure Functions Core Tools host and record what actually happened.

Used by the required ``host-smoke`` CI job (``.github/workflows/ci-test.yml``). It starts Azurite
and ``func start`` for a recipe directory, requires the host to index at least one function, sends
one meaningful request, checks the status and body, and writes a JSON evidence record (host and
toolchain versions, indexed functions, the request outcome). Any problem exits non-zero: a host
that indexes zero functions, a worker failure, an unexpected response or a timeout is never a pass.

This is local-host evidence only. It proves the recipe indexes and answers on Core Tools with
Azurite, not that it works in Azure.
"""

from __future__ import annotations

import argparse
from collections.abc import Sequence
import json
import os
from pathlib import Path
import re
import shutil
import signal
import socket
import subprocess
import sys
import tempfile
import time
from typing import Any
import urllib.error
import urllib.request

_FAILURE_MARKERS = (
    "Generating 0 job function",
    "Worker failed",
    "Host startup operation has been canceled",
)
_FUNCTION_LINE = re.compile(r"^\s+(?P<name>[\w.-]+): (?P<detail>.+)$")
_RUNTIME_VERSION = re.compile(r"Function Runtime Version:\s+(?P<version>\S+)")
_RECORDED_PREFIXES = ("azure-functions", "langgraph", "langchain", "pydantic")


class HostSmokeError(RuntimeError):
    """The recipe did not produce host-level evidence."""


def indexed_functions(log: str) -> list[str]:
    """Return ``name: detail`` lines from the host's ``Functions:`` section (empty if none)."""
    found: list[str] = []
    in_section = False
    for line in log.splitlines():
        if line.strip() == "Functions:":
            in_section = True
            continue
        if not in_section:
            continue
        match = _FUNCTION_LINE.match(line)
        if match:
            found.append(f"{match['name']}: {match['detail'].strip()}")
        elif line.strip() and not line.startswith((" ", "\t")):
            break
    return found


def runtime_version(log: str) -> str | None:
    match = _RUNTIME_VERSION.search(log)
    return match["version"] if match else None


def failure_marker(log: str) -> str | None:
    return next((marker for marker in _FAILURE_MARKERS if marker in log), None)


def check_response(status: int, body: str, expect_status: int, expect_body: Sequence[str]) -> None:
    """Raise unless the response has the expected status and contains every expected substring."""
    if status != expect_status:
        raise HostSmokeError(f"expected HTTP {expect_status}, got {status}: {body[:300]}")
    missing = [text for text in expect_body if text not in body]
    if missing:
        raise HostSmokeError(f"response body is missing {missing}: {body[:300]}")


def _first_line(command: Sequence[str]) -> str:
    try:
        completed = subprocess.run(  # noqa: S603 - fixed argv, no shell
            command, capture_output=True, text=True, timeout=30, check=False
        )
    except (OSError, subprocess.SubprocessError):
        return "unavailable"
    lines = (completed.stdout or completed.stderr).strip().splitlines()
    return lines[0] if lines else "unavailable"


def installed_packages(python: Path) -> dict[str, str]:
    """Versions of the toolkit/runtime packages installed in the recipe's own environment."""
    completed = subprocess.run(  # noqa: S603 - fixed argv, no shell
        [str(python), "-m", "pip", "list", "--format=json"],
        capture_output=True,
        text=True,
        timeout=120,
        check=True,
    )
    return {
        item["name"]: item["version"]
        for item in json.loads(completed.stdout)
        if item["name"].lower().startswith(_RECORDED_PREFIXES)
    }


def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def _port_open(port: int) -> bool:
    try:
        with socket.create_connection(("127.0.0.1", port), timeout=2):
            return True
    except OSError:
        return False


def _wait_port(port: int, timeout: float) -> bool:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if _port_open(port):
            return True
        time.sleep(0.5)
    return False


def _stop(proc: subprocess.Popen[bytes]) -> None:
    for sig in (signal.SIGTERM, signal.SIGKILL):
        try:
            os.killpg(os.getpgid(proc.pid), sig)
        except (ProcessLookupError, PermissionError):
            return
        try:
            proc.wait(timeout=5)
            return
        except subprocess.TimeoutExpired:
            continue


def _request(url: str, method: str, body: str | None) -> tuple[int, str]:
    data = body.encode() if body is not None else None
    headers = {"Content-Type": "application/json"} if body is not None else {}
    request = urllib.request.Request(url, data=data, method=method, headers=headers)  # noqa: S310
    try:
        with urllib.request.urlopen(request, timeout=20) as response:  # noqa: S310
            return int(response.status), response.read().decode(errors="replace")
    except urllib.error.HTTPError as error:
        return error.code, error.read().decode(errors="replace")
    except OSError:
        return 0, ""


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--recipe-dir", type=Path, required=True)
    parser.add_argument("--route", required=True, help="Path with leading slash, e.g. /api/hello")
    parser.add_argument("--method", default="GET")
    parser.add_argument("--body", help="JSON request body (sent as application/json)")
    parser.add_argument("--expect-status", type=int, default=200)
    parser.add_argument("--expect-body", action="append", default=[], metavar="TEXT")
    parser.add_argument("--min-functions", type=int, default=1)
    parser.add_argument("--startup-timeout", type=float, default=120)
    parser.add_argument("--no-azurite", action="store_true", help="Do not start Azurite")
    parser.add_argument(
        "--python", type=Path, help="Recipe venv python (default: .venv/bin/python)"
    )
    parser.add_argument("--evidence", type=Path, help="Write the JSON evidence record here")
    return parser


def run(args: argparse.Namespace) -> dict[str, Any]:
    """Start the host, send the request, return the evidence record or raise ``HostSmokeError``."""
    recipe_dir: Path = args.recipe_dir.resolve()
    python: Path = args.python or recipe_dir / ".venv" / "bin" / "python"
    if not (recipe_dir / "function_app.py").is_file():
        raise HostSmokeError(f"{recipe_dir} has no function_app.py")
    if not python.exists():
        raise HostSmokeError(f"recipe virtualenv python not found: {python}")
    if args.min_functions < 1:
        raise HostSmokeError("--min-functions must be at least 1")

    workdir = Path(tempfile.mkdtemp(prefix="host-smoke-"))
    func_log = workdir / "func-host.log"
    azurite: subprocess.Popen[bytes] | None = None
    host: subprocess.Popen[bytes] | None = None
    port = _free_port()
    try:
        env = os.environ | {
            "AzureWebJobsStorage": "UseDevelopmentStorage=true",
            "FUNCTIONS_WORKER_RUNTIME": "python",
            "PATH": f"{python.parent}{os.pathsep}{os.environ.get('PATH', '')}",
        }
        if not args.no_azurite:
            if _port_open(10000):
                raise HostSmokeError("port 10000 is already in use; stop the other Azurite first")
            azurite = subprocess.Popen(  # noqa: S603,S607 - fixed argv, no shell
                [
                    "azurite",
                    "--silent",
                    "--skipApiVersionCheck",
                    "--location",
                    str(workdir / "azurite"),
                ],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                start_new_session=True,
            )
            if not _wait_port(10000, 30):
                raise HostSmokeError("Azurite did not open port 10000")
        with func_log.open("wb") as sink:
            host = subprocess.Popen(  # noqa: S603,S607 - fixed argv, no shell
                ["func", "start", "--python", "--port", str(port)],
                cwd=recipe_dir,
                env=env,
                stdout=sink,
                stderr=subprocess.STDOUT,
                start_new_session=True,
            )

        url = f"http://127.0.0.1:{port}{args.route}"
        deadline = time.monotonic() + args.startup_timeout
        status, body = 0, ""
        while time.monotonic() < deadline:
            marker = failure_marker(func_log.read_text(errors="replace"))
            if marker:
                raise HostSmokeError(f"host reported `{marker}`")
            if host.poll() is not None:
                raise HostSmokeError(f"func host exited early with code {host.returncode}")
            if _port_open(port):
                status, body = _request(url, args.method, args.body)
                # A host that is not ready answers 404/5xx; only the expected answer ends the wait.
                if status == args.expect_status:
                    break
            time.sleep(2)
        log = func_log.read_text(errors="replace")
        functions = indexed_functions(log)
        if len(functions) < args.min_functions:
            raise HostSmokeError(
                f"host indexed {len(functions)} function(s), need at least {args.min_functions}"
            )
        check_response(status, body, args.expect_status, args.expect_body)

        return {
            "recipe": recipe_dir.name,
            "recipe_path": str(args.recipe_dir),
            "commit": os.environ.get("GITHUB_SHA") or _first_line(["git", "rev-parse", "HEAD"]),
            "versions": {
                "core_tools": _first_line(["func", "--version"]),
                "function_runtime": runtime_version(log),
                "azurite": None if args.no_azurite else _first_line(["azurite", "--version"]),
                "python": _first_line([str(python), "--version"]),
            },
            "packages": installed_packages(python),
            "indexed_functions": functions,
            "request": {"method": args.method, "route": args.route},
            "response": {"status": status, "body_prefix": body[:200]},
            "result": "passed",
        }
    except HostSmokeError:
        if func_log.exists():
            tail = func_log.read_text(errors="replace").splitlines()[-60:]
            print("--- func host log (tail) ---\n" + "\n".join(tail), file=sys.stderr)
        raise
    finally:
        for proc in (host, azurite):
            if proc is not None:
                _stop(proc)
        shutil.rmtree(workdir, ignore_errors=True)


def _write_evidence(path: Path | None, record: dict[str, Any]) -> None:
    if path is not None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n")


def main(argv: Sequence[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    try:
        evidence = run(args)
    except HostSmokeError as error:
        print(f"host-smoke FAILED: {error}", file=sys.stderr)
        _write_evidence(
            args.evidence,
            {"recipe_path": str(args.recipe_dir), "result": "failed", "error": str(error)},
        )
        return 1
    print(json.dumps(evidence, indent=2, sort_keys=True))
    _write_evidence(args.evidence, evidence)
    return 0


if __name__ == "__main__":
    sys.exit(main())
