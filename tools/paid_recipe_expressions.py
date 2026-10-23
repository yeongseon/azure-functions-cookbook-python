"""Allowed expression grammar for canonical paid-recipe declarations."""

import ast


def literal_value(node: ast.expr, constants: set[str]) -> bool:
    match node:
        case ast.Constant():
            return True
        case ast.Name(id=name):
            return name in constants
        case ast.List(elts=values) | ast.Tuple(elts=values) | ast.Set(elts=values):
            return all(literal_value(value, constants) for value in values)
        case ast.Dict(keys=keys, values=values):
            return all(key is not None and literal_value(key, constants) for key in keys) and all(
                literal_value(value, constants) for value in values
            )
        case ast.Attribute(
            value=ast.Attribute(value=ast.Name(id="func"), attr="AuthLevel"), attr=level
        ):
            return level in {"FUNCTION", "ADMIN", "ANONYMOUS"}
        case _:
            return False


def safe_body(node: ast.AST) -> bool:
    for child in ast.walk(node):
        if isinstance(child, ast.Name) and child.id in {
            "app",
            "bp",
            "globals",
            "locals",
            "vars",
            "exec",
            "eval",
            "compile",
            "__import__",
            "importlib",
            "runpy",
        }:
            return False
        if (
            isinstance(child, ast.Attribute)
            and isinstance(child.value, ast.Name)
            and child.value.id == "func"
            and child.attr in {"FunctionApp", "Blueprint"}
        ):
            return False
        if isinstance(child, (ast.Import, ast.ImportFrom, ast.Global, ast.Nonlocal)):
            return False
    return True


def annotation_allowed(node: ast.expr | None) -> bool:
    return node is None or all(
        isinstance(
            child,
            (
                ast.Name,
                ast.Attribute,
                ast.Subscript,
                ast.Tuple,
                ast.Constant,
                ast.BinOp,
                ast.BitOr,
                ast.Load,
            ),
        )
        for child in ast.walk(node)
    )


def decorator_allowed(node: ast.expr, constants: set[str], models: set[str]) -> bool:
    if isinstance(node, ast.Name):
        return node.id == "with_context"
    if not isinstance(node, ast.Call) or any(keyword.arg is None for keyword in node.keywords):
        return False
    if (
        isinstance(node.func, ast.Attribute)
        and isinstance(node.func.value, ast.Name)
        and node.func.value.id in {"app", "bp"}
    ):
        if node.func.attr not in {
            "route",
            "schedule",
            "function_name",
        } and not node.func.attr.endswith("_trigger"):
            return False
        if node.args and not (
            node.func.attr == "route"
            and len(node.args) == 1
            and isinstance(node.args[0], ast.Constant)
            and isinstance(node.args[0].value, str)
        ):
            return False
        return all(
            literal_value(keyword.value, constants)
            and (
                keyword.arg != "auth_level"
                or ast.unparse(keyword.value)
                in {"func.AuthLevel.FUNCTION", "func.AuthLevel.ADMIN", "'function'", "'admin'"}
            )
            for keyword in node.keywords
        )
    if (
        isinstance(node.func, ast.Name)
        and node.func.id in {"openapi", "validate_http"}
        and not node.args
    ):
        return all(literal_value(keyword.value, constants | models) for keyword in node.keywords)
    return False
