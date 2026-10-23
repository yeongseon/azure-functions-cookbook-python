"""Shared recipe-source discovery excludes generated environments and caches."""

import os
from pathlib import Path

IGNORED = frozenset(
    {".venv", "venv", "env", "__pycache__", "site-packages", "node_modules", ".git"}
)


def recipe_files(root: Path, pattern: str) -> tuple[Path, ...]:
    paths: list[Path] = []
    for directory, children, files in os.walk(root, followlinks=False):
        children[:] = [
            child for child in children if child not in IGNORED and not child.startswith(".")
        ]
        for name in files:
            path = Path(directory) / name
            if path.match(pattern):
                paths.append(path)
    return tuple(sorted(paths))
