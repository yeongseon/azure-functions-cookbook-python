import importlib.util
from pathlib import Path
import py_compile
import sys

import pytest

from tests.test_recipe_auth_sdk import paid_recipe
from tests.test_recipe_inspection_sdk import sdk_levels
from tools.recipe_security import check_manifest
from tools.security_report import Status

ENTRY = (
    "import azure.functions as func\n"
    "app = func.FunctionApp(http_auth_level=func.AuthLevel.FUNCTION)\n"
    "@app.route(route='chat')\ndef chat(req): return req\n"
)
BOOTSTRAP = (
    "import azure.functions as func\nfrom function_app import app\n"
    "@app.route(route='hidden', auth_level=func.AuthLevel.ANONYMOUS)\n"
    "def hidden(req): return req\n"
)


def test_oracle_seven_sourceless_registration_is_not_external(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    project = paid_recipe(tmp_path, ENTRY + "import bootstrap\n")
    source = project / "bootstrap.py"
    source.write_text(BOOTSTRAP)
    py_compile.compile(str(source), cfile=str(project / "bootstrap.pyc"), doraise=True)
    source.unlink()
    monkeypatch.syspath_prepend(str(project))
    monkeypatch.delitem(sys.modules, "bootstrap", raising=False)
    spec = importlib.util.spec_from_file_location("function_app", project / "function_app.py")
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    monkeypatch.setitem(sys.modules, "function_app", module)
    spec.loader.exec_module(module)
    levels = [
        function.get_trigger().get_dict_repr()["authLevel"].value
        for function in module.app.get_functions()
    ]
    assert levels == ["function", "anonymous"]
    assert check_manifest(tmp_path).status == Status.FAIL


def test_oracle_seven_entrypoint_relative_import_is_unknown(tmp_path: Path) -> None:
    project = paid_recipe(tmp_path, ENTRY + "from .endpoints import bp\n")
    (project / "endpoints.py").write_text("import azure.functions as func\nbp = func.Blueprint()\n")
    with pytest.raises(ImportError, match="no known parent package"):
        sdk_levels(project)
    assert check_manifest(tmp_path).status == Status.FAIL


@pytest.mark.parametrize(
    "filename",
    [
        "bootstrap.pyc",
        "bootstrap.pyo",
        "bootstrap.so",
        "bootstrap.pyd",
        "bootstrap.cpython-314-x86_64-linux-gnu.so",
        "bootstrap.zip",
        "bootstrap.egg",
        "bootstrap/__init__.pyc",
        "bootstrap/__init__.pyd",
    ],
)
def test_opaque_import_candidates_fail_closed(tmp_path: Path, filename: str) -> None:
    project = paid_recipe(tmp_path, ENTRY + "import bootstrap\n")
    candidate = project / filename
    candidate.parent.mkdir(parents=True, exist_ok=True)
    candidate.write_bytes(b"opaque")
    assert check_manifest(tmp_path).status == Status.FAIL


def test_pycache_only_is_not_a_sourceless_import(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    project = paid_recipe(tmp_path, ENTRY)
    source = project / "bootstrap.py"
    source.write_text(BOOTSTRAP)
    py_compile.compile(str(source), doraise=True)
    source.unlink()
    monkeypatch.syspath_prepend(str(project))
    monkeypatch.delitem(sys.modules, "bootstrap", raising=False)
    assert importlib.util.find_spec("bootstrap") is None
    assert check_manifest(tmp_path).status == Status.PASS


@pytest.mark.parametrize(
    "hook", ["sitecustomize.py", "usercustomize.py", "startup.pth", "local.settings.json", ".env"]
)
@pytest.mark.parametrize(
    "category,expected", [("paid-backend", Status.FAIL), ("protected", Status.INCOMPLETE)]
)
def test_recipe_startup_customization_is_inspection_gap(
    tmp_path: Path, hook: str, category: str, expected: Status
) -> None:
    project = paid_recipe(tmp_path, ENTRY, category)
    content = (
        '{"Values":{"PYTHONPATH":"."}}'
        if hook.endswith(".json")
        else ("PYTHONPATH=.\n" if hook == ".env" else "# startup hook\n")
    )
    (project / hook).write_text(content)
    result = check_manifest(tmp_path)
    assert result.status == expected
    assert any(finding.id == "INCOMPLETE_INSPECTION" for finding in result.findings)
