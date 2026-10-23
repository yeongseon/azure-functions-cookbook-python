"""Resolve the supported static SDK constructor and auth expression subset."""

from __future__ import annotations

import ast

from tools.recipe_binding_order import expression_is_stable, unstable_names


def symbol(node: ast.expr, names: dict[str, str]) -> str:
    match node:
        case ast.Name(id=name):
            return names.get(name, name)
        case ast.Call(func=ast.Name(id="cast"), args=[_, value]):
            return symbol(value, names)
        case ast.Call(
            func=ast.Name(id="getattr"), args=[value, ast.Constant(value=str(attribute))]
        ):
            return symbol(value, names) + "." + attribute
        case ast.Attribute(value=value, attr=attribute):
            return symbol(value, names) + "." + attribute
        case _:
            return "UNKNOWN"


def auth_value(node: ast.expr, names: dict[str, str]) -> str:
    match node:
        case ast.Constant(value=str(value)):
            return (
                value.upper() if value.upper() in {"ANONYMOUS", "FUNCTION", "ADMIN"} else "UNKNOWN"
            )
        case ast.IfExp(test=test, body=body, orelse=otherwise):
            if isinstance(test, ast.Constant) and isinstance(test.value, bool):
                return auth_value(body if test.value else otherwise, names)
            if isinstance(test, ast.Name) and names.get(test.id) == "PUBLIC_DEMO_OPT_IN":
                return auth_value(otherwise, names)
            return "UNKNOWN"
        case _:
            value = symbol(node, names)
            for level in ("ANONYMOUS", "FUNCTION", "ADMIN"):
                if value == level or value in {
                    f"func.AuthLevel.{level}",
                    f"azure.functions.AuthLevel.{level}",
                    f"AuthLevel.{level}",
                }:
                    return level
            return "UNKNOWN"


def constructor_auth(call: ast.Call, names: dict[str, str]) -> str:
    resolved_constructor = symbol(call.func, names)
    constructor = resolved_constructor.rsplit(".", 1)[-1]
    if any(isinstance(argument, ast.Starred) for argument in call.args):
        return "UNKNOWN"
    if any(keyword.arg is None for keyword in call.keywords):
        return "UNKNOWN"
    if constructor not in {"FunctionApp", "DFApp", "LangGraphApp"}:
        return "UNKNOWN"
    if constructor != "LangGraphApp" and resolved_constructor not in {
        "func.FunctionApp",
        "azure.functions.FunctionApp",
        "df.DFApp",
        "azure.durable_functions.DFApp",
    }:
        return "UNKNOWN"
    # FunctionApp's inspected SDK signature has one positional parameter: http_auth_level.
    parameter = "auth_level" if constructor == "LangGraphApp" else "http_auth_level"
    arguments = [keyword.value for keyword in call.keywords if keyword.arg == parameter]
    if len(call.args) > 1 or (call.args and arguments):
        return "UNKNOWN"
    if any(keyword.arg != parameter for keyword in call.keywords) and constructor != "LangGraphApp":
        return "UNKNOWN"
    if call.args:
        return auth_value(call.args[0], names)
    return auth_value(arguments[0], names) if arguments else "FUNCTION"


def module_bindings(
    tree: ast.Module, before: int | None = None, reviewed: frozenset[str] = frozenset()
) -> tuple[dict[str, str], dict[str, str]]:
    names: dict[str, str] = {}
    defaults: dict[str, str] = {}
    invalid = unstable_names(tree) - reviewed
    for node in tree.body:
        if before is not None and node.lineno >= before:
            break
        match node:
            case ast.Import(names=imports):
                for alias in imports:
                    names[alias.asname or alias.name.split(".")[0]] = (
                        alias.name if alias.asname else alias.name.split(".")[0]
                    )
            case ast.ImportFrom(module=module, names=imports):
                for alias in imports:
                    if alias.name == "*":
                        names = dict.fromkeys(names, "UNKNOWN")
                        defaults = dict.fromkeys(defaults, "UNKNOWN")
                        defaults["*import*"] = "UNKNOWN"
                    else:
                        names[alias.asname or alias.name] = f"{module}.{alias.name}"
            case ast.Assign() | ast.AnnAssign():
                value = node.value
                targets = node.targets if isinstance(node, ast.Assign) else [node.target]
                for target in targets:
                    if not isinstance(target, ast.Name) or value is None:
                        continue
                    if target.id in defaults:
                        defaults[target.id] = "UNKNOWN"
                    names[target.id] = symbol(value, names)
                    resolved = auth_value(value, names)
                    if resolved != "UNKNOWN":
                        names[target.id] = resolved
                    if isinstance(value, ast.Constant) and isinstance(value.value, bool):
                        names[target.id] = str(value.value)
                    if ast.unparse(value) in {
                        "os.getenv('COOKBOOK_PUBLIC_DEMO', '') == 'true'",
                    }:
                        names[target.id] = "PUBLIC_DEMO_OPT_IN"
                    if target.id == "AUTH_LEVEL_ANONYMOUS":
                        names[target.id] = "ANONYMOUS"
                    if isinstance(value, ast.Call):
                        defaults[target.id] = constructor_auth(value, names)
                        if (
                            symbol(value.func, names).endswith("Blueprint")
                            and not value.args
                            and not value.keywords
                        ):
                            defaults[target.id] = "BLUEPRINT"
                    elif (
                        isinstance(value, ast.Attribute)
                        and value.attr == "function_app"
                        and isinstance(value.value, ast.Name)
                    ):
                        defaults[target.id] = defaults.get(value.value.id, "UNKNOWN")
                    relevant = value
                    if isinstance(value, ast.Call):
                        auth_arguments = [
                            keyword.value
                            for keyword in value.keywords
                            if keyword.arg in {"auth_level", "http_auth_level"}
                        ]
                        relevant = (
                            auth_arguments[0]
                            if auth_arguments
                            else (value.args[0] if value.args else value.func)
                        )
                    if target.id in invalid or not expression_is_stable(relevant, invalid):
                        names[target.id] = "UNKNOWN"
                        if target.id in defaults:
                            defaults[target.id] = "UNKNOWN"
            case ast.FunctionDef() | ast.AsyncFunctionDef() | ast.ClassDef():
                continue
            case _:
                for child in module_nodes(node):
                    if isinstance(child, ast.Name) and isinstance(child.ctx, ast.Store):
                        names[child.id] = defaults[child.id] = "UNKNOWN"
                if isinstance(node, ast.Try) and any(
                    isinstance(child, ast.Call)
                    and isinstance(child.func, ast.Attribute)
                    and child.func.attr == "import_module"
                    and child.args
                    and isinstance(child.args[0], ast.Constant)
                    and child.args[0].value == "azure.functions"
                    for child in ast.walk(node)
                ):
                    names["func"] = "azure.functions"
                if isinstance(node, ast.Try):
                    for child in ast.walk(node):
                        if isinstance(child, ast.Import):
                            for alias in child.names:
                                if alias.name in {"azure.functions", "azure.durable_functions"}:
                                    names[alias.asname or alias.name] = alias.name
                        if (
                            isinstance(child, ast.Call)
                            and isinstance(child.func, ast.Name)
                            and child.func.id == "import_module"
                            and child.args
                            and isinstance(child.args[0], ast.Constant)
                            and child.args[0].value == "azure.functions"
                        ):
                            names["_func_module"] = "azure.functions"
    for name in invalid.intersection(names):
        names[name] = "UNKNOWN"
        if name in defaults:
            defaults[name] = "UNKNOWN"
    return names, defaults


def module_nodes(tree: ast.AST) -> list[ast.AST]:
    nodes: list[ast.AST] = []
    for node in ast.iter_child_nodes(tree):
        nodes.append(node)
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            nodes.extend(module_nodes(node))
    return nodes
