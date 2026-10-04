from __future__ import annotations

from pathlib import Path
import subprocess
import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
EXAMPLES = REPO_ROOT / "examples"


def recipe_projects() -> tuple[Path, ...]:
    projects = {test.parent.parent for test in EXAMPLES.glob("*/*/tests/test_*.py")}
    return tuple(sorted(project for project in projects if (project / "pyproject.toml").exists()))


def main() -> int:
    failures: list[str] = []
    for project in recipe_projects():
        result = subprocess.run(
            [
                "uv",
                "run",
                "--project",
                str(project),
                "--with",
                "pytest",
                "python",
                "-m",
                "pytest",
                "-q",
                "tests",
            ],
            cwd=project,
            check=False,
        )
        if result.returncode != 0:
            failures.append(project.relative_to(EXAMPLES).as_posix())

    if failures:
        print("Recipe test failures:", file=sys.stderr)
        print("\n".join(failures), file=sys.stderr)
        return 1
    print(f"Recipe tests passed for {len(recipe_projects())} projects.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
