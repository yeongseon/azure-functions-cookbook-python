from pathlib import Path

import pytest

from tools.recipe_routes import routes


@pytest.mark.parametrize(
    "nested",
    [
        "def factory():\n    app = func.FunctionApp(http_auth_level=func.AuthLevel.FUNCTION)",
        "class Factory:\n    app = func.FunctionApp(http_auth_level=func.AuthLevel.FUNCTION)",
    ],
)
def test_nested_binding_cannot_replace_module_auth(tmp_path: Path, nested: str) -> None:
    # Given an exported anonymous app and an unrelated nested binding.
    (tmp_path / "function_app.py").write_text(
        "app = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)\n"
        + nested
        + "\n@app.route(route='chat')\ndef chat(req): return req\n"
    )
    # When declarations are extracted without executing the module.
    result = routes(tmp_path, tmp_path)
    # Then nested rebinding is unresolved, never falsely protected.
    assert result[0].auth == "UNKNOWN"


@pytest.mark.parametrize(
    "binding,expected",
    [
        ("api = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)", "ANONYMOUS"),
        ("api = func.FunctionApp()", "FUNCTION"),
        ("api = unknown_factory()", "UNKNOWN"),
        ("", "UNKNOWN"),
        (
            "api = func.FunctionApp()\nif condition:\n"
            "    api = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)",
            "UNKNOWN",
        ),
        (
            "try:\n    api = func.FunctionApp()\nexcept RuntimeError:\n"
            "    api = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)",
            "UNKNOWN",
        ),
        ("for value in values:\n    api = func.FunctionApp()", "UNKNOWN"),
    ],
)
def test_actual_receiver_controls_inherited_auth(
    tmp_path: Path, binding: str, expected: str
) -> None:
    # Given a route on a receiver that is not named app.
    (tmp_path / "function_app.py").write_text(
        binding + "\n@api.route(route='chat')\ndef chat(req): return req\n"
    )
    # When extracting route metadata, then unresolved bindings fail closed.
    assert routes(tmp_path, tmp_path)[0].auth == expected


def test_registered_blueprint_inherits_receivers_auth(tmp_path: Path) -> None:
    # Given a blueprint registered on an anonymous app under another name.
    (tmp_path / "function_app.py").write_text(
        "from app.routes import bp as chat_routes\n"
        "api = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)\n"
        "api.register_functions(chat_routes)\n"
    )
    (tmp_path / "app").mkdir()
    (tmp_path / "app/routes.py").write_text(
        "bp = func.Blueprint()\n@bp.route(route='chat')\ndef chat(req): return req\n"
    )
    # When extracting declarations, then registration transfers the actual app default.
    assert routes(tmp_path, tmp_path)[0].auth == "ANONYMOUS"
