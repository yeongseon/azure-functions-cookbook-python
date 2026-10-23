from pathlib import Path
import sys

import pytest

from tests.test_recipe_auth_sdk import paid_recipe
from tests.test_recipe_inspection_sdk import sdk_levels
from tools.recipe_routes import routes
from tools.recipe_security import ROOT, check_manifest
from tools.security_report import Status


def assert_unknown(project: Path, root: Path) -> None:
    assert any(route.auth == "UNKNOWN" for route in routes(project, root))
    assert check_manifest(root).status == Status.FAIL


def test_oracle_five_positional_route_auth_is_not_function(tmp_path: Path) -> None:
    project = paid_recipe(
        tmp_path,
        "import azure.functions as func\napp = func.FunctionApp()\n"
        "@app.route('chat','req','$return',['POST'],func.AuthLevel.ANONYMOUS)\n"
        "def chat(req): return req\n",
    )
    assert sdk_levels(project) == ["ANONYMOUS"]
    assert_unknown(project, tmp_path)


def test_oracle_five_sibling_exported_app_is_inspected(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    project = paid_recipe(tmp_path, "from endpoints import app\n")
    (project / "endpoints.py").write_text(
        "import azure.functions as func\napp = func.FunctionApp(func.AuthLevel.ANONYMOUS)\n"
        "@app.route(route='hidden')\ndef hidden(req): return req\n"
    )
    monkeypatch.syspath_prepend(str(project))
    monkeypatch.delitem(sys.modules, "endpoints", raising=False)
    assert sdk_levels(project) == ["ANONYMOUS"]
    assert_unknown(project, tmp_path)


@pytest.mark.parametrize(
    "mutation",
    [
        "web._auth_level = ANONYMOUS\n@web.route(route='chat')\ndef chat(req): return req\n",
        "route = web.route\n@route(route='chat', auth_level=ANONYMOUS)\n"
        "def chat(req): return req\n",
    ],
)
def test_oracle_five_constructor_alias_receiver_is_unknown(tmp_path: Path, mutation: str) -> None:
    project = paid_recipe(
        tmp_path,
        "import azure.functions as func\nfrom azure.functions import FunctionApp as App\n"
        "ANONYMOUS = func.AuthLevel.ANONYMOUS\nweb = App()\n" + mutation + "app = web\n",
    )
    assert sdk_levels(project) == ["ANONYMOUS"]
    assert_unknown(project, tmp_path)


def test_oracle_five_conditional_import_alias_counts_as_write(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    project = paid_recipe(
        tmp_path,
        "import azure.functions as func\napp = func.FunctionApp()\nauth = func.AuthLevel.FUNCTION\n"
        "try:\n    from constants import LEVEL as auth\nexcept ImportError:\n    pass\n"
        "@app.route(route='chat', auth_level=auth)\ndef chat(req): return req\n",
    )
    (project / "constants.py").write_text(
        "import azure.functions as func\nLEVEL = func.AuthLevel.ANONYMOUS\n"
    )
    monkeypatch.syspath_prepend(str(project))
    monkeypatch.delitem(sys.modules, "constants", raising=False)
    assert sdk_levels(project) == ["ANONYMOUS"]
    assert_unknown(project, tmp_path)


@pytest.mark.parametrize(
    "name", ["openai_direct_chat", "ai_image_generation", "streaming_ai_response"]
)
@pytest.mark.parametrize("mutation", ["default", "anonymous", "alias", "try-import"])
def test_real_paid_recipes_use_canonical_form(tmp_path: Path, name: str, mutation: str) -> None:
    source = (ROOT / "examples/ai-and-agents" / name / "function_app.py").read_text()
    if mutation == "anonymous":
        source += "\n@app.route(route='extra', auth_level=func.AuthLevel.ANONYMOUS)\n"
        source += "def extra(req): return req\n"
    elif mutation == "alias":
        source = source.replace(
            "import azure.functions as func", "import azure.functions as alternate"
        )
    elif mutation == "try-import":
        source += "\ntry:\n    import types as func\nexcept ImportError:\n    pass\n"
    project = paid_recipe(tmp_path, source)
    if mutation == "default":
        import json

        manifest = tmp_path / "security/recipe-security-manifest.json"
        data = json.loads(manifest.read_text())
        data["recipes"]["examples/demo/chat"]["routes"] = [
            f"{route.handler}={route.auth}" for route in routes(project, tmp_path)
        ]
        manifest.write_text(json.dumps(data))
        assert not any(route.auth == "UNKNOWN" for route in routes(project, tmp_path))
        assert check_manifest(tmp_path).status == Status.PASS
    else:
        assert_unknown(project, tmp_path)


@pytest.mark.parametrize("setting", [None, "true", "True", "false", " true "])
def test_exact_canonical_opt_in_matches_sdk(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, setting: str | None
) -> None:
    from tools.paid_recipe_canonical import canonical_gaps

    if setting is None:
        monkeypatch.delenv("COOKBOOK_PUBLIC_DEMO", raising=False)
    else:
        monkeypatch.setenv("COOKBOOK_PUBLIC_DEMO", setting)
    source = (
        "import os\nfrom typing import Final\nimport azure.functions as func\n"
        "PUBLIC_DEMO: Final = os.getenv('COOKBOOK_PUBLIC_DEMO', '') == 'true'\n"
        "app = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS "
        "if PUBLIC_DEMO else func.AuthLevel.FUNCTION)\n"
        "@app.route(route='chat')\ndef chat(req): return req\n"
    )
    project = paid_recipe(tmp_path, source)
    assert canonical_gaps(project, tmp_path) == ()
    assert check_manifest(tmp_path).status == Status.PASS
    assert sdk_levels(project) == (["ANONYMOUS"] if setting == "true" else ["FUNCTION"])


def test_paid_first_party_import_outside_recipe_is_unknown(tmp_path: Path) -> None:
    (tmp_path / "shared.py").write_text("VALUE = 1\n")
    project = paid_recipe(
        tmp_path,
        "import shared\nimport azure.functions as func\n"
        "app = func.FunctionApp(http_auth_level=func.AuthLevel.FUNCTION)\n"
        "@app.route(route='chat')\ndef chat(req): return req\n",
    )
    assert_unknown(project, tmp_path)


def test_recursive_package_relative_import_is_checked(tmp_path: Path) -> None:
    from tools.recipe_local_imports import reachable_modules

    project = paid_recipe(tmp_path, "import package\n")
    package = project / "package"
    package.mkdir()
    (package / "__init__.py").write_text("from . import nested\n")
    (package / "nested.py").write_text("from .. import helper\n")
    (project / "helper.py").write_text("VALUE = 1\n")
    assert len(reachable_modules(project)) == 4
    assert_unknown(project, tmp_path)


def test_reviewed_sdk_namespace_cannot_be_rebound_by_import(tmp_path: Path) -> None:
    import ast
    import json

    from tools.recipe_binding_reviews import binding_digest, reviewed_bindings

    project = paid_recipe(
        tmp_path,
        "try:\n import azure.functions as func\nexcept ImportError:\n func = None\n"
        "import types as func\n",
    )
    path = project / "function_app.py"
    tree = ast.parse(path.read_text())
    policy = tmp_path / "security/recipe-security-manifest.json"
    data = json.loads(policy.read_text())
    data["binding_reviews"] = [
        {
            "file": "examples/demo/chat/function_app.py",
            "line": 1,
            "name": "func",
            "digest": binding_digest(tree.body[0]),
            "owner": "maintainer",
            "reason": "fixed SDK fallback",
        }
    ]
    policy.write_text(json.dumps(data))
    assert reviewed_bindings(path, tmp_path, tree) == frozenset()


def test_route_signature_allows_only_leading_route_string() -> None:
    import inspect

    import azure.functions as func

    parameters = list(inspect.signature(func.FunctionApp.route).parameters)
    assert parameters[:2] == ["self", "route"]
    assert parameters.index("auth_level") == 5


@pytest.mark.parametrize(
    "syntax",
    [
        "with manager() as auth:\n pass\n",
        "for auth in []:\n pass\n",
        "try:\n pass\nexcept RuntimeError as auth:\n pass\n",
        "del auth\n",
        "from constants import LEVEL as auth\n",
        "import types as auth\n",
    ],
)
def test_import_and_binding_targets_are_auth_writes(syntax: str) -> None:
    import ast

    from tools.recipe_binding_order import unstable_names

    assert "auth" in unstable_names(ast.parse("auth = 'function'\n" + syntax))


def test_canonical_imported_blueprint_is_resolved_in_module_set(tmp_path: Path) -> None:
    project = paid_recipe(
        tmp_path,
        "import azure.functions as func\nfrom endpoints import bp\n"
        "app = func.FunctionApp(http_auth_level=func.AuthLevel.FUNCTION)\n"
        "app.register_functions(bp)\n",
    )
    (project / "endpoints.py").write_text(
        "import azure.functions as func\nbp = func.Blueprint()\n"
        "@bp.route(route='chat')\ndef chat(req): return req\n"
    )
    assert check_manifest(tmp_path).status == Status.PASS
