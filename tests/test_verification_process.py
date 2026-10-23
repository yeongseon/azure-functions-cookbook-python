import os
from pathlib import Path
import signal
import subprocess
import sys
import time

import pytest

from tools.verification_process import child, run


def test_owned_child_is_stopped_after_body_failure(tmp_path: Path) -> None:
    # Given: a real owned process.
    with pytest.raises(RuntimeError, match="failure"):
        with child([sys.executable, "-c", "import time; time.sleep(60)"], tmp_path / "log") as proc:
            # When: the calling body fails.
            raise RuntimeError("failure")
    # Then: cleanup reaps the process.
    assert proc.returncode is not None


def test_process_exit_and_redaction_are_preserved(tmp_path: Path) -> None:
    # Given: a command with secret output and an explicit failure.
    log = tmp_path / "log"
    # When: it executes through the shared runner.
    code = run([sys.executable, "-c", "print('AccountKey=canary-process'); exit(42)"], log)
    # Then: status survives and credentials do not.
    assert code == 42
    assert "canary-process" not in log.read_text()


def test_timeout_terminates_only_owned_process(tmp_path: Path) -> None:
    # Given: an unrelated process alongside a timed-out owned command.
    with subprocess.Popen([sys.executable, "-c", "import time; time.sleep(60)"]) as unrelated:
        try:
            # When: the owned command times out.
            code = run(
                [sys.executable, "-c", "import time; time.sleep(60)"],
                tmp_path / "log",
                0.05,
            )
            # Then: unrelated services remain alive.
            assert code == 124
            assert unrelated.poll() is None
        finally:
            unrelated.terminate()


def test_interruption_stops_detached_descendants(tmp_path: Path) -> None:
    # Given: an owned process that launches a child in a separate session.
    pidfile = tmp_path / "pid"
    script = (
        "import pathlib, subprocess, sys, time; "
        "p=subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(60)'], "
        "start_new_session=True); "
        f"pathlib.Path({str(pidfile)!r}).write_text(str(p.pid)); time.sleep(60)"
    )
    with child([sys.executable, "-c", script], tmp_path / "log"):
        deadline = time.monotonic() + 5
        while not pidfile.exists() and time.monotonic() < deadline:
            time.sleep(0.01)
        pid = int(pidfile.read_text())
    # When / Then: the owned descendant is gone or a terminated zombie, never running.
    status = Path(f"/proc/{pid}/status")
    if status.exists():
        assert "State:\tZ" in status.read_text()
    else:
        with pytest.raises(ProcessLookupError):
            os.kill(pid, signal.SIGCONT)
