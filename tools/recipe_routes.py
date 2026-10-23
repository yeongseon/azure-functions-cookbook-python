"""AST-only HTTP declaration extraction; example modules are never imported."""

from __future__ import annotations

import ast
from dataclasses import dataclass
from pathlib import Path

from tools.recipe_auth import auth_value, constructor_auth, module_bindings, module_nodes
from tools.recipe_inspection import unreviewed_gaps


@dataclass(frozen=True, slots=True)
class Route:
    file: str
    handler: str
    auth: str


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
                    if key[0] not in bindings or bindings[key[0]][1].get(key[1]) != "BLUEPRINT":
                        result.append(
                            Route(
                                path.relative_to(root).as_posix(),
                                "unresolved-registration",
                                "UNKNOWN",
                            )
                        )
                    else:
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
                adapter_auth = constructor_auth(node.value, names)
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
                if any(isinstance(argument, ast.Starred) for argument in decorator.args) or any(
                    keyword.arg is None for keyword in decorator.keywords
                ):
                    auth = "UNKNOWN"
                result.append(Route(path.relative_to(root).as_posix(), handler.name, auth))
        if any(defaults.get(name) == "UNKNOWN" for name in ("app", "api", "bp", "*import*")):
            result.append(
                Route(path.relative_to(root).as_posix(), "unresolved-application", "UNKNOWN")
            )
        for node in tree.body:
            if isinstance(node, (ast.If, ast.For, ast.While, ast.Try)):
                if (
                    isinstance(node, ast.If)
                    and isinstance(node.test, ast.Name)
                    and names.get(node.test.id) in {"True", "False"}
                ):
                    continue
                if any(
                    isinstance(child, ast.Attribute)
                    and child.attr in {"route", "register_functions"}
                    for child in ast.walk(node)
                ):
                    result.append(
                        Route(path.relative_to(root).as_posix(), "dynamic-registration", "UNKNOWN")
                    )
    if not result:
        constructors = any(defaults for _, defaults in bindings.values())
        event_triggers = any(
            isinstance(node, ast.Attribute)
            and node.attr.endswith("_trigger")
            and node.attr != "http_trigger"
            or isinstance(node, ast.Attribute)
            and node.attr == "schedule"
            for tree in modules.values()
            for node in ast.walk(tree)
        )
        if constructors and not event_triggers:
            result.append(
                Route(files[0].relative_to(root).as_posix(), "unresolved-surface", "UNKNOWN")
            )
    result.extend(
        Route(gap.file, f"incomplete-inspection:{gap.line}:{gap.rule}", "UNKNOWN")
        for gap in unreviewed_gaps(project, root)
    )
    return tuple(sorted(set(result), key=lambda route: (route.file, route.handler)))
