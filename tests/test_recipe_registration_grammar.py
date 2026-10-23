import itertools
from pathlib import Path
import py_compile
import random
import sys

import pytest

from tests.test_recipe_auth_sdk import paid_recipe
from tests.test_recipe_inspection_sdk import PROTECTED, sdk_levels
from tools.recipe_routes import routes
from tools.recipe_security import check_manifest
from tools.security_report import Status


def test_oracle_route_kwargs_options_cannot_assume_function(tmp_path: Path) -> None:
    source = (
        "import azure.functions as func\napp = func.FunctionApp()\n"
        'options = {"route": "chat", "auth_level": func.AuthLevel.ANONYMOUS}\n'
        "@app.route(**options)\ndef chat(req): return req\n"
    )
    project = paid_recipe(tmp_path, source)
    assert sdk_levels(project) == ["ANONYMOUS"]
    assert (
        next(route for route in routes(project, tmp_path) if route.handler == "chat").auth
        == "UNKNOWN"
    )
    assert check_manifest(tmp_path).status == Status.FAIL


def test_oracle_bound_route_alias_cannot_hide_anonymous_binding(tmp_path: Path) -> None:
    source = PROTECTED + (
        "from azure.functions import AuthLevel\nANONYMOUS = AuthLevel.ANONYMOUS\n"
        "route = app.route\n"
        '@route(route="hidden", auth_level=ANONYMOUS)\ndef hidden(req): return req\n'
    )
    project = paid_recipe(tmp_path, source)
    assert sdk_levels(project) == ["FUNCTION", "ANONYMOUS"]
    assert any(route.auth == "UNKNOWN" for route in routes(project, tmp_path))
    assert check_manifest(tmp_path).status == Status.FAIL


@pytest.mark.parametrize(
    "expression",
    [
        "app.route(*args, auth_level=func.AuthLevel.FUNCTION)",
        "app.route(**options, auth_level=func.AuthLevel.FUNCTION)",
    ],
)
def test_expansion_overrides_apparently_explicit_auth(tmp_path: Path, expression: str) -> None:
    project = paid_recipe(
        tmp_path,
        "import azure.functions as func\napp = func.FunctionApp()\n"
        f"@{expression}\ndef chat(req): return req\n",
    )
    assert (
        next(route for route in routes(project, tmp_path) if route.handler == "chat").auth
        == "UNKNOWN"
    )


@pytest.mark.parametrize(
    "method",
    [
        "route",
        "schedule",
        "queue_trigger",
        "blob_trigger",
        "service_bus_queue_trigger",
        "event_hub_message_trigger",
        "cosmos_db_trigger",
        "durable_client_input",
        "timer_trigger",
        "function_name",
        "register_functions",
        "register_blueprint",
    ],
)
@pytest.mark.parametrize("receiver", ["app", "bp"])
def test_registration_method_escapes_are_incomplete(
    tmp_path: Path, method: str, receiver: str
) -> None:
    project = paid_recipe(
        tmp_path, PROTECTED + f"bp = func.Blueprint()\nalias = {receiver}.{method}\n"
    )
    assert any(route.auth == "UNKNOWN" for route in routes(project, tmp_path))


@pytest.mark.parametrize(
    "source",
    [
        "consume(app.route)\n",
        "alias = holder.decorator = app.route\n",
        "from functools import partial\nroute = partial(app.route, route='hidden')\n",
        "bp = func.Blueprint(**options)\n",
    ],
)
def test_registration_factory_escapes_and_constructor_expansion_fail_closed(
    tmp_path: Path, source: str
) -> None:
    project = paid_recipe(tmp_path, PROTECTED + source)
    assert any(route.auth == "UNKNOWN" for route in routes(project, tmp_path))


def grammar_source(form: str, auth: str, application: str) -> str:
    setup = "import azure.functions as func\nfrom functools import partial\n"
    constructors = {
        "positional": "app = func.FunctionApp(func.AuthLevel.FUNCTION)\nreceiver = app\n",
        "keyword": "app = func.FunctionApp(http_auth_level=func.AuthLevel.FUNCTION)\n"
        "receiver = app\n",
        "factory": "def make(): return func.FunctionApp()\napp = make()\nreceiver = app\n",
        "alias": "app = func.FunctionApp()\nreceiver = app\n",
        "blueprint": "app = func.FunctionApp()\nreceiver = func.Blueprint()\n",
    }
    setup += constructors[application]
    setup += "@app.route(route='chat')\ndef chat(req): return req\n"
    preparations = {
        "keyword": "",
        "import-alias": "from azure.functions import AuthLevel as A\n",
        "variable": "level = func.AuthLevel.ANONYMOUS\n",
        "dict": "auth_options = {'auth_level': func.AuthLevel.ANONYMOUS}\n",
        "conditional": "enabled = True\n",
        "external": "from grammar_constants import LEVEL\n",
    }
    values = {
        "keyword": "func.AuthLevel.ANONYMOUS",
        "import-alias": "A.ANONYMOUS",
        "variable": "level",
        "dict": "func.AuthLevel.ANONYMOUS",
        "conditional": "func.AuthLevel.ANONYMOUS if enabled else func.AuthLevel.FUNCTION",
        "external": "LEVEL",
    }
    setup += preparations[auth]
    value = values[auth]
    arguments = "**auth_options" if auth == "dict" else f"auth_level={value}"
    decorator = f"receiver.route(route='hidden', {arguments})"
    handler = f"@{decorator}\ndef hidden(req): return req\n"
    if form == "aliased":
        handler = "route = receiver.route\n" + handler.replace("@receiver.route", "@route")
    elif form == "kwargs":
        handler = f"opts = {{'route': 'hidden', 'auth_level': {value}}}\n"
        handler += "@receiver.route(**opts)\ndef hidden(req): return req\n"
    elif form == "args":
        handler = f"args = ('hidden',)\n@receiver.route(*args, {arguments})\n"
        handler += "def hidden(req): return req\n"
    elif form == "partial":
        handler = f"route = partial(receiver.route, route='hidden', {arguments})\n"
        handler += "@route()\ndef hidden(req): return req\n"
    elif form in {"class", "loop", "with", "try", "nested"}:
        header = {
            "class": "class Registration:",
            "loop": "for _ in [0]:",
            "with": "with __import__('contextlib').nullcontext():",
            "try": "try:",
            "nested": "def register():",
        }[form]
        handler = header + "\n" + "".join("    " + line + "\n" for line in handler.splitlines())
        if form == "try":
            handler += "except RuntimeError:\n    raise\n"
        if form == "nested":
            handler += "register()\n"
    elif form == "lambda":
        handler = decorator + "(lambda req: req)\n"
    return (
        setup
        + handler
        + ("app.register_functions(receiver)\n" if application == "blueprint" else "")
    )


def test_seeded_registration_grammar_against_real_sdk(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    forms = (
        "direct",
        "aliased",
        "kwargs",
        "args",
        "partial",
        "class",
        "loop",
        "with",
        "try",
        "nested",
        "lambda",
    )
    auths = ("keyword", "import-alias", "variable", "dict", "conditional", "external")
    applications = ("positional", "keyword", "factory", "alias", "blueprint")
    rebinding = ("once-before", "twice-before", "after-use", "conditional", "local")
    import_forms = (
        "ordinary",
        "positional-auth",
        "sibling",
        "constructor-alias",
        "import-rebinding",
        "conditional-import",
        "package",
        "nested-package",
        "namespace-package",
        "bytecode",
        "relative-entry",
        "cache-only",
    )
    combinations = list(itertools.product(forms, auths, applications, rebinding, import_forms))
    random.Random(4313).shuffle(combinations)
    cases = combinations[:1050]
    for index, (form, auth, application, binding, import_form) in enumerate(cases):
        source = grammar_source(form, auth, application)
        source = source.replace("func.AuthLevel.ANONYMOUS", "auth_binding")
        source = source.replace(
            "import azure.functions as func\n",
            "import azure.functions as func\nauth_binding = func.AuthLevel.ANONYMOUS\n",
            1,
        )
        if binding == "twice-before":
            source = source.replace(
                "from functools import partial",
                "auth_binding = func.AuthLevel.ANONYMOUS\nfrom functools import partial",
            )
        elif binding == "after-use":
            source += "auth_binding = func.AuthLevel.FUNCTION\n"
        elif binding == "conditional":
            source += "if True:\n    auth_binding = func.AuthLevel.FUNCTION\n"
        elif binding == "local":
            source += "def unused():\n    auth_binding = func.AuthLevel.FUNCTION\n"
        if import_form == "positional-auth":
            source = source.replace(
                "@app.route(route='chat')",
                "@app.route('chat','req','$return',['POST'],func.AuthLevel.ANONYMOUS)",
            )
        elif import_form == "constructor-alias":
            source = source.replace(
                "import azure.functions as func\n",
                "import azure.functions as func\nfrom azure.functions import FunctionApp as App\n",
            ).replace("func.FunctionApp(", "App(")
        elif import_form == "import-rebinding":
            source += "import types as auth_binding\n"
        elif import_form == "conditional-import":
            source += "if True:\n    from grammar_constants import LEVEL as auth_binding\n"
        elif import_form == "sibling":
            source = "from endpoints import app\n"
        elif import_form in {"package", "nested-package", "namespace-package"}:
            source = "from endpoints.routes import app\n"
        elif import_form == "bytecode":
            source = "from endpoints import app\n"
        elif import_form == "relative-entry":
            source = "from .endpoints import app\n"
        project = paid_recipe(tmp_path / str(index), source)
        (project / "endpoints.py").write_text(
            "import azure.functions as func\napp = func.FunctionApp(func.AuthLevel.ANONYMOUS)\n"
            "@app.route(route='hidden')\ndef hidden(req): return req\n"
        )
        if import_form == "bytecode":
            py_compile.compile(
                str(project / "endpoints.py"), cfile=str(project / "endpoints.pyc"), doraise=True
            )
            (project / "endpoints.py").unlink()
        elif import_form == "cache-only":
            py_compile.compile(str(project / "endpoints.py"), doraise=True)
            (project / "endpoints.py").unlink()
        if import_form in {"package", "nested-package", "namespace-package"}:
            (project / "endpoints.py").unlink()
            package = project / "endpoints"
            package.mkdir()
            route_source = (
                "import azure.functions as func\napp = func.FunctionApp(func.AuthLevel.ANONYMOUS)\n"
                "@app.route(route='hidden')\ndef hidden(req): return req\n"
            )
            (package / "routes.py").write_text(route_source)
            if import_form != "namespace-package":
                (package / "__init__.py").write_text("from .routes import app\n")
            if import_form == "nested-package":
                nested = package / "nested"
                nested.mkdir()
                (nested / "__init__.py").write_text('"Nested package."\n')
                (nested / "routes.py").write_text("from ..routes import app\n")
                (project / "function_app.py").write_text(
                    "from endpoints.nested.routes import app\n"
                )
        (project / "grammar_constants.py").write_text(
            "from azure.functions import AuthLevel\nLEVEL = AuthLevel.ANONYMOUS\n"
        )
        monkeypatch.syspath_prepend(str(project))
        monkeypatch.setattr(
            sys,
            "path",
            [str(project), *(entry for entry in sys.path if not entry.startswith(str(tmp_path)))],
        )
        monkeypatch.delitem(sys.modules, "grammar_constants", raising=False)
        monkeypatch.delitem(sys.modules, "endpoints", raising=False)
        for module_name in tuple(sys.modules):
            if module_name.startswith("endpoints."):
                monkeypatch.delitem(sys.modules, module_name, raising=False)
        if import_form == "relative-entry":
            with pytest.raises(ImportError, match="no known parent package"):
                sdk_levels(project)
            assert check_manifest(tmp_path / str(index)).status != Status.PASS
            continue
        levels = sdk_levels(project)
        assert "ANONYMOUS" in levels, (index, form, auth, application)
        extracted = routes(project, tmp_path)
        assert check_manifest(tmp_path / str(index)).status != Status.PASS, (index, source)
        hidden = [route for route in extracted if route.handler == "hidden"]
        assert all(route.auth != "FUNCTION" for route in hidden), (index, source)
