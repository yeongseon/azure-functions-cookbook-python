from __future__ import annotations

from collections.abc import Iterator, Mapping
from contextlib import contextmanager
import os
from pathlib import Path
import signal
import subprocess
import tempfile
import time
from types import FrameType

from tools.verification_evidence import redact


def terminate(process: subprocess.Popen[str]) -> None:
    snapshot = subprocess.run(
        ["ps", "-eo", "pid=,ppid="],
        capture_output=True,
        text=True,
        check=True,
    )
    pairs = [tuple(map(int, line.split())) for line in snapshot.stdout.splitlines()]
    owned = {process.pid}
    while descendants := {pid for pid, parent in pairs if parent in owned} - owned:
        owned.update(descendants)
    for pid in sorted(owned, reverse=True):
        try:
            os.kill(pid, signal.SIGTERM)
        except ProcessLookupError:
            continue
    try:
        try:
            process.wait(timeout=15)
        except subprocess.TimeoutExpired:
            os.killpg(process.pid, signal.SIGKILL)
            process.wait()
        os.killpg(process.pid, signal.SIGKILL)
    except ProcessLookupError:
        process.wait()
    for pid in owned - {process.pid}:
        try:
            os.kill(pid, signal.SIGKILL)
        except ProcessLookupError:
            continue
    deadline = time.monotonic() + 5
    while time.monotonic() < deadline:
        states = subprocess.run(
            ["ps", "-o", "stat=", "-p", ",".join(map(str, owned))],
            capture_output=True,
            text=True,
            check=False,
        ).stdout.split()
        if all(state.startswith("Z") for state in states):
            return
        time.sleep(0.01)
    raise TimeoutError("Owned descendant processes did not exit after termination")


@contextmanager
def configured(values: Mapping[str, str]) -> Iterator[None]:
    previous = {key: os.environ.get(key) for key in values}
    os.environ.update(values)
    try:
        yield
    finally:
        for key, value in previous.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value


@contextmanager
def child(
    command: list[str], log: Path, cwd: Path | None = None
) -> Iterator[subprocess.Popen[str]]:
    log.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryFile(mode="w+", encoding="utf-8") as output:
        with subprocess.Popen(
            command,
            cwd=cwd,
            stdout=output,
            stderr=subprocess.STDOUT,
            text=True,
            start_new_session=True,
        ) as process:

            def interrupted(number: int, frame: FrameType | None) -> None:
                raise KeyboardInterrupt(number)

            previous = {
                sig: signal.signal(sig, interrupted) for sig in (signal.SIGTERM, signal.SIGINT)
            }
            try:
                yield process
            finally:
                terminate(process)
                for sig, handler in previous.items():
                    signal.signal(sig, handler)
                output.seek(0)
                text = redact(output.read())
                log.write_text(text, encoding="utf-8")
                print(text, end="")


def run(command: list[str], log: Path, timeout: float = 600, *, cwd: Path | None = None) -> int:
    try:
        with child(command, log, cwd) as process:
            try:
                code = process.wait(timeout=timeout)
                return code if code >= 0 else 128 - code
            except subprocess.TimeoutExpired:
                return 124
    except FileNotFoundError as error:
        log.parent.mkdir(parents=True, exist_ok=True)
        log.write_text(redact(str(error)))
        return 127
