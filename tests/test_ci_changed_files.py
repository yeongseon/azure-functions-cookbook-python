from __future__ import annotations

import os
from pathlib import Path
import subprocess

SCRIPT = Path(__file__).resolve().parents[1] / "tools" / "ci_changed_files.sh"


def git(repository: Path, *arguments: str) -> str:
    result = subprocess.run(
        ["git", *arguments],
        cwd=repository,
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def commit_file(repository: Path, name: str, content: str) -> str:
    (repository / name).write_text(content, encoding="utf-8")
    git(repository, "add", name)
    git(repository, "commit", "-m", f"change {name}")
    return git(repository, "rev-parse", "HEAD")


def run_push_range(repository: Path, before: str, after: str) -> subprocess.CompletedProcess[str]:
    output = repository / "changed.txt"
    return subprocess.run(
        ["bash", str(SCRIPT), str(output)],
        cwd=repository,
        env={**os.environ, "EVENT_NAME": "push", "BEFORE_SHA": before, "SHA": after},
        check=False,
        capture_output=True,
        text=True,
    )


def test_push_range_lists_changes_when_before_is_an_ancestor(tmp_path: Path) -> None:
    # Given: a normal two-commit push range.
    git(tmp_path, "init")
    git(tmp_path, "config", "user.name", "CI Test")
    git(tmp_path, "config", "user.email", "ci@example.invalid")
    before = commit_file(tmp_path, "README.md", "before\n")
    after = commit_file(tmp_path, "README.md", "after\n")

    # When: the workflow range wrapper evaluates the push.
    result = run_push_range(tmp_path, before, after)

    # Then: classification receives the changed path.
    assert result.returncode == 0, result.stderr
    assert (tmp_path / "changed.txt").read_text(encoding="utf-8") == "README.md\n"


def test_push_range_fails_closed_when_before_is_not_an_ancestor(tmp_path: Path) -> None:
    # Given: two commits on diverged branches, as produced by a force push.
    git(tmp_path, "init")
    git(tmp_path, "config", "user.name", "CI Test")
    git(tmp_path, "config", "user.email", "ci@example.invalid")
    common = commit_file(tmp_path, "base.txt", "base\n")
    before = commit_file(tmp_path, "old.txt", "old history\n")
    git(tmp_path, "checkout", "--detach", common)
    after = commit_file(tmp_path, "new.txt", "replacement history\n")

    # When: the workflow range wrapper evaluates the force-pushed range.
    result = run_push_range(tmp_path, before, after)

    # Then: it refuses the unsafe range so the workflow selects the full matrix.
    assert result.returncode != 0
