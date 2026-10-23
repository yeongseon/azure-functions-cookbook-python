"""Conservative inspection boundaries, never execution of recipe source."""

from __future__ import annotations

import ast
from dataclasses import dataclass
import hashlib
from pathlib import Path
import sys

from tools.recipe_auth import module_bindings, symbol
from tools.recipe_discovery import recipe_files


def construct_digest(node: ast.AST) -> str:
    def normalized(value: ast.AST | list[ast.AST] | str | int | float | bool | None) -> str:
        if isinstance(value, ast.AST):
            fields = ", ".join(
                f"{name}={normalized(child)}"
                for name, child in ast.iter_fields(value)
                if child is not None
            )
            return f"{type(value).__name__}({fields})"
        if isinstance(value, list):
            return "[" + ", ".join(normalized(child) for child in value) + "]"
        return repr(value)

    return hashlib.sha256(normalized(node).encode()).hexdigest()


@dataclass(frozen=True, slots=True)
class InspectionGap:
    file: str
    line: int
    rule: str
    digest: str


def source_modules(project: Path) -> dict[Path, ast.Module]:
    return {
        path: ast.parse(path.read_text())
        for path in recipe_files(project, "*.py")
        if not any(
            part.startswith(".") or part in {"tests", "__pycache__"}
            for part in path.relative_to(project).parts
        )
    }


def app_names(tree: ast.Module) -> set[str]:
    names = {"app", "api", "bp"}
    bindings, _ = module_bindings(tree)
    for node in ast.walk(tree):
        if isinstance(node, ast.Name) and "blueprint" in node.id.lower():
            names.add(node.id)
        if isinstance(node, (ast.Assign, ast.AnnAssign)) and isinstance(node.value, ast.Call):
            if symbol(node.value.func, bindings).rsplit(".", 1)[-1] in {
                "FunctionApp",
                "Blueprint",
                "DFApp",
                "LangGraphApp",
            }:
                targets = node.targets if isinstance(node, ast.Assign) else [node.target]
                names.update(target.id for target in targets if isinstance(target, ast.Name))
    return names


def mentions_app(node: ast.AST, names: set[str]) -> bool:
    return any(isinstance(child, ast.Name) and child.id in names for child in ast.walk(node))


def registration_method(name: str) -> bool:
    return (
        name in {"route", "schedule", "function_name", "register_functions", "register_blueprint"}
        or name.endswith("_trigger")
        or name.startswith(("service_bus_", "event_hub_", "cosmos_db_", "durable_"))
    )


def expanded_arguments(call: ast.Call) -> bool:
    return any(isinstance(argument, ast.Starred) for argument in call.args) or any(
        keyword.arg is None for keyword in call.keywords
    )


def inspection_gaps(project: Path, root: Path) -> tuple[InspectionGap, ...]:
    gaps: set[InspectionGap] = set()
    for path, tree in source_modules(project).items():
        names = app_names(tree)
        bindings, _ = module_bindings(tree)
        for node in ast.walk(tree):
            if (
                isinstance(node, ast.Assign)
                and isinstance(node.value, ast.Name)
                and node.value.id in names
            ):
                names.update(target.id for target in node.targets if isinstance(target, ast.Name))
        parents = {
            child: parent for parent in ast.walk(tree) for child in ast.iter_child_nodes(parent)
        }

        def record(node: ast.AST, rule: str) -> None:
            digest = construct_digest(node)
            gaps.add(
                InspectionGap(
                    path.relative_to(root).as_posix(),
                    node.lineno if isinstance(node, (ast.expr, ast.stmt)) else 1,
                    rule,
                    digest,
                )
            )

        for node in ast.walk(tree):
            if (
                isinstance(node, ast.Attribute)
                and isinstance(node.ctx, ast.Load)
                and registration_method(node.attr)
                and mentions_app(node.value, names)
            ):
                parent = parents.get(node)
                if not isinstance(parent, ast.Call) or parent.func is not node:
                    record(node, "registration-method-escape")
                elif expanded_arguments(parent):
                    record(parent, "registration-argument-expansion")
            if isinstance(node, ast.ImportFrom) and any(alias.name == "*" for alias in node.names):
                if (node.module or "").split(".")[0] not in sys.stdlib_module_names:
                    record(node, "star-import")
            if isinstance(node, ast.Attribute) and isinstance(node.ctx, (ast.Store, ast.Del)):
                if (
                    mentions_app(node.value, names)
                    and (node.attr.startswith("_") or "auth_level" in node.attr.lower())
                    and node.attr != "http_auth_level"
                ):
                    record(node, "app-attribute-mutation")
            if not isinstance(node, ast.Call):
                continue
            callable_name = symbol(node.func, bindings)
            leaf = callable_name.rsplit(".", 1)[-1]
            if leaf in {"FunctionApp", "DFApp", "Blueprint", "LangGraphApp"} and expanded_arguments(
                node
            ):
                record(node, "constructor-argument-expansion")
            if callable_name in {
                "exec",
                "eval",
                "compile",
                "__import__",
            } or callable_name.startswith(("importlib.", "runpy.")):
                record(node, "dynamic-execution")
            if leaf in {"globals", "locals", "vars"}:
                record(node, "namespace-reflection")
            if (
                leaf in {"getattr", "setattr", "delattr"}
                and node.args
                and mentions_app(node.args[0], names)
            ):
                record(node, "app-reflection")
            if isinstance(node.func, ast.Call) and mentions_app(node.func, names):
                record(node, "call-style-registration")
            if any(
                mentions_app(argument, names)
                for argument in [*node.args, *(keyword.value for keyword in node.keywords)]
            ):
                supported = (
                    isinstance(node.func, ast.Attribute)
                    and node.func.attr == "register_functions"
                    and mentions_app(node.func.value, names)
                )
                if not supported:
                    record(node, "app-escape")
            if isinstance(node.func, ast.Attribute) and registration_method(node.func.attr):
                ancestor = parents.get(node)
                while ancestor is not None:
                    if isinstance(ancestor, ast.ClassDef):
                        record(node, "class-registration")
                        break
                    if isinstance(ancestor, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        if node not in ancestor.decorator_list:
                            record(node, "nested-registration")
                            break
                    ancestor = parents.get(ancestor)
    return tuple(sorted(gaps, key=lambda gap: (gap.file, gap.line, gap.rule)))


def unreviewed_gaps(project: Path, root: Path) -> tuple[InspectionGap, ...]:
    import json

    manifest = root / "security/recipe-security-manifest.json"
    reviews = (
        json.loads(manifest.read_text()).get("inspection_reviews", []) if manifest.exists() else []
    )
    return tuple(
        gap
        for gap in inspection_gaps(project, root)
        if not any(
            review.get("file") == gap.file
            and review.get("line") == gap.line
            and review.get("rule") == gap.rule
            and review.get("digest") == gap.digest
            and isinstance(review.get("reason"), str)
            and review["reason"].strip()
            and isinstance(review.get("owner"), str)
            and review["owner"].strip()
            for review in reviews
        )
    )
