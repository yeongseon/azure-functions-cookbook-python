"""AST-only HTTP declaration extraction; example modules are never imported."""

from __future__ import annotations

import ast
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class Route:
    file: str
    handler: str
    auth: str


def auth_value(node: ast.expr, names: dict[str, str]) -> str:
    if isinstance(node, ast.Attribute) and node.attr in {"ANONYMOUS", "FUNCTION", "ADMIN"}:
        return node.attr
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        value = node.value.upper()
        return value if value in {"ANONYMOUS", "FUNCTION", "ADMIN"} else "UNKNOWN"
    if isinstance(node, ast.Name):
        return names.get(node.id, "UNKNOWN")
    if isinstance(node, ast.IfExp):
        # Resolve the false branch only after checking the actual environment expression.
        if isinstance(node.test, ast.Name) and names.get(node.test.id) == "PUBLIC_DEMO_OPT_IN":
            return auth_value(node.orelse, names)
    return "UNKNOWN"


def routes(project: Path, root: Path) -> tuple[Route, ...]:
    result: list[Route] = []
    files = [project / "function_app.py", *sorted((project / "app").rglob("*.py"))]
    modules = {path: ast.parse(path.read_text()) for path in files}
    bindings = {path: module_bindings(tree) for path, tree in modules.items()}
    inherited: dict[tuple[Path, str], set[str]] = {}
    for path, tree in modules.items():
        names, defaults = bindings[path]
        imports = {
            alias.asname or alias.name: (
                project / (node.module or "").replace(".", "/")
            ).with_suffix(".py")
            for node in tree.body
            if isinstance(node, ast.ImportFrom)
            for alias in node.names
        }
        imported_names = {
            alias.asname or alias.name: alias.name
            for node in tree.body
            if isinstance(node, ast.ImportFrom)
            for alias in node.names
        }
        for node in tree.body:
            match node:
                case ast.Expr(
                    value=ast.Call(
                        func=ast.Attribute(value=ast.Name(id=receiver), attr="register_functions"),
                        args=[ast.Name(id=blueprint)],
                    )
                ):
                    key = (imports.get(blueprint, path), imported_names.get(blueprint, blueprint))
                    inherited.setdefault(key, set()).add(defaults.get(receiver, "UNKNOWN"))
    for path in files:
        tree = modules[path]
        names, defaults = bindings[path]
        for receiver, levels in (
            (receiver, levels) for (module, receiver), levels in inherited.items() if module == path
        ):
            defaults[receiver] = next(iter(levels)) if len(levels) == 1 else "UNKNOWN"
        for node in tree.body:
            if (
                isinstance(node, (ast.Assign, ast.AnnAssign))
                and isinstance(node.value, ast.Call)
                and isinstance(node.value.func, ast.Name)
                and node.value.func.id == "LangGraphApp"
            ):
                adapter_auth = "FUNCTION"
                for keyword in node.value.keywords:
                    if keyword.arg == "auth_level":
                        adapter_auth = auth_value(keyword.value, names)
                result.append(
                    Route(path.relative_to(root).as_posix(), "adapter-routes", adapter_auth)
                )
        for handler in module_nodes(tree):
            if not isinstance(handler, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            for decorator in handler.decorator_list:
                if not (
                    isinstance(decorator, ast.Call)
                    and isinstance(decorator.func, ast.Attribute)
                    and decorator.func.attr == "route"
                ):
                    continue
                route_receiver = decorator.func.value
                auth = (
                    defaults.get(route_receiver.id, "UNKNOWN")
                    if isinstance(route_receiver, ast.Name)
                    else "UNKNOWN"
                )
                for keyword in decorator.keywords:
                    if keyword.arg == "auth_level":
                        auth = auth_value(keyword.value, names)
                result.append(Route(path.relative_to(root).as_posix(), handler.name, auth))
    return tuple(sorted(set(result), key=lambda route: (route.file, route.handler)))


def module_bindings(tree: ast.Module) -> tuple[dict[str, str], dict[str, str]]:
    names: dict[str, str] = {}
    defaults: dict[str, str] = {}
    for node in tree.body:
        if isinstance(node, (ast.Assign, ast.AnnAssign)):
            value = node.value
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            for target in targets:
                if not isinstance(target, ast.Name) or value is None:
                    continue
                names[target.id] = auth_value(value, names)
                defaults[target.id] = "UNKNOWN"
                if (
                    isinstance(value, ast.Attribute)
                    and value.attr == "function_app"
                    and isinstance(value.value, ast.Name)
                ):
                    defaults[target.id] = defaults.get(value.value.id, "UNKNOWN")
                if ast.unparse(value) == "os.getenv('COOKBOOK_PUBLIC_DEMO', '').lower() == 'true'":
                    names[target.id] = "PUBLIC_DEMO_OPT_IN"
                if target.id == "AUTH_LEVEL_ANONYMOUS":
                    names[target.id] = "ANONYMOUS"
                if isinstance(value, ast.Call):
                    constructor = value.func
                    if isinstance(constructor, ast.Attribute) and constructor.attr in {
                        "FunctionApp",
                        "DFApp",
                    }:
                        defaults[target.id] = "FUNCTION"
                    for keyword in value.keywords:
                        if keyword.arg in {"http_auth_level", "auth_level"}:
                            defaults[target.id] = auth_value(keyword.value, names)
        elif not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            pending = list(ast.iter_child_nodes(node))
            while pending:
                child = pending.pop()
                if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                    continue
                if isinstance(child, ast.Name) and isinstance(child.ctx, ast.Store):
                    names[child.id] = defaults[child.id] = "UNKNOWN"
                pending.extend(ast.iter_child_nodes(child))
    return names, defaults


def module_nodes(tree: ast.AST) -> list[ast.AST]:
    nodes: list[ast.AST] = []
    for node in ast.iter_child_nodes(tree):
        nodes.append(node)
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            nodes.extend(module_nodes(node))
    return nodes
