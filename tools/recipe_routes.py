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
    defaults: dict[str, str] = {}
    for path in files:
        tree = ast.parse(path.read_text())
        names: dict[str, str] = {}
        for node in ast.walk(tree):
            if isinstance(node, (ast.Assign, ast.AnnAssign)):
                value = node.value
                targets = node.targets if isinstance(node, ast.Assign) else [node.target]
                for target in targets:
                    if not isinstance(target, ast.Name) or value is None:
                        continue
                    names[target.id] = auth_value(value, names)
                    if (
                        ast.unparse(value)
                        == "os.getenv('COOKBOOK_PUBLIC_DEMO', '').lower() == 'true'"
                    ):
                        names[target.id] = "PUBLIC_DEMO_OPT_IN"
                    if target.id == "AUTH_LEVEL_ANONYMOUS":
                        names[target.id] = "ANONYMOUS"
                    if isinstance(value, ast.Call):
                        for keyword in value.keywords:
                            if keyword.arg in {"http_auth_level", "auth_level"}:
                                defaults[target.id] = auth_value(keyword.value, names)
        app_default = defaults.get("app", defaults.get("LANGGRAPH_HOST", "FUNCTION"))
        for node in ast.walk(tree):
            if (
                isinstance(node, ast.Call)
                and isinstance(node.func, ast.Name)
                and node.func.id == "LangGraphApp"
            ):
                adapter_auth = "FUNCTION"
                for keyword in node.keywords:
                    if keyword.arg == "auth_level":
                        adapter_auth = auth_value(keyword.value, names)
                result.append(
                    Route(path.relative_to(root).as_posix(), "adapter-routes", adapter_auth)
                )
        for node in ast.walk(tree):
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            for decorator in node.decorator_list:
                if not (
                    isinstance(decorator, ast.Call)
                    and isinstance(decorator.func, ast.Attribute)
                    and decorator.func.attr == "route"
                ):
                    continue
                auth = app_default
                for keyword in decorator.keywords:
                    if keyword.arg == "auth_level":
                        auth = auth_value(keyword.value, names)
                result.append(Route(path.relative_to(root).as_posix(), node.name, auth))
    return tuple(sorted(set(result), key=lambda route: (route.file, route.handler)))
