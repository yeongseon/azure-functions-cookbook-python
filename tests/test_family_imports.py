import ast
from pathlib import Path

import pytest

from tools.recipe_discovery import recipe_files

pytestmark = pytest.mark.repo_infra

_EXAMPLES = Path(__file__).parents[1] / "examples"


def test_family_packages_are_not_soft_imported() -> None:
    """Offline: no recipe source soft-imports a family package behind `except ImportError`.

    A missing family API must fail at import time instead of silently selecting a fallback.
    """
    violations: list[str] = []

    for source in recipe_files(_EXAMPLES, "*.py"):
        tree = ast.parse(source.read_text())
        for node in ast.walk(tree):
            if not isinstance(node, ast.Try):
                continue
            catches_import_error = any(
                isinstance(handler.type, ast.Name) and handler.type.id == "ImportError"
                for handler in node.handlers
            )
            family_import = any(
                (
                    isinstance(child, ast.ImportFrom)
                    and child.module is not None
                    and child.module.startswith("azure_functions_")
                )
                or (
                    isinstance(child, ast.Call)
                    and isinstance(child.func, ast.Attribute)
                    and child.func.attr == "import_module"
                    and child.args
                    and isinstance(child.args[0], ast.Constant)
                    and isinstance(child.args[0].value, str)
                    and child.args[0].value.startswith("azure_functions_")
                )
                for statement in node.body
                for child in ast.walk(statement)
            )
            if catches_import_error and family_import:
                violations.append(f"{source.relative_to(_EXAMPLES)}:{node.lineno}")

    assert violations == [], "\n".join(violations)
