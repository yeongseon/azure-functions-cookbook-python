import os
from pathlib import Path
import subprocess
from typing import Final

ROOT: Final = Path(__file__).resolve().parents[1]


def test_tracked_files_exclude_local_agent_state() -> None:
    tracked = subprocess.run(
        ["git", "-c", "core.pager=cat", "ls-files", "-z"],
        cwd=ROOT,
        env={**os.environ, "GIT_MASTER": "1"},
        check=True,
        capture_output=True,
        text=True,
    ).stdout.split("\0")

    assert not any(path == ".sisyphus" or path.startswith(".sisyphus/") for path in tracked)
    assert "AGENTS.md" in tracked


def test_ignore_rules_exclude_state_but_allow_contributor_guidance() -> None:
    state_paths = [".sisyphus/ralph-loop.local.md", ".sisyphus/sessions/example/state.json"]
    ignored = subprocess.run(
        ["git", "-c", "core.pager=cat", "check-ignore", "--no-index", "--stdin"],
        cwd=ROOT,
        env={**os.environ, "GIT_MASTER": "1"},
        input="\n".join([*state_paths, "AGENTS.md"]) + "\n",
        check=False,
        capture_output=True,
        text=True,
    )

    assert ignored.returncode == 0, ignored.stderr
    assert ignored.stdout.splitlines() == state_paths
