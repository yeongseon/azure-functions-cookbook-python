"""Paid recipes require an explicit supported grammar, not absence of known hazards."""

from __future__ import annotations

import ast
from pathlib import Path

from tools.paid_recipe_expressions import (
    annotation_allowed,
    decorator_allowed,
    literal_value,
    safe_body,
)
from tools.recipe_auth import auth_value, module_bindings
from tools.recipe_binding_order import unstable_names
from tools.recipe_inspection import InspectionGap, construct_digest
from tools.recipe_local_imports import outside_import, reachable_modules

OPT_IN = "os.getenv('COOKBOOK_PUBLIC_DEMO', '') == 'true'"
APP_AUTH = "func.AuthLevel.ANONYMOUS if PUBLIC_DEMO else func.AuthLevel.FUNCTION"
OPENAI_FALLBACK = ast.parse(
    "try:\n from openai import AzureOpenAI, OpenAIError\n"
    "except ImportError:\n AzureOpenAI = None\n class OpenAIError(Exception):\n  pass\n"
).body[0]
WARNING = ast.parse(
    "if PUBLIC_DEMO:\n logger.warning("
    "'Public paid-AI demo enabled; authentication and cost protection required at edge')\n"
).body[0]


def same_shape(left: ast.AST, right: ast.AST) -> bool:
    return ast.unparse(left) == ast.unparse(right)


def canonical_gaps(project: Path, root: Path) -> tuple[InspectionGap, ...]:
    modules = reachable_modules(project)
    result: list[InspectionGap] = []
    for path, tree in modules.items():
        constants: set[str] = set()
        models: set[str] = set()
        imported: set[str] = set()
        apps = 0
        func_import = False
        invalid = unstable_names(tree)
        for statement in tree.body:
            allowed = False
            names, _ = module_bindings(tree, statement.lineno)
            match statement:
                case ast.Expr(value=ast.Constant(value=str())):
                    allowed = True
                case ast.Import() | ast.ImportFrom():
                    aliases = statement.names
                    module = statement.module if isinstance(statement, ast.ImportFrom) else ""
                    bound = {
                        alias.asname
                        or (
                            alias.name
                            if isinstance(statement, ast.ImportFrom)
                            else alias.name.split(".")[0]
                        )
                        for alias in aliases
                    }
                    allowed = not (
                        bound & imported or bound & constants or "app" in bound or "*" in bound
                    )
                    allowed &= not outside_import(statement, path, project, root)
                    allowed &= not bool(bound & invalid)
                    allowed &= not bool(bound & models)
                    if isinstance(statement, ast.ImportFrom) and module == "azure.functions":
                        allowed &= not any(
                            alias.name in {"FunctionApp", "Blueprint"} for alias in aliases
                        )
                    identities = {
                        "os": "os",
                        "setup_logging": "azure_functions_logging",
                        "get_logger": "azure_functions_logging",
                        "with_context": "azure_functions_logging",
                        "openapi": "azure_functions_openapi",
                        "validate_http": "azure_functions_validation",
                        "BaseModel": "pydantic",
                        "Field": "pydantic",
                        "Final": "typing",
                        "Literal": "typing",
                    }
                    for alias in aliases:
                        local = alias.asname or alias.name
                        if local in identities:
                            if local == "os":
                                allowed &= (
                                    isinstance(statement, ast.Import)
                                    and alias.name == "os"
                                    and alias.asname is None
                                )
                            else:
                                allowed &= (
                                    isinstance(statement, ast.ImportFrom)
                                    and module == identities[local]
                                    and alias.name == local
                                )
                    if "func" in bound:
                        allowed &= (
                            isinstance(statement, ast.Import)
                            and len(aliases) == 1
                            and aliases[0].name == "azure.functions"
                            and aliases[0].asname == "func"
                        )
                        func_import = allowed
                    if module == "__future__":
                        allowed = len(aliases) == 1 and aliases[0].name == "annotations"
                    imported.update(bound)
                case ast.Assign() | ast.AnnAssign():
                    targets = (
                        statement.targets
                        if isinstance(statement, ast.Assign)
                        else [statement.target]
                    )
                    value = statement.value
                    if len(targets) == 1 and isinstance(targets[0], ast.Name) and value is not None:
                        name = targets[0].id
                        allowed = name not in invalid and name not in imported
                        if isinstance(statement, ast.AnnAssign):
                            allowed &= annotation_allowed(statement.annotation)
                        if name == "app":
                            apps += 1
                            allowed &= (
                                func_import
                                and isinstance(value, ast.Call)
                                and ast.unparse(value.func) == "func.FunctionApp"
                                and not value.args
                                and len(value.keywords) == 1
                                and value.keywords[0].arg == "http_auth_level"
                            )
                            if allowed and isinstance(value, ast.Call):
                                expression = value.keywords[0].value
                                allowed = auth_value(expression, names) in {
                                    "FUNCTION",
                                    "ADMIN",
                                    "ANONYMOUS",
                                } or (
                                    ast.unparse(expression) == APP_AUTH
                                    and "PUBLIC_DEMO" in constants
                                )
                        elif name == "PUBLIC_DEMO":
                            allowed &= (
                                isinstance(statement, ast.AnnAssign)
                                and ast.unparse(statement.annotation) == "Final"
                                and ast.unparse(value) == OPT_IN
                                and "os" in imported
                            )
                            constants.add(name)
                        elif name == "logger":
                            allowed &= ast.unparse(value) == "get_logger(__name__)"
                        elif name == "bp":
                            allowed &= func_import and ast.unparse(value) == "func.Blueprint()"
                        else:
                            allowed &= literal_value(value, constants)
                            if allowed:
                                constants.add(name)
                case ast.FunctionDef() | ast.AsyncFunctionDef():
                    allowed = all(
                        decorator_allowed(decorator, constants, models)
                        for decorator in statement.decorator_list
                    ) and all(safe_body(child) for child in statement.body)
                    allowed &= safe_body(statement.args) and (
                        statement.returns is None or safe_body(statement.returns)
                    )
                    allowed &= annotation_allowed(statement.returns) and all(
                        annotation_allowed(argument.annotation)
                        for argument in [
                            *statement.args.posonlyargs,
                            *statement.args.args,
                            *statement.args.kwonlyargs,
                        ]
                    )
                    allowed &= statement.name not in imported | constants | {"app", "func"}
                    allowed &= statement.name not in {
                        "os",
                        "logger",
                        "PUBLIC_DEMO",
                        "setup_logging",
                        "get_logger",
                        "openapi",
                        "with_context",
                        "validate_http",
                        "BaseModel",
                        "Field",
                        "Final",
                        "Literal",
                    }
                    allowed &= all(
                        not isinstance(decorator, ast.Name) or decorator.id in imported
                        for decorator in statement.decorator_list
                    )
                case ast.ClassDef():
                    allowed = (
                        len(statement.bases) == 1
                        and isinstance(statement.bases[0], ast.Name)
                        and statement.bases[0].id == "BaseModel"
                        and "BaseModel" in imported
                        and not statement.decorator_list
                        and not statement.keywords
                    )
                    allowed &= statement.name not in imported | constants | {"app", "func"}
                    allowed &= statement.name not in invalid
                    for field in statement.body:
                        if isinstance(field, ast.AnnAssign) and isinstance(field.target, ast.Name):
                            allowed &= (
                                annotation_allowed(field.annotation)
                                and safe_body(field)
                                and (
                                    field.value is None
                                    or literal_value(field.value, constants)
                                    or isinstance(field.value, ast.Call)
                                    and ast.unparse(field.value.func) == "Field"
                                    and all(
                                        literal_value(arg, constants) for arg in field.value.args
                                    )
                                    and all(
                                        keyword.arg is not None
                                        and literal_value(keyword.value, constants)
                                        for keyword in field.value.keywords
                                    )
                                )
                            )
                        else:
                            allowed = False
                    if allowed:
                        models.add(statement.name)
                case ast.Try():
                    allowed = same_shape(statement, OPENAI_FALLBACK)
                case ast.If():
                    allowed = "PUBLIC_DEMO" in constants and same_shape(statement, WARNING)
                case ast.Expr(value=ast.Call()):
                    allowed = ast.unparse(statement.value) == "setup_logging(format='json')"
                    call = statement.value
                    if (
                        isinstance(call, ast.Call)
                        and ast.unparse(call.func) == "app.register_functions"
                        and len(call.args) == 1
                        and not call.keywords
                        and isinstance(call.args[0], ast.Name)
                    ):
                        blueprint = call.args[0].id
                        allowed = blueprint in imported and any(
                            isinstance(node, ast.Assign)
                            and any(
                                isinstance(target, ast.Name) and target.id == blueprint
                                for target in node.targets
                            )
                            and isinstance(node.value, ast.Call)
                            and ast.unparse(node.value) == "func.Blueprint()"
                            for module in modules.values()
                            for node in module.body
                        )
                case _:
                    allowed = False
            if not allowed:
                result.append(
                    InspectionGap(
                        path.relative_to(root).as_posix(),
                        statement.lineno,
                        "paid-canonical-form",
                        construct_digest(statement),
                    )
                )
        if path == project / "function_app.py" and apps != 1:
            result.append(
                InspectionGap(path.relative_to(root).as_posix(), 1, "paid-canonical-app", "")
            )
    return tuple(result)
