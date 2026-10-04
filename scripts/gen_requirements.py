from __future__ import annotations

import argparse
from pathlib import Path
import sys

import tomli

REPO_ROOT = Path(__file__).resolve().parents[1]
EXAMPLES = REPO_ROOT / "examples"


def render(pyproject: Path) -> str:
    metadata = tomli.loads(pyproject.read_text())
    dependencies = metadata["project"]["dependencies"]
    return "".join(f"{dependency}\n" for dependency in sorted(dependencies, key=str.casefold))


def recipe_projects() -> tuple[Path, ...]:
    return tuple(sorted(path.parent for path in EXAMPLES.glob("**/function_app.py")))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Generate recipe requirements.txt files from pyproject.toml dependencies."
    )
    parser.add_argument("--check", action="store_true", help="Fail if requirements files are stale")
    args = parser.parse_args(argv)

    stale: list[Path] = []
    for project in recipe_projects():
        requirements = project / "requirements.txt"
        generated = render(project / "pyproject.toml")
        current = requirements.read_text() if requirements.exists() else ""
        if current == generated:
            continue
        if args.check:
            stale.append(project.relative_to(REPO_ROOT))
        else:
            requirements.write_text(generated)

    if stale:
        print(
            "Recipe requirements are stale. Run: python scripts/gen_requirements.py",
            file=sys.stderr,
        )
        for project in stale:
            print(project, file=sys.stderr)
        return 1
    if args.check:
        print("Recipe requirements are up to date.")
    else:
        print("Updated recipe requirements files.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
