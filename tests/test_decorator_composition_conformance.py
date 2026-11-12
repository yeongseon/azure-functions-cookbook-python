"""Table-driven decorator-composition conformance tests (#474).

One compact table of *tested* compositions (positive and negative). It is
regression hardening over released toolkit packages, not a claim that every
decorator permutation is supported. Existing, more specific tests stay in place:

* ``tests/test_worker_context_injection.py`` -- literal worker-visible ``context``
* ``tests/test_db_input_output_openapi.py`` -- DB recipe response schema
* ``tests/test_endpoint_consumer_compat.py`` -- Validation/LangGraph producers
  consumed by OpenAPI
* ``tests/test_worker_registration_guard.py`` -- real worker ``Registry`` indexing
  (``worker_registration`` marker; the handlers below are listed there too)

Tested composition table
------------------------

====  ===========================================================  =========
Id    Composition                                                  Expected
====  ===========================================================  =========
P1    HTTP + @openapi + @with_context + @validate_http (body)      supported
      (recipe ``ai-and-agents/langgraph_agent``)
P2    HTTP + @openapi + @with_context + @validate_http (path,      supported
      model return; recipe ``apis-and-ingress/apim_function_backend``)
P3    HTTP + @openapi + @with_context + @validate_http above       supported
      ``db.output`` (fixture; same decorators as the DB recipe,
      with ``@validate_http`` above ``@db.output``)
P4    HTTP + @openapi + ``db.output`` + @with_context +            xfail
      @validate_http (recipe ``data-and-pipelines/db_input_output``)
      -- raises ``TypeError`` on azure-functions-db>=0.9.0 (#503)
P5    Independent LangGraph ``endpoint`` producer read by OpenAPI  supported
N1    ``@validate_http`` above ``@app.route``                      rejected
N2    ``endpoint`` namespace with an unsupported version           degraded +
                                                                   warning
N3    explicit ``@openapi(requests=...)`` vs ``@validate_http``    rejected
      request model (needs azure-functions-openapi>=0.31)
====  ===========================================================  =========

Each case separates four checks: (a) registered SDK function, bindings and
signature, (b) ``_azure_functions_metadata`` namespaces and versions, (c) HTTP
status/body/header behavior, (d) OpenAPI contract versus that behavior. These
are in-process unit tests against the real installed packages; they are neither
a Functions-host run nor Azure-deployed certification (host-level registration
is covered by ``tests/test_worker_registration_guard.py``).
"""

from __future__ import annotations

from collections.abc import Callable, Iterator
from dataclasses import dataclass
import importlib.metadata
import inspect
import json
import os
from pathlib import Path
import sqlite3
from typing import Any
from unittest.mock import patch

import azure.functions as func
from azure_functions_db import DbBindings, DbOut
from azure_functions_langgraph import LangGraphApp
from azure_functions_logging import with_context
from azure_functions_openapi import (
    OpenAPIRegistry,
    OpenAPISpecConfigError,
    WarningCode,
    clear_openapi_registry,
    generate_openapi_report,
    generate_openapi_spec,
    openapi,
    scan_endpoint_metadata,
)
from azure_functions_validation import validate_http
from packaging.version import Version
from pydantic import BaseModel
import pytest

from tests._isolation import load_example_module

METADATA_ATTR = "_azure_functions_metadata"
HTTP_BINDINGS = [("req", "httpTrigger"), ("$return", "http")]
JSON_HEADERS = {"content-type": "application/json"}


def _installed(distribution: str) -> Version:
    return Version(importlib.metadata.version(distribution))


@pytest.fixture(autouse=True)
def _isolated_openapi_registry() -> Iterator[None]:
    """``@openapi`` records into a process-global registry at import time."""
    clear_openapi_registry()
    yield
    clear_openapi_registry()


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------


def _function(app: func.FunctionApp, name: str) -> Any:
    # FunctionApp.get_functions() re-validates name uniqueness; call it once per lookup.
    return next(f for f in app.get_functions() if f.get_function_name() == name)


def _request(
    method: str = "POST",
    body: bytes = b"",
    route_params: dict[str, str] | None = None,
    headers: dict[str, str] | None = None,
) -> func.HttpRequest:
    return func.HttpRequest(
        method=method,
        url="https://example.invalid/api/test",
        body=body,
        headers=JSON_HEADERS if headers is None else headers,
        route_params=route_params or {},
    )


def _namespace_versions(handler: Callable[..., Any]) -> dict[str, int]:
    metadata = getattr(handler, METADATA_ATTR)
    return {name: payload["version"] for name, payload in metadata.items()}


def _spec_for(app: func.FunctionApp) -> dict[str, Any]:
    registry = OpenAPIRegistry()
    scan_endpoint_metadata(app, registry=registry)
    spec: dict[str, Any] = json.loads(json.dumps(generate_openapi_spec(registry=registry)))
    return spec


def _operation(spec: dict[str, Any], path: str, method: str) -> dict[str, Any]:
    operation: dict[str, Any] = spec["paths"][path][method]
    return operation


def _schema_properties(spec: dict[str, Any], schema: dict[str, Any]) -> set[str]:
    if "$ref" in schema:
        node: Any = spec
        for token in schema["$ref"][2:].split("/"):
            node = node[token]
        schema = node
    return set(schema.get("properties", {}))


def _response_schema(spec: dict[str, Any], operation: dict[str, Any], status: str) -> set[str]:
    schema = operation["responses"][status]["content"]["application/json"]["schema"]
    return _schema_properties(spec, schema)


def _content_type(response: func.HttpResponse) -> str:
    # Handlers that pass ``mimetype=`` expose it directly; responses built by
    # validate_http carry the type in the Content-Type header instead.
    return str(response.headers.get("Content-Type") or response.mimetype).split(";")[0]


def _json_body(response: func.HttpResponse) -> Any:
    return json.loads(response.get_body())


# ---------------------------------------------------------------------------
# Recipe-backed positive cases (P1, P2)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class RecipeCase:
    case_id: str
    recipe: str
    handler: str
    path: str
    method: str
    success_status: int
    # Parameters the worker must see and nothing else (body/path/out are hidden).
    worker_params: tuple[str, ...]
    valid_request: Callable[[], func.HttpRequest]
    expected_body: dict[str, Any]
    invalid_request: Callable[[], func.HttpRequest] | None
    response_fields: frozenset[str]


RECIPE_CASES = [
    RecipeCase(
        case_id="P1-body-validation",
        recipe="ai-and-agents/langgraph_agent",
        handler="invoke_agent",
        path="/api/agent/invoke",
        method="post",
        success_status=200,
        worker_params=("req", "context"),
        valid_request=lambda: _request(body=b'{"message": "hi", "thread_id": "t-1"}'),
        expected_body={"response": "Agent received: hi", "thread_id": "t-1"},
        invalid_request=lambda: _request(body=b'{"thread_id": "t-1"}'),
        response_fields=frozenset({"response", "thread_id"}),
    ),
    RecipeCase(
        case_id="P2-path-validation-model-return",
        recipe="apis-and-ingress/apim_function_backend",
        handler="get_catalog_item",
        path="/api/catalog/{item_id}",
        method="get",
        success_status=200,
        worker_params=("req", "context"),
        valid_request=lambda: _request(
            method="GET",
            route_params={"item_id": "sku-1"},
            headers={"x-correlation-id": "corr-1"},
        ),
        expected_body={
            "item_id": "sku-1",
            "routed_by": "azure-api-management",
            "correlation_id": "corr-1",
            "cache_status": "bypass",
        },
        invalid_request=lambda: _request(method="GET", route_params={}),
        response_fields=frozenset({"item_id", "routed_by", "correlation_id", "cache_status"}),
    ),
]
RECIPE_PARAMS = [pytest.param(case, id=case.case_id) for case in RECIPE_CASES]


@pytest.mark.parametrize("case", RECIPE_PARAMS)
def test_recipe_registers_http_binding_and_worker_signature(case: RecipeCase) -> None:
    module = load_example_module(case.recipe)
    function = _function(module.app, case.handler)
    handler = function.get_user_function()

    # (a) real SDK registration: one HTTP trigger + the $return output binding,
    # and only worker-visible parameters (validation/DB-injected ones are hidden).
    assert [(b.name, b.get_dict_repr()["type"]) for b in function.get_bindings()] == HTTP_BINDINGS
    assert tuple(inspect.signature(handler).parameters) == case.worker_params


@pytest.mark.parametrize("case", RECIPE_PARAMS)
def test_recipe_metadata_namespaces_coexist(case: RecipeCase) -> None:
    handler = _function(load_example_module(case.recipe).app, case.handler).get_user_function()

    # (b) every decorator kept its own namespace; none overwrote another.
    assert _namespace_versions(handler) == {"validation": 1, "endpoint": 1, "logging": 1}
    assert getattr(handler, METADATA_ATTR)["logging"]["context_param"] == "context"


@pytest.mark.parametrize("case", RECIPE_PARAMS)
def test_recipe_http_behavior_matches_openapi_contract(case: RecipeCase) -> None:
    module = load_example_module(case.recipe)
    handler = _function(module.app, case.handler).get_user_function()
    spec = _spec_for(module.app)
    operation = _operation(spec, case.path, case.method)

    # (c) valid request: documented status, JSON content type, exact body.
    response = handler(req=case.valid_request(), context=None)
    assert response.status_code == case.success_status
    assert _content_type(response) == "application/json"
    assert _json_body(response) == case.expected_body

    # (d) OpenAPI documents that same status with the same field set.
    assert str(case.success_status) in operation["responses"]
    assert _response_schema(spec, operation, str(case.success_status)) == case.response_fields
    assert _json_body(response).keys() == case.response_fields

    # (c)+(d) invalid request: 422 error body, and 422 is documented.
    assert case.invalid_request is not None
    invalid = handler(req=case.invalid_request(), context=None)
    assert invalid.status_code == 422
    assert _json_body(invalid)["detail"]
    assert "422" in operation["responses"]


# ---------------------------------------------------------------------------
# DB output composition (P3 supported fixture, P4 recipe order)
# ---------------------------------------------------------------------------


class ItemCreate(BaseModel):
    name: str
    category: str


class ItemResponse(BaseModel):
    id: str
    name: str


@pytest.fixture
def items_db(tmp_path: Path) -> Iterator[Path]:
    db_path = tmp_path / "items.sqlite"
    with sqlite3.connect(db_path) as connection:
        connection.execute("CREATE TABLE items (id TEXT PRIMARY KEY, name TEXT, category TEXT)")
    with patch.dict(os.environ, {"DB_URL": f"sqlite:///{db_path}"}):
        yield db_path


def _rows(db_path: Path) -> list[tuple[Any, ...]]:
    with sqlite3.connect(db_path) as connection:
        return connection.execute("SELECT id, name, category FROM items").fetchall()


def _db_fixture_app() -> func.FunctionApp:
    """``@validate_http`` above ``@db.output``: the supported order (P3).

    The handler returns an extra, undeclared field so response filtering is
    observable.
    """
    db = DbBindings()
    app = func.FunctionApp(http_auth_level=func.AuthLevel.FUNCTION)

    @app.route(route="items", methods=["POST"])
    @openapi(summary="Create item", tags=["items"])
    @with_context
    @validate_http(body=ItemCreate, response_model=ItemResponse, status_code=201)
    @db.output("out", url="%DB_URL%", table="items")
    def create_item(
        req: func.HttpRequest, body: ItemCreate, out: DbOut, context: func.Context
    ) -> dict[str, str]:
        out.set({"id": "item-1", **body.model_dump()})
        return {"id": "item-1", "name": body.name, "category": body.category}

    return app


def test_db_output_fixture_registers_worker_visible_signature_and_namespaces() -> None:
    app = _db_fixture_app()
    function = _function(app, "create_item")
    handler = function.get_user_function()

    assert [(b.name, b.get_dict_repr()["type"]) for b in function.get_bindings()] == HTTP_BINDINGS
    assert tuple(inspect.signature(handler).parameters) == ("req", "context")
    assert _namespace_versions(handler) == {"validation": 1, "endpoint": 1, "logging": 1, "db": 1}
    db_metadata = getattr(handler, METADATA_ATTR)["db"]
    assert db_metadata["bindings"][0]["parameter"] == "out"


def test_db_output_fixture_valid_request_writes_row_and_filters_response(items_db: Path) -> None:
    app = _db_fixture_app()
    handler = _function(app, "create_item").get_user_function()
    operation = _operation(_spec_for(app), "/api/items", "post")

    response = handler(req=_request(body=b'{"name": "Widget", "category": "tools"}'), context=None)

    assert response.status_code == 201
    assert _content_type(response) == "application/json"
    # "category" is returned by the handler but not declared on the response model.
    assert _json_body(response) == {"id": "item-1", "name": "Widget"}
    assert _rows(items_db) == [("item-1", "Widget", "tools")]
    assert "201" in operation["responses"]


def test_db_output_fixture_invalid_request_is_rejected_before_any_write(items_db: Path) -> None:
    app = _db_fixture_app()
    handler = _function(app, "create_item").get_user_function()
    operation = _operation(_spec_for(app), "/api/items", "post")

    missing = handler(req=_request(body=b'{"name": "Widget"}'), context=None)
    malformed = handler(req=_request(body=b"not json"), context=None)

    assert missing.status_code == 422
    assert malformed.status_code == 400
    assert _rows(items_db) == []
    assert "422" in operation["responses"]


def test_db_output_fixture_openapi_documents_response_schema() -> None:
    app = _db_fixture_app()
    spec = _spec_for(app)
    operation = _operation(spec, "/api/items", "post")

    assert _response_schema(spec, operation, "201") == {"id", "name"}
    request_schema = operation["requestBody"]["content"]["application/json"]["schema"]
    assert _schema_properties(spec, request_schema) == {"name", "category"}


DB_RECIPE = "data-and-pipelines/db_input_output"


def test_db_recipe_registration_and_metadata_hold_for_create_item() -> None:
    """P4 (a)/(b)/(d): the recipe's registration, namespaces and spec are sound."""
    module = load_example_module(DB_RECIPE)
    function = _function(module.app, "create_item")
    handler = function.get_user_function()

    assert [(b.name, b.get_dict_repr()["type"]) for b in function.get_bindings()] == HTTP_BINDINGS
    assert tuple(inspect.signature(handler).parameters) == ("req", "context")
    assert _namespace_versions(handler) == {"validation": 1, "endpoint": 1, "logging": 1, "db": 1}
    spec = _spec_for(module.app)
    operation = _operation(spec, "/api/items", "post")
    assert _response_schema(spec, operation, "201") == {"id", "name", "category", "price"}
    assert "422" in operation["responses"]


@pytest.mark.xfail(
    # Verified failing on azure-functions-db 0.9.0 and passing on the 0.8.1 floor
    # (minimum-deps lane), so the xfail is non-strict; see #503.
    condition=_installed("azure-functions-db") >= Version("0.9.0"),
    strict=False,
    raises=TypeError,
    reason="#503: db.output above with_context forwards `out` positionally into validate_http",
)
def test_db_recipe_create_item_runs_and_inserts_row(tmp_path: Path) -> None:
    """P4 (c): remove the xfail when #503 is fixed."""
    db_path = tmp_path / "recipe.sqlite"
    with sqlite3.connect(db_path) as connection:
        connection.execute(
            "CREATE TABLE items (id TEXT PRIMARY KEY, name TEXT, category TEXT, price REAL)"
        )
    with patch.dict(os.environ, {"DB_URL": f"sqlite:///{db_path}"}):
        module = load_example_module(DB_RECIPE)
        handler = _function(module.app, "create_item").get_user_function()
        response = handler(
            req=_request(body=b'{"name": "Widget", "category": "tools", "price": 9.5}'),
            context=None,
        )
        assert response.status_code == 201
    with sqlite3.connect(db_path) as connection:
        assert len(connection.execute("SELECT id FROM items").fetchall()) == 1


# ---------------------------------------------------------------------------
# Independent LangGraph endpoint producer consumed by OpenAPI (P5)
# ---------------------------------------------------------------------------


class GraphRequest(BaseModel):
    a: int


class GraphResponse(BaseModel):
    b: int


class IncrementGraph:
    def invoke(
        self, graph_input: dict[str, Any], config: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        return {"b": graph_input["a"] + 1}


def _langgraph_function_app() -> func.FunctionApp:
    app = LangGraphApp()
    app.register(
        IncrementGraph(),
        "inc",
        stream=False,
        request_model=GraphRequest,
        response_model=GraphResponse,
    )
    return app.function_app


def test_langgraph_producer_registration_and_namespaces() -> None:
    function = _function(_langgraph_function_app(), "aflg_inc_invoke")
    handler = function.get_user_function()

    assert [(b.name, b.get_dict_repr()["type"]) for b in function.get_bindings()] == HTTP_BINDINGS
    assert tuple(inspect.signature(handler).parameters) == ("req",)
    # LangGraph owns its namespace and publishes the shared endpoint contract;
    # it does not claim the validation or logging namespaces.
    assert _namespace_versions(handler) == {"langgraph": 1, "endpoint": 1}


def test_langgraph_transport_envelope_matches_openapi() -> None:
    app = _langgraph_function_app()
    handler = _function(app, "aflg_inc_invoke").get_user_function()
    spec = _spec_for(app)
    operation = _operation(spec, "/api/graphs/inc/invoke", "post")

    response = handler(_request(body=b'{"input": {"a": 1}}'))
    assert response.status_code == 200
    assert _content_type(response) == "application/json"
    assert _json_body(response) == {"output": {"b": 2}}

    # The documented 200 schema is the transport envelope wrapping the model.
    envelope = _response_schema(spec, operation, "200")
    assert envelope == {"output"}
    request_envelope = operation["requestBody"]["content"]["application/json"]["schema"]
    assert {"input"} <= _schema_properties(spec, request_envelope)

    malformed = handler(_request(body=b"not json"))
    assert malformed.status_code == 400
    assert _json_body(malformed)["detail"] == "Invalid JSON body"


# ---------------------------------------------------------------------------
# Negative cases (N1-N3)
# ---------------------------------------------------------------------------


def test_n1_validate_http_above_route_fails_loudly_instead_of_a_silent_route() -> None:
    app = func.FunctionApp()

    with pytest.raises(RuntimeError, match="applied ABOVE a binding decorator"):

        @validate_http(body=ItemCreate)
        @app.route(route="dead", methods=["POST"])
        def dead(req: func.HttpRequest, body: ItemCreate) -> dict[str, str]:  # pragma: no cover
            return {}

    # The inner @app.route already registered the bare handler: only the
    # import-time error stops this unvalidated route, so it must stay an error.
    (builder,) = app.get_functions()
    assert METADATA_ATTR not in builder.get_user_function().__dict__


def test_n2_unsupported_endpoint_version_degrades_visibly() -> None:
    app = func.FunctionApp()

    @app.route(route="skew", methods=["POST"])
    @validate_http(body=GraphRequest, response_model=GraphResponse)
    def skew(req: func.HttpRequest, body: GraphRequest) -> dict[str, int]:
        return {"b": body.a}

    handler = _function(app, "skew").get_user_function()
    getattr(handler, METADATA_ATTR)["endpoint"]["version"] = 99

    registry = OpenAPIRegistry()
    scan_endpoint_metadata(app, registry=registry)
    report = generate_openapi_report(registry=registry)

    # Observable: a structured warning, and the route is still documented
    # from its HTTP binding rather than silently disappearing from the spec.
    assert [w.code for w in report.warnings] == [WarningCode.VERSION_SKEW]
    assert "/api/skew" in report.spec["paths"]
    operation = report.spec["paths"]["/api/skew"]["post"]
    assert "requestBody" not in operation
    # Runtime validation is owned by the separate ``validation`` namespace and
    # keeps rejecting bad input even though the OpenAPI contract degraded.
    rejected = handler(req=_request(body=b"{}"))
    assert rejected.status_code == 422


@pytest.mark.skipif(
    _installed("azure-functions-openapi") < Version("0.31.0"),
    reason="request-body conflict detection between @openapi and @validate_http needs "
    "azure-functions-openapi>=0.31.0 (the declared floor, 0.30.0, does not raise)",
)
def test_n3_explicit_openapi_request_model_conflicting_with_validation_raises() -> None:
    class OtherRequest(BaseModel):
        z: int

    app = func.FunctionApp()

    @app.route(route="conflict", methods=["POST"])
    @openapi(requests=OtherRequest)
    @validate_http(body=GraphRequest, response_model=GraphResponse)
    def conflict(req: func.HttpRequest, body: GraphRequest) -> dict[str, int]:  # pragma: no cover
        return {"b": body.a}

    with pytest.raises(
        OpenAPISpecConfigError, match="Conflicting request body.*POST /api/conflict"
    ):
        _spec_for(app)
