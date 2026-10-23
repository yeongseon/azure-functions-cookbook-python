from __future__ import annotations

from importlib.util import find_spec
import os
from pathlib import Path
import shutil
import subprocess
import sys


def doctor() -> int:
    missing = sys.version_info < (3, 11)
    print(f"python >=3.11: {'MISSING' if missing else sys.version.split()[0]} (required)")
    managed = sys.prefix != sys.base_prefix or bool(shutil.which("hatch"))
    print(f"hatch or venv: {'available' if managed else 'MISSING'} (required)")
    missing |= not managed
    for tool in ("ruff", "mypy", "pytest", "bandit"):
        present = bool(find_spec(tool)) and bool(shutil.which(tool))
        print(f"{tool}: {'available' if present else 'MISSING'} (required for check/test)")
        missing |= not present
    for tool, lanes in (
        ("func", "integration/verify"),
        ("azurite", "integration/verify"),
        ("uv", "recipe-tests/verify"),
        ("git", "worker-registration/verify"),
    ):
        print(f"{tool}: {'available' if shutil.which(tool) else 'MISSING'} (required for {lanes})")
    print(f"bicep: {'available' if bicep_command() else 'MISSING'} (required for bicep/verify)")
    print("doctor: " + ("INCOMPLETE" if missing else "PASS"))
    if missing:
        print("development environment not created: run make install")
    return 2 if missing else 0


def bicep_command() -> list[str]:
    explicit = os.environ.get("BICEP_CLI") or shutil.which("bicep")
    if explicit:
        return [explicit]
    installed = Path.home() / ".azure/bin/bicep"
    return [str(installed)] if installed.is_file() and os.access(installed, os.X_OK) else []


def clean(root: Path) -> None:
    result = subprocess.run(
        ["git", "-C", str(root), "ls-files", "-z"],
        capture_output=True,
        text=True,
        check=True,
    )
    tracked = set(result.stdout.split("\0"))
    candidates = [
        root / name
        for name in (
            "test-results",
            "dist",
            "build",
            "site",
            "htmlcov",
            "coverage.xml",
            ".coverage",
            ".pytest_cache",
            ".mypy_cache",
            ".ruff_cache",
        )
    ]
    candidates.extend(root.glob("*.egg-info"))
    candidates.extend(root.rglob("__pycache__"))
    for candidate in candidates:
        if candidate.is_symlink():
            continue
        if any(
            part in {".git", ".venv", "venv", "env"} for part in candidate.relative_to(root).parts
        ):
            continue
        files = list(candidate.rglob("*")) if candidate.is_dir() else [candidate]
        for path in files:
            if path.is_file() and path.relative_to(root).as_posix() not in tracked:
                path.unlink()
        if candidate.is_dir():
            for path in sorted(candidate.rglob("*"), reverse=True):
                if not path.is_symlink() and path.is_dir() and not any(path.iterdir()):
                    path.rmdir()
            if not any(candidate.iterdir()):
                candidate.rmdir()
