from pathlib import Path

import pytest

from tests.test_recipe_auth_sdk import paid_recipe
from tests.test_recipe_inspection_sdk import sdk_levels
from tools.recipe_routes import routes
from tools.recipe_security import check_manifest
from tools.security_report import Status

PREFIX = "import azure.functions as func\napp = func.FunctionApp()\n"
CHAT = '@app.route(route="chat", auth_level=auth)\ndef chat(req): return req\n'


def test_oracle_later_auth_assignment_cannot_change_earlier_binding(tmp_path: Path) -> None:
    source = (
        PREFIX + "auth = func.AuthLevel.ANONYMOUS\n" + CHAT + "auth = func.AuthLevel.FUNCTION\n"
    )
    project = paid_recipe(tmp_path, source)
    assert sdk_levels(project) == ["ANONYMOUS"]
    assert (
        next(route for route in routes(project, tmp_path) if route.handler == "chat").auth
        == "UNKNOWN"
    )
    assert check_manifest(tmp_path).status == Status.FAIL


def test_oracle_reused_auth_variable_cannot_rewrite_first_of_two_routes(tmp_path: Path) -> None:
    source = (
        PREFIX
        + "auth = func.AuthLevel.ANONYMOUS\n"
        + CHAT
        + (
            'auth = func.AuthLevel.FUNCTION\n@app.route(route="protected", auth_level=auth)\n'
            "def protected(req): return req\n"
        )
    )
    project = paid_recipe(tmp_path, source)
    assert sdk_levels(project) == ["ANONYMOUS", "FUNCTION"]
    assert all(route.auth == "UNKNOWN" for route in routes(project, tmp_path))


@pytest.mark.parametrize(
    "mutation",
    [
        "auth = func.AuthLevel.FUNCTION\n",
        "auth += ''\n",
        "(auth := func.AuthLevel.FUNCTION)\n",
        "if True:\n    auth = func.AuthLevel.FUNCTION\n",
        "def unused():\n    auth = func.AuthLevel.FUNCTION\n",
        "def change():\n    global auth\n    auth = func.AuthLevel.FUNCTION\nchange()\n",
        "class Local:\n    auth = func.AuthLevel.FUNCTION\n",
    ],
)
def test_auth_rebinding_is_unknown_even_after_sdk_registration(
    tmp_path: Path, mutation: str
) -> None:
    project = paid_recipe(tmp_path, PREFIX + "auth = 'anonymous'\n" + CHAT + mutation)
    assert sdk_levels(project) == ["ANONYMOUS"]
    assert (
        next(route for route in routes(project, tmp_path) if route.handler == "chat").auth
        == "UNKNOWN"
    )


def test_constructor_auth_rebinding_cannot_change_declared_default(tmp_path: Path) -> None:
    source = (
        "import azure.functions as func\nlevel = func.AuthLevel.ANONYMOUS\n"
        "app = func.FunctionApp(http_auth_level=level)\nlevel = func.AuthLevel.FUNCTION\n"
        '@app.route(route="chat")\ndef chat(req): return req\n'
    )
    project = paid_recipe(tmp_path, source)
    assert sdk_levels(project) == ["ANONYMOUS"]
    assert all(route.auth == "UNKNOWN" for route in routes(project, tmp_path))


def test_single_auth_assignment_preceding_declaration_is_supported(tmp_path: Path) -> None:
    project = paid_recipe(tmp_path, PREFIX + "auth = func.AuthLevel.ANONYMOUS\n" + CHAT)
    assert sdk_levels(project) == ["ANONYMOUS"]
    assert routes(project, tmp_path)[0].auth == "ANONYMOUS"


def test_later_app_rebinding_cannot_certify_earlier_receiver(tmp_path: Path) -> None:
    source = PREFIX + "auth = func.AuthLevel.ANONYMOUS\n" + CHAT + "app = func.FunctionApp()\n"
    project = paid_recipe(tmp_path, source)
    assert any(route.auth == "UNKNOWN" for route in routes(project, tmp_path))


def test_auth_name_assigned_only_after_use_is_unknown(tmp_path: Path) -> None:
    project = paid_recipe(tmp_path, PREFIX + CHAT + "auth = func.AuthLevel.FUNCTION\n")
    assert (
        next(route for route in routes(project, tmp_path) if route.handler == "chat").auth
        == "UNKNOWN"
    )


def test_reviewed_fallback_does_not_allow_new_later_rebinding(tmp_path: Path) -> None:
    import ast
    import json

    from tools.recipe_inspection import construct_digest

    block = "try:\n    auth = 'anonymous'\nexcept ImportError:\n    auth = 'anonymous'\n"
    project = paid_recipe(tmp_path, PREFIX + block + CHAT)
    manifest = tmp_path / "security/recipe-security-manifest.json"
    data = json.loads(manifest.read_text())
    node = ast.parse(block).body[0]
    data["binding_reviews"] = [
        {
            "file": "examples/demo/chat/function_app.py",
            "line": 3,
            "name": "auth",
            "digest": construct_digest(node),
            "owner": "maintainer",
            "reason": "fixed fallback",
        }
    ]
    manifest.write_text(json.dumps(data))
    (project / "function_app.py").write_text(PREFIX + block + CHAT + "auth = 'function'\n")
    assert check_manifest(tmp_path).status == Status.FAIL
