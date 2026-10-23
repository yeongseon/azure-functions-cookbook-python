from pathlib import Path
import sys

import pytest

from tests.test_recipe_auth_sdk import paid_recipe
from tests.test_recipe_inspection_sdk import sdk_levels
from tools.recipe_local_imports import reachable_modules
from tools.recipe_security import check_manifest
from tools.security_report import Status

ENTRY = (
    "import azure.functions as func\nfrom endpoints.routes import bp\n"
    "app = func.FunctionApp(http_auth_level=func.AuthLevel.FUNCTION)\n"
    "app.register_functions(bp)\n"
)
ROUTES = (
    "import azure.functions as func\nbp = func.Blueprint()\n"
    "@bp.route(route='chat')\ndef chat(req): return req\n"
)
HIDDEN = (
    "import azure.functions as func\nfrom .routes import bp\n"
    "@bp.route(route='hidden', auth_level=func.AuthLevel.ANONYMOUS)\n"
    "def hidden(req): return req\n"
)


def clear_packages(monkeypatch: pytest.MonkeyPatch) -> None:
    for name in tuple(sys.modules):
        if name == "endpoints" or name.startswith("endpoints."):
            monkeypatch.delitem(sys.modules, name, raising=False)


def test_oracle_six_dotted_import_executes_anonymous_package_initializer(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    project = paid_recipe(tmp_path, ENTRY)
    package = project / "endpoints"
    package.mkdir()
    (package / "routes.py").write_text(ROUTES)
    (package / "__init__.py").write_text(HIDDEN)
    clear_packages(monkeypatch)
    monkeypatch.syspath_prepend(str(project))
    assert sdk_levels(project) == ["FUNCTION", "ANONYMOUS"]
    assert check_manifest(tmp_path).status == Status.FAIL
    assert (package / "__init__.py").resolve() in reachable_modules(project)


@pytest.mark.parametrize(
    "layout",
    [
        "docstring",
        "reexport",
        "nested",
        "from-module",
        "from-package",
        "namespace",
        "relative-parent",
    ],
)
def test_sdk_package_import_execution_is_fully_inspected(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, layout: str
) -> None:
    project = paid_recipe(tmp_path, ENTRY)
    package = project / "endpoints"
    package.mkdir()
    (package / "routes.py").write_text(ROUTES)
    (package / "__init__.py").write_text('"Package documentation."\n')
    expected = {"function_app.py", "endpoints/routes.py", "endpoints/__init__.py"}
    entry = ENTRY
    if layout == "reexport":
        (package / "__init__.py").write_text("from .routes import bp\n")
        entry = ENTRY.replace("from endpoints.routes import bp", "from endpoints import bp")
    elif layout in {"nested", "relative-parent"}:
        nested = package / "nested"
        nested.mkdir()
        (nested / "__init__.py").write_text('"Nested package."\n')
        (nested / "routes.py").write_text("from ..routes import bp\n")
        entry = ENTRY.replace("endpoints.routes", "endpoints.nested.routes")
        expected.update({"endpoints/nested/__init__.py", "endpoints/nested/routes.py"})
        if layout == "relative-parent":
            (nested / "routes.py").write_text("from .. import routes\nfrom ..routes import bp\n")
    elif layout == "from-module":
        entry = ENTRY.replace(
            "from endpoints.routes import bp",
            "from endpoints import routes\nfrom endpoints.routes import bp",
        )
    elif layout == "from-package":
        nested = package / "nested"
        nested.mkdir()
        (nested / "__init__.py").write_text("from ..routes import bp\n")
        entry = ENTRY.replace(
            "from endpoints.routes import bp",
            "from endpoints import nested\nfrom endpoints.nested import bp",
        )
        expected.add("endpoints/nested/__init__.py")
    elif layout == "namespace":
        (package / "__init__.py").unlink()
        expected.remove("endpoints/__init__.py")
    (project / "function_app.py").write_text(entry)
    clear_packages(monkeypatch)
    monkeypatch.syspath_prepend(str(project))
    assert sdk_levels(project) == ["FUNCTION"]
    assert {path.relative_to(project).as_posix() for path in reachable_modules(project)} == expected
    assert check_manifest(tmp_path).status == Status.PASS


@pytest.mark.parametrize("entry", ["from endpoints.missing import bp", "from .missing import bp"])
def test_unresolved_recipe_local_import_fails_closed(tmp_path: Path, entry: str) -> None:
    project = paid_recipe(tmp_path, ENTRY.replace("from endpoints.routes import bp", entry))
    (project / "endpoints").mkdir()
    assert check_manifest(tmp_path).status == Status.FAIL


@pytest.mark.parametrize(
    "layout",
    ["ambiguous", "module-parent", "missing-relative", "relative-escape", "star", "symlink"],
)
def test_unmodelled_import_resolution_is_unknown(tmp_path: Path, layout: str) -> None:
    import ast

    from tools.recipe_local_imports import resolve_import

    project = tmp_path / "recipe"
    project.mkdir()
    path = project / "function_app.py"
    path.touch()
    text = "import pkg.child"
    if layout == "ambiguous":
        (project / "pkg.py").touch()
        (project / "pkg").mkdir()
        (project / "pkg/__init__.py").touch()
        text = "import pkg"
    elif layout == "module-parent":
        (project / "pkg.py").touch()
        (project / "pkg").mkdir()
        (project / "pkg/child.py").touch()
    elif layout == "missing-relative":
        text = "from .missing import value"
    elif layout == "relative-escape":
        text = "from ...outside import value"
    elif layout == "star":
        (project / "pkg.py").touch()
        text = "from pkg import *"
    else:
        outside = tmp_path / "outside.py"
        outside.write_text("VALUE = 1\n")
        (project / "pkg.py").symlink_to(outside)
        text = "import pkg"
    node = __import__("ast").parse(text).body[0]
    assert isinstance(node, (ast.Import, ast.ImportFrom))
    assert resolve_import(path, node, project).unresolved
