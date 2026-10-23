from __future__ import annotations

import argparse
from dataclasses import replace
from pathlib import Path
import shutil
import sys
import tempfile

from tools.verification import aggregate
from tools.verification_evidence import Summary, collect, redact
from tools.verification_lanes import finish, fresh
from tools.verification_manifest import recipes
from tools.verification_process import run

REPO_ROOT = Path(__file__).resolve().parents[1]
EXAMPLES = REPO_ROOT / "examples"


def recipe_projects() -> tuple[Path, ...]:
    projects = {test.parent.parent for test in EXAMPLES.glob("*/*/tests/test_*.py")}
    return tuple(sorted(project for project in projects if (project / "pyproject.toml").exists()))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--family")
    args = parser.parse_args()
    directory = REPO_ROOT / "test-results/recipe-tests"
    fresh(directory)
    outcomes: list[Summary] = []
    inventory = recipes(REPO_ROOT)
    for family in sorted({r.family for r in inventory}):
        if args.family and args.family != family:
            continue
        selected = [p for p in recipe_projects() if p.parent.name == family]
        if not selected:
            outcomes.append(
                Summary(
                    family,
                    ("uv", "run"),
                    required=False,
                    status="NOT_APPLICABLE",
                    exit_code=0,
                    reason="No standalone pytest suites; covered by repository recipe contracts",
                )
            )
        for project in selected:
            lane = "recipe-tests/" + project.relative_to(EXAMPLES).as_posix()
            target = REPO_ROOT / "test-results" / lane
            fresh(target)
            if not shutil.which("uv"):
                outcomes.append(
                    finish(target, Summary(lane, ("uv", "run"), reason="uv is required"))
                )
                continue
            with tempfile.TemporaryDirectory(prefix="cookbook-recipe-") as temporary:
                workspace = Path(temporary) / "app"
                shutil.copytree(
                    project,
                    workspace,
                    ignore=shutil.ignore_patterns(".venv", "__pycache__", "uv.lock"),
                )
                raw = Path(temporary) / "junit.xml"
                command = [
                    "uv",
                    "run",
                    "--python",
                    sys.executable,
                    "--project",
                    str(workspace),
                    "--with",
                    "pytest",
                    "python",
                    "-m",
                    "pytest",
                    "-q",
                    "tests",
                    "--junitxml=" + str(raw),
                ]
                code = run(command, target / "logs/pytest.log", 900, cwd=workspace)
                if raw.exists():
                    (target / "junit.xml").write_text(redact(raw.read_text()))
                summary = replace(collect(target, command, code), lane=lane)
                outcomes.append(finish(target, summary))
    if not any(s.required for s in outcomes):
        outcomes.append(
            Summary("recipe-tests", ("uv", "run"), reason="No recipe test suites selected")
        )
    return aggregate("recipe-tests", outcomes).exit_code


if __name__ == "__main__":
    raise SystemExit(main())
