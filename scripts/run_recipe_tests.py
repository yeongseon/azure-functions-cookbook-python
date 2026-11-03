from __future__ import annotations

import os
from pathlib import Path
import signal
import subprocess
import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
EXAMPLES = REPO_ROOT / "examples"

# Upper bound for one recipe suite (environment build plus tests); override per run with
# RECIPE_TEST_TIMEOUT_SECONDS so one hanging install or test cannot monopolize the CI job.
DEFAULT_TIMEOUT_SECONDS = 900.0


def suite_timeout() -> float:
    raw = os.environ.get("RECIPE_TEST_TIMEOUT_SECONDS")
    if raw is None:
        return DEFAULT_TIMEOUT_SECONDS
    try:
        value = float(raw)
    except ValueError:
        raise SystemExit(f"RECIPE_TEST_TIMEOUT_SECONDS must be a number, got {raw!r}") from None
    if value <= 0:
        raise SystemExit("RECIPE_TEST_TIMEOUT_SECONDS must be greater than zero")
    return value


def run_bounded(command: list[str], *, cwd: Path, env: dict[str, str], timeout: float) -> int | None:
    """Run ``command`` in its own process group; return its exit code, or ``None`` on timeout.

    On timeout the whole group (uv plus its pytest and any grandchildren) is killed so nothing
    keeps holding ports or files after the suite is reported as failed.
    """
    with subprocess.Popen(command, cwd=cwd, env=env, start_new_session=True) as process:
        try:
            return process.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            process.wait()
            return None


def recipe_projects() -> tuple[Path, ...]:
    """Every recipe that ships a local ``tests/test_*.py`` suite."""
    return tuple(sorted({test.parent.parent for test in EXAMPLES.glob("*/*/tests/test_*.py")}))


def main() -> int:
    projects = recipe_projects()
    failures: list[str] = []
    if not projects:
        failures.append("no recipe test suites found under examples/")

    # The repository plugin fails a suite that skips any test (pytest itself exits 5 when a
    # suite selects nothing); PYTHONPATH makes it importable inside uv's isolated environment.
    pythonpath = os.pathsep.join(filter(None, [str(REPO_ROOT), os.environ.get("PYTHONPATH")]))
    timeout = suite_timeout()
    for project in projects:
        name = project.relative_to(EXAMPLES).as_posix()
        if not (project / "pyproject.toml").exists():
            failures.append(f"{name}: has tests but no pyproject.toml")
            continue
        returncode = run_bounded(
            [
                "uv",
                "run",
                "--isolated",
                "--python",
                sys.executable,
                "--project",
                str(project),
                "--with",
                "pytest",
                "python",
                "-m",
                "pytest",
                "-q",
                "-p",
                "no:cacheprovider",
                "-p",
                "tools.pytest_fail_on_skip",
                "tests",
            ],
            cwd=project,
            env={**os.environ, "PYTHONPATH": pythonpath},
            timeout=timeout,
        )
        if returncode is None:
            failures.append(f"{name}: suite timed out after {timeout:g}s")
        elif returncode != 0:
            failures.append(f"{name}: suite failed")

    if failures:
        print("Recipe test failures:", file=sys.stderr)
        print("\n".join(failures), file=sys.stderr)
        return 1
    print(f"Recipe tests passed for {len(projects)} projects.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
