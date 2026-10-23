import importlib.util
import inspect
import json
from pathlib import Path

import azure.functions as func
import pytest

from tools.recipe_routes import routes
from tools.recipe_security import check_manifest
from tools.security_report import Status


def paid_recipe(root: Path, source: str, category: str = "paid-backend") -> Path:
    project = root / "examples/demo/chat"
    project.mkdir(parents=True)
    (project / "function_app.py").write_text(source)
    (root / "security").mkdir()
    (root / "security/recipe-security-manifest.json").write_text(
        json.dumps(
            {
                "recipes": {
                    "examples/demo/chat": {
                        "category": category,
                        "reason": "test",
                        "routes": ["chat=FUNCTION"] if category != "non-http" else [],
                    }
                }
            }
        )
    )
    return project


@pytest.mark.parametrize(
    "setup,constructor",
    [
        ("", "func.FunctionApp(func.AuthLevel.ANONYMOUS)"),
        ("", "func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)"),
        ("from azure.functions import AuthLevel\n", "func.FunctionApp(AuthLevel.ANONYMOUS)"),
        ("from azure.functions import AuthLevel as A\n", "func.FunctionApp(A.ANONYMOUS)"),
        (
            "import azure.functions\n",
            "azure.functions.FunctionApp(azure.functions.AuthLevel.ANONYMOUS)",
        ),
        ("level = func.AuthLevel.ANONYMOUS\n", "func.FunctionApp(level)"),
        ("", "func.FunctionApp(func.AuthLevel.ANONYMOUS if True else func.AuthLevel.FUNCTION)"),
        ("from azure.functions import FunctionApp as App\n", "App(func.AuthLevel.ANONYMOUS)"),
        ("App = func.FunctionApp\n", "App(func.AuthLevel.ANONYMOUS)"),
    ],
)
def test_constructor_auth_matches_real_sdk(tmp_path: Path, setup: str, constructor: str) -> None:
    # Given a runnable fake recipe with real SDK decorators.
    project = paid_recipe(
        tmp_path,
        "import azure.functions as func\n"
        + setup
        + f"app = {constructor}\n@app.route(route='chat')\ndef chat(req): return req\n",
    )
    spec = importlib.util.spec_from_file_location("sdk_auth_probe", project / "function_app.py")
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    # When both SDK indexing and static policy inspect the declaration.
    actual = module.app.get_functions()[0].get_trigger().get_dict_repr()["authLevel"].value.upper()
    extracted = routes(project, tmp_path)[0].auth
    # Then static evidence agrees with the SDK and the paid policy blocks.
    assert actual == extracted == "ANONYMOUS"
    assert check_manifest(tmp_path).status == Status.FAIL


def test_constructor_parameter_contract_matches_installed_sdk() -> None:
    assert list(inspect.signature(func.FunctionApp).parameters) == ["http_auth_level"]
    assert (
        inspect.signature(func.FunctionApp).parameters["http_auth_level"].default
        == func.AuthLevel.FUNCTION
    )


@pytest.mark.parametrize(
    "constructor",
    [
        "func.FunctionApp(*levels)",
        "func.FunctionApp(**settings)",
        "func.FunctionApp(http_auth_level=get_level())",
        "func.FunctionApp(http_auth_level=external.level)",
        "func.FunctionApp(http_auth_level=unknown)",
        "factory()",
        "untrusted.FunctionApp()",
        "func.FunctionApp(func.AuthLevel.ANONYMOUS, http_auth_level=func.AuthLevel.FUNCTION)",
        "func.FunctionApp(unknown_option=True)",
    ],
)
def test_unresolved_constructor_never_assumes_function_auth(
    tmp_path: Path, constructor: str
) -> None:
    project = paid_recipe(
        tmp_path,
        f"import azure.functions as func\napp = {constructor}\n"
        "@app.route(route='chat')\ndef chat(req): return req\n",
    )
    assert routes(project, tmp_path)[0].auth == "UNKNOWN"
    assert check_manifest(tmp_path).status == Status.FAIL


@pytest.mark.parametrize(
    "source",
    [
        "def make():\n    app = func.FunctionApp(func.AuthLevel.ANONYMOUS)\n"
        "    @app.route(route='chat')\n    def chat(req): return req\n"
        "    return app\napp = make()\n",
        "app = func.FunctionApp()\nfrom external import *\n"
        "@app.route(route='chat')\ndef chat(req): return req\n",
        "from external import make\napp = make()\n",
        "app = func.FunctionApp()\napp.register_functions(unknown_blueprint)\n",
        "app = func.FunctionApp()\nif enabled:\n"
        "    @app.route(route='chat')\n    def chat(req): return req\n",
        "app = func.FunctionApp()\nfor item in items:\n    app.register_functions(item)\n",
        "api = external_factory()\n",
        "app = func.FunctionApp()\nbp = func.Blueprint(**unknown)\napp.register_functions(bp)\n",
        "app = func.FunctionApp()\n",
        "app = func.FunctionApp()\napp = external_app\n",
    ],
)
def test_dynamic_registration_cannot_masquerade_as_non_http(tmp_path: Path, source: str) -> None:
    project = paid_recipe(tmp_path, "import azure.functions as func\n" + source, "non-http")
    assert any(route.auth == "UNKNOWN" for route in routes(project, tmp_path))
    assert check_manifest(tmp_path).status in {Status.FAIL, Status.INCOMPLETE}
