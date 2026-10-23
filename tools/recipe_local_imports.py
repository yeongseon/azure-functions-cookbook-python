"""Resolve recipe-local imports without importing or executing Python modules."""

from __future__ import annotations

import ast
from pathlib import Path


def import_candidates(
    path: Path, node: ast.Import | ast.ImportFrom, project: Path
) -> tuple[Path, ...]:
    base = project
    if isinstance(node, ast.ImportFrom) and node.level:
        base = path.parent
        for _ in range(node.level - 1):
            base = base.parent
    names = (
        [alias.name for alias in node.names]
        if isinstance(node, ast.Import)
        else [node.module or ""]
    )
    candidates: list[Path] = []
    for name in names:
        target = base.joinpath(*name.split(".")) if name else base
        candidates.extend([target.with_suffix(".py"), target / "__init__.py"])
        if isinstance(node, ast.ImportFrom):
            candidates.extend(target / (alias.name + ".py") for alias in node.names)
    return tuple(candidate.resolve() for candidate in candidates if candidate.is_file())


def outside_import(
    node: ast.Import | ast.ImportFrom, path: Path, project: Path, root: Path
) -> bool:
    if any(
        not candidate.is_relative_to(project.resolve())
        for candidate in import_candidates(path, node, project)
    ):
        return True
    names = (
        [alias.name for alias in node.names]
        if isinstance(node, ast.Import)
        else [node.module or ""]
    )
    for name in names:
        for base in (root, root / "src"):
            target = base.joinpath(*name.split("."))
            for candidate in (target.with_suffix(".py"), target / "__init__.py"):
                if candidate.is_file() and not candidate.resolve().is_relative_to(
                    project.resolve()
                ):
                    return True
    return False


def reachable_modules(project: Path) -> dict[Path, ast.Module]:
    pending = [project / "function_app.py"]
    modules: dict[Path, ast.Module] = {}
    while pending:
        path = pending.pop().resolve()
        if path in modules or not path.is_relative_to(project.resolve()):
            continue
        tree = ast.parse(path.read_text())
        modules[path] = tree
        for node in ast.walk(tree):
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                pending.extend(import_candidates(path, node, project))
    return modules
