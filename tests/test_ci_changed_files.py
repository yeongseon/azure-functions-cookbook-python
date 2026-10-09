from __future__ import annotations

import os
from pathlib import Path
import subprocess

SCRIPT = Path(__file__).resolve().parents[1] / "tools" / "ci_changed_files.sh"
WORKFLOW_WRAPPER = Path(__file__).resolve().parents[1] / "tools" / "ci_classify_workflow.sh"


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


def run_workflow_wrapper_with_failing_git(tmp_path: Path, event_name: str) -> dict[str, str]:
    # Given: git fails before it can produce a changed-file list.
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    fake_git = bin_dir / "git"
    fake_git.write_text("#!/usr/bin/env bash\nexit 1\n", encoding="utf-8")
    fake_git.chmod(0o755)
    output = tmp_path / "github-output.txt"
    environment = {
        **os.environ,
        "PATH": f"{bin_dir}:{os.environ['PATH']}",
        "EVENT_NAME": event_name,
        "BASE_SHA": "base",
        "HEAD_SHA": "head",
        "BEFORE_SHA": "before",
        "SHA": "after",
        "GITHUB_OUTPUT": str(output),
    }

    # When: the same wrapper used by the changes job handles the event.
    result = subprocess.run(
        ["bash", str(WORKFLOW_WRAPPER)],
        cwd=SCRIPT.parents[1],
        env=environment,
        check=False,
        capture_output=True,
        text=True,
    )

    # Then: failure is absorbed and the prewritten full-matrix outputs remain.
    assert result.returncode == 0, result.stderr
    return dict(line.split("=", 1) for line in output.read_text(encoding="utf-8").splitlines())


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


def test_pull_request_git_failure_selects_full_matrix(tmp_path: Path) -> None:
    assert run_workflow_wrapper_with_failing_git(tmp_path, "pull_request") == {
        "docs_only": "false",
        "docs_changed": "true",
        "full_required": "true",
    }


def test_push_git_failure_selects_full_matrix(tmp_path: Path) -> None:
    assert run_workflow_wrapper_with_failing_git(tmp_path, "push") == {
        "docs_only": "false",
        "docs_changed": "true",
        "full_required": "true",
    }
