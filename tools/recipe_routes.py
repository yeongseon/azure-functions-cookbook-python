"""AST-only HTTP declaration extraction; example modules are never imported."""

from __future__ import annotations

import ast
from dataclasses import dataclass
from pathlib import Path

from tools.paid_recipe_canonical import canonical_gaps
from tools.recipe_auth import auth_value, constructor_auth, module_bindings, module_nodes
from tools.recipe_binding_order import unstable_names
from tools.recipe_binding_reviews import reviewed_bindings
from tools.recipe_inspection import unreviewed_gaps
from tools.recipe_local_imports import exported_binding, import_candidates, reachable_modules


@dataclass(frozen=True, slots=True)
class Route:
    file: str
    handler: str
    auth: str


def routes(project: Path, root: Path) -> tuple[Route, ...]:
    import json

    from tools.recipe_startup import startup_gaps

    manifest_path = root / "security/recipe-security-manifest.json"
    manifest = json.loads(manifest_path.read_text()) if manifest_path.exists() else {}
    classification = manifest.get("recipes", {}).get(project.relative_to(root).as_posix(), {})
    paid = classification.get("category") == "paid-backend" or project.name in {
        "openai_direct_chat",
        "ai_image_generation",
        "streaming_ai_response",
    }
    result: list[Route] = []
    from tools.recipe_discovery import recipe_files

    files = [project / "function_app.py", *recipe_files(project / "app", "*.py")]
    if paid:
        files = list(reachable_modules(project))
    modules = {path: ast.parse(path.read_text()) for path in files}
    reviews = {path: reviewed_bindings(path, root, tree) for path, tree in modules.items()}
    bindings = {
        path: module_bindings(tree, reviewed=reviews[path]) for path, tree in modules.items()
    }
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
                    if paid:
                        for statement in tree.body:
                            if isinstance(statement, ast.ImportFrom):
                                for alias in statement.names:
                                    if (alias.asname or alias.name) == blueprint:
                                        for candidate in reversed(
                                            import_candidates(path, statement, project)
                                        ):
                                            resolved = exported_binding(
                                                candidate, alias.name, project
                                            )
                                            if resolved is not None:
                                                key = resolved
                                                break
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
                declaration_names, _ = module_bindings(tree, node.lineno, reviews[path])
                adapter_auth = constructor_auth(node.value, declaration_names)
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
                visible_names, visible_defaults = module_bindings(
                    tree, decorator.lineno, reviews[path]
                )
                visible_defaults.update(
                    {
                        receiver: next(iter(levels)) if len(levels) == 1 else "UNKNOWN"
                        for (module, receiver), levels in inherited.items()
                        if module == path
                    }
                )
                auth = (
                    visible_defaults.get(route_receiver.id, "UNKNOWN")
                    if isinstance(route_receiver, ast.Name)
                    else "UNKNOWN"
                )
                for keyword in decorator.keywords:
                    if keyword.arg == "auth_level":
                        auth = auth_value(keyword.value, visible_names)
                if (
                    isinstance(route_receiver, ast.Name)
                    and route_receiver.id in unstable_names(tree) - reviews[path]
                ):
                    auth = "UNKNOWN"
                if any(isinstance(argument, ast.Starred) for argument in decorator.args) or any(
                    keyword.arg is None for keyword in decorator.keywords
                ):
                    auth = "UNKNOWN"
                if len(decorator.args) > 1 or (
                    decorator.args
                    and not (
                        isinstance(decorator.args[0], ast.Constant)
                        and isinstance(decorator.args[0].value, str)
                    )
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
    if paid:
        result.extend(
            Route(gap.file, f"paid-canonical:{gap.line}", "UNKNOWN")
            for gap in canonical_gaps(project, root)
        )
    result.extend(
        Route(gap.file, f"startup-inspection:{gap.line}", "UNKNOWN")
        for gap in startup_gaps(project, root)
    )
    return tuple(sorted(set(result), key=lambda route: (route.file, route.handler)))
