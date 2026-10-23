import ast
import importlib.util
import json
from pathlib import Path
import random
import sys

import pytest

from tests.test_recipe_auth_sdk import paid_recipe
from tools.recipe_routes import routes
from tools.recipe_security import check_manifest
from tools.security_report import Status

PROTECTED = (
    "import azure.functions as func\napp = func.FunctionApp()\n"
    "@app.route(route='chat')\ndef chat(req): return req\n"
)
HIDDEN = (
    "@app.route(route='hidden', auth_level=func.AuthLevel.ANONYMOUS)\ndef hidden(req): return req\n"
)
SHAPES = (
    'app.route(route="hidden", auth_level=func.AuthLevel.ANONYMOUS)(lambda req: req)\n',
    "class Registration:\n" + "".join("    " + line + "\n" for line in HIDDEN.splitlines()),
    HIDDEN.replace("@app.route", '@globals()["app"].route'),
    "exec(" + repr(HIDDEN) + ")\n",
    'import importlib\nimportlib.import_module("registration").register(app)\n',
    "app._auth_level = func.AuthLevel.ANONYMOUS\n",
    "def register(target):\n"
    "    target.route(route='hidden', auth_level=func.AuthLevel.ANONYMOUS)(lambda req: req)\n"
    "register(app)\n",
    "def register():\n"
    + "".join("    " + line + "\n" for line in HIDDEN.splitlines())
    + "register()\n",
    "setattr(app, '_auth_level', func.AuthLevel.ANONYMOUS)\n",
    "getattr(app, 'route')(route='hidden', auth_level=func.AuthLevel.ANONYMOUS)(lambda req: req)\n",
    "eval(\"app.route(route='hidden', auth_level=func.AuthLevel.ANONYMOUS)(lambda req: req)\")\n",
    "exec(compile(" + repr(HIDDEN) + ", '<registration>', 'exec'))\n",
    HIDDEN.replace("@app.route", '@locals()["app"].route'),
    "vars(app)['_auth_level'] = func.AuthLevel.ANONYMOUS\n",
    "__import__('registration').register(app)\n",
    "from registration import *\nregister(app)\n",
    "from functools import partial, update_wrapper\n"
    "def hidden(req): return req\n"
    "app.route(route='hidden', auth_level=func.AuthLevel.ANONYMOUS)"
    "(update_wrapper(partial(hidden), hidden))\n",
)


def sdk_levels(project: Path) -> list[str]:
    spec = importlib.util.spec_from_file_location("inspection_probe", project / "function_app.py")
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return [
        function.get_trigger().get_dict_repr()["authLevel"].value.upper()
        for function in module.app.get_functions()
        if function.get_trigger().get_dict_repr()["type"] == "httpTrigger"
    ]


@pytest.mark.parametrize("shape", SHAPES)
def test_unmodelled_registration_is_unknown_against_sdk(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, shape: str
) -> None:
    # Given the real SDK and a protected route plus an unsupported mutation.
    project = paid_recipe(tmp_path, PROTECTED + shape)
    (project / "registration.py").write_text(
        "import azure.functions as func\ndef register(app):\n"
        "    app.route(route='hidden', auth_level=func.AuthLevel.ANONYMOUS)(lambda req: req)\n"
    )
    monkeypatch.syspath_prepend(str(project))
    monkeypatch.delitem(sys.modules, "registration", raising=False)
    # When the SDK indexes the module, it exposes anonymous HTTP.
    assert "ANONYMOUS" in sdk_levels(project)
    # Then the static guard must not certify this module.
    assert any(route.auth == "UNKNOWN" for route in routes(project, tmp_path))
    assert check_manifest(tmp_path).status == Status.FAIL


@pytest.mark.parametrize("timer", [False, True])
def test_exec_cannot_hide_http_behind_non_http_classification(tmp_path: Path, timer: bool) -> None:
    prefix = "import azure.functions as func\n"
    if timer:
        prefix += (
            "app = func.FunctionApp()\n"
            "@app.schedule(schedule='0 * * * * *', arg_name='tick')\ndef tick(tick): pass\n"
        )
        source = prefix + "exec(" + repr(HIDDEN) + ")\n"
    else:
        source = prefix + "exec(" + repr("app = func.FunctionApp()\n" + HIDDEN) + ")\n"
    project = paid_recipe(tmp_path, source, "non-http")
    assert "ANONYMOUS" in sdk_levels(project)
    assert any(route.auth == "UNKNOWN" for route in routes(project, tmp_path))
    assert check_manifest(tmp_path).status == Status.INCOMPLETE


def test_public_attribute_that_sdk_ignores_is_not_an_auth_mutation(tmp_path: Path) -> None:
    project = paid_recipe(
        tmp_path, PROTECTED + "app.http_auth_level = func.AuthLevel.ANONYMOUS\n", "protected"
    )
    assert sdk_levels(project) == ["FUNCTION"]
    assert check_manifest(tmp_path).status == Status.PASS


def test_seeded_sdk_differential_never_certifies_anonymous_paid_app(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    generator = random.Random(431)
    for index in range(200):
        root = tmp_path / str(index)
        supported = HIDDEN if generator.choice([False, True]) else "value = 42\n"
        prefix = PROTECTED.replace(
            "func.FunctionApp()",
            generator.choice(
                ["func.FunctionApp()", "func.FunctionApp(http_auth_level=func.AuthLevel.FUNCTION)"]
            ),
        )
        project = paid_recipe(root, prefix + generator.choice((*SHAPES, supported)))
        (project / "registration.py").write_text(
            "import azure.functions as func\ndef register(app):\n"
            "    app.route(route='hidden', auth_level=func.AuthLevel.ANONYMOUS)(lambda req: req)\n"
        )
        monkeypatch.syspath_prepend(str(project))
        monkeypatch.delitem(sys.modules, "registration", raising=False)
        levels = sdk_levels(project)
        result = check_manifest(root)
        assert not ("ANONYMOUS" in levels and result.status == Status.PASS), index


def test_local_imported_module_is_part_of_inspection(tmp_path: Path) -> None:
    project = paid_recipe(tmp_path, PROTECTED + "import registration\n")
    (project / "registration.py").write_text("exec('pass')\n")
    result = check_manifest(tmp_path)
    assert result.status == Status.FAIL
    assert any(
        finding.file.endswith("registration.py") and finding.line == 1
        for finding in result.findings
    )


def test_review_is_exact_and_does_not_allow_changed_construct(tmp_path: Path) -> None:
    from dataclasses import asdict

    from tools.recipe_inspection import inspection_gaps

    project = paid_recipe(tmp_path, PROTECTED + "exec('pass')\n", "protected")
    manifest = tmp_path / "security/recipe-security-manifest.json"
    content = json.loads(manifest.read_text())
    content["inspection_reviews"] = [
        {**asdict(gap), "owner": "maintainer", "reason": "Reviewed inert literal"}
        for gap in inspection_gaps(project, tmp_path)
    ]
    manifest.write_text(json.dumps(content))
    assert check_manifest(tmp_path).status == Status.PASS
    (project / "function_app.py").write_text(PROTECTED + "exec(" + repr(HIDDEN) + ")\n")
    assert check_manifest(tmp_path).status == Status.INCOMPLETE


@pytest.mark.parametrize(
    "source",
    [
        "import runpy\nrunpy.run_module('registration')\n",
        "from importlib import import_module as load\nload('registration')\n",
        "del app._auth_level\n",
        "class Local:\n    app = func.FunctionApp()\n"
        "    @app.route(route='hidden')\n    def hidden(req): return req\n",
    ],
)
def test_conservative_boundary_reports_source_location(tmp_path: Path, source: str) -> None:
    project = paid_recipe(tmp_path, PROTECTED + source, "protected")
    result = check_manifest(tmp_path)
    assert result.status == Status.INCOMPLETE
    assert any(
        finding.id == "INCOMPLETE_INSPECTION" and finding.line > 0 for finding in result.findings
    )
    assert any(route.auth == "UNKNOWN" for route in routes(project, tmp_path))


def test_review_digest_is_independent_of_python_ast_dump_format() -> None:
    from unittest.mock import patch

    from tools.recipe_inspection import construct_digest

    statement = ast.parse("eval(expression)").body[0]
    assert isinstance(statement, ast.Expr)
    node = statement.value
    with patch.object(ast, "dump", return_value="different interpreter formatting"):
        assert (
            construct_digest(node)
            == "5a3bc37cdb8fc138b088893167d0d2a3e25adae64886ba9d4a8b2f476af56ad1"
        )
