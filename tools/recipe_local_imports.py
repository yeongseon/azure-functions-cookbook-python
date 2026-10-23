"""Resolve Python's recipe-local import execution closure without executing source."""

from __future__ import annotations

import ast
from dataclasses import dataclass
from pathlib import Path


def opaque_candidate(target: Path) -> bool:
    names = (target, target / "__init__")
    for stem in names:
        if not stem.parent.is_dir():
            continue
        for path in stem.parent.glob(stem.name + ".*"):
            if path.is_file() and path.suffix.lower() in {
                ".pyc",
                ".pyo",
                ".so",
                ".pyd",
                ".zip",
                ".egg",
            }:
                return True
    return False


@dataclass(frozen=True, slots=True)
class Resolution:
    files: tuple[Path, ...]
    unresolved: bool = False


def module_path(target: Path, project: Path) -> Resolution:
    files: list[Path] = []
    module = target.with_suffix(".py")
    package = target / "__init__.py"
    if opaque_candidate(target):
        return Resolution((), True)
    if module.is_file() and package.is_file():
        return Resolution((), True)
    selected = package if package.is_file() else module
    if not selected.is_file() and not target.is_dir():
        return Resolution((), True)
    if selected.is_file() and not selected.resolve().is_relative_to(project.resolve()):
        return Resolution((), True)
    if not target.resolve().is_relative_to(project.resolve()):
        return Resolution((), True)
    ancestors = list(target.relative_to(project).parts)
    for length in range(1, len(ancestors)):
        parent = project.joinpath(*ancestors[:length])
        if not parent.is_dir() or parent.with_suffix(".py").is_file() or opaque_candidate(parent):
            return Resolution((), True)
        initializer = parent / "__init__.py"
        if initializer.is_file():
            if not initializer.resolve().is_relative_to(project.resolve()):
                return Resolution((), True)
            files.append(initializer.resolve())
    if selected.is_file():
        files.append(selected.resolve())
    return Resolution(tuple(files))


def declared_name(files: tuple[Path, ...], name: str) -> bool:
    if not files:
        return False
    tree = ast.parse(files[-1].read_text())
    return any(
        isinstance(node, ast.Name)
        and isinstance(node.ctx, ast.Store)
        and node.id == name
        or isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
        and node.name == name
        or isinstance(node, (ast.Import, ast.ImportFrom))
        and any((alias.asname or alias.name.split(".")[0]) == name for alias in node.names)
        for node in ast.walk(tree)
    )


def resolve_import(path: Path, node: ast.Import | ast.ImportFrom, project: Path) -> Resolution:
    project = project.resolve()
    base = project
    relative = isinstance(node, ast.ImportFrom) and bool(node.level)
    if relative and isinstance(node, ast.ImportFrom):
        if path.resolve() == project / "function_app.py":
            return Resolution((), True)
        base = path.resolve().parent
        for _ in range(node.level - 1):
            base = base.parent
        if not base.is_relative_to(project):
            return Resolution((), True)
    names = (
        [alias.name for alias in node.names]
        if isinstance(node, ast.Import)
        else [node.module or ""]
    )
    files: list[Path] = []
    unresolved = False
    for name in names:
        parts = name.split(".") if name else []
        target = base.joinpath(*parts)
        local = (
            relative
            or not parts
            or (base / parts[0]).exists()
            or (base / (parts[0] + ".py")).exists()
            or opaque_candidate(base / parts[0])
        )
        if not local:
            continue
        resolution = module_path(target, project) if parts or base != project else Resolution(())
        files.extend(resolution.files)
        unresolved |= resolution.unresolved
        if isinstance(node, ast.ImportFrom):
            # Importing from a package first executes that package, even for ``from . import x``.
            if not parts and base != project:
                initializer = base / "__init__.py"
                if initializer.is_file():
                    files.extend(module_path(base, project).files)
            for alias in node.names:
                if alias.name == "*":
                    unresolved = True
                    continue
                child = target / alias.name
                if child.with_suffix(".py").is_file() or child.is_dir() or opaque_candidate(child):
                    child_resolution = module_path(child, project)
                    files.extend(child_resolution.files)
                    unresolved |= child_resolution.unresolved
                elif not declared_name(resolution.files or tuple(files), alias.name):
                    unresolved = True
    return Resolution(tuple(dict.fromkeys(files)), unresolved)


def import_candidates(
    path: Path, node: ast.Import | ast.ImportFrom, project: Path
) -> tuple[Path, ...]:
    return resolve_import(path, node, project).files


def exported_binding(
    path: Path, name: str, project: Path, seen: frozenset[tuple[Path, str]] = frozenset()
) -> tuple[Path, str] | None:
    key = (path, name)
    if key in seen:
        return None
    tree = ast.parse(path.read_text())
    for statement in tree.body:
        if isinstance(statement, (ast.Assign, ast.AnnAssign)):
            targets = statement.targets if isinstance(statement, ast.Assign) else [statement.target]
            if any(isinstance(target, ast.Name) and target.id == name for target in targets):
                return key
        if isinstance(statement, ast.ImportFrom):
            for alias in statement.names:
                if (alias.asname or alias.name) == name:
                    for candidate in reversed(import_candidates(path, statement, project)):
                        resolved = exported_binding(candidate, alias.name, project, seen | {key})
                        if resolved is not None:
                            return resolved
    return None


def outside_import(
    node: ast.Import | ast.ImportFrom, path: Path, project: Path, root: Path
) -> bool:
    if resolve_import(path, node, project).unresolved:
        return True
    if isinstance(node, ast.ImportFrom) and node.level:
        return False
    names = (
        [alias.name for alias in node.names]
        if isinstance(node, ast.Import)
        else [node.module or ""]
    )
    for name in names:
        for base in (root, root / "src"):
            target = base.joinpath(*name.split("."))
            if any(
                candidate.exists() and not candidate.resolve().is_relative_to(project.resolve())
                for candidate in (target.with_suffix(".py"), target)
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
