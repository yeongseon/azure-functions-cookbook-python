from __future__ import annotations

import os
from pathlib import Path
import subprocess
import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
EXAMPLES = REPO_ROOT / "examples"


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
    for project in projects:
        name = project.relative_to(EXAMPLES).as_posix()
        if not (project / "pyproject.toml").exists():
            failures.append(f"{name}: has tests but no pyproject.toml")
            continue
        result = subprocess.run(
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
            check=False,
        )
        if result.returncode != 0:
            failures.append(f"{name}: suite failed")

    if failures:
        print("Recipe test failures:", file=sys.stderr)
        print("\n".join(failures), file=sys.stderr)
        return 1
    print(f"Recipe tests passed for {len(projects)} projects.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
