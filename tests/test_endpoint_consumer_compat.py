"""Consumer-level compatibility guard for the shared ``endpoint`` metadata namespace.

The Azure Functions Python DX Toolkit has two independent producers of the
``endpoint`` namespace payload (schema version 1):

* ``azure_functions_validation._endpoint.build_endpoint_metadata`` — reads a
  pipeline ``config`` (``body``/``query``/``path``/``headers``/``response_model``/
  ``success_status_code``).
* ``azure_functions_langgraph._endpoint.build_endpoint_metadata`` — takes an
  explicit ``request_model``/``response_model``/``parameters``/
  ``success_status_code``.

The real cross-package promise is **not** that the two producers emit
byte-identical payloads. ``azure-functions-validation``'s own SPEC
(``docs/METADATA_SPEC.md``) states that its Pydantic canonicalization
(``by_alias``/``ref_template``/``mode``) is *validation-specific* and that the
generic convention only requires the semantic payload shape; the ``"422"``
validation-error response is likewise validation-specific. Enforcing
byte-equality between the two private builders would elevate that
implementation detail into a bidirectional contract the convention explicitly
disclaims (and would break on harmless Pydantic-version schema-shape changes).

Instead, this test pins the promise the ecosystem actually makes: **metadata
independently emitted by either producer, when fed through the real
``azure-functions-openapi`` consumer, yields a valid and semantically
equivalent OpenAPI operation.** Equivalence is asserted at the client-visible
level — same request-body fields, same required-ness, same success-response
fields, all ``$ref``s resolvable — while tolerating producer-specific additive
metadata (e.g. validation's 422). Byte-level schema shape is intentionally NOT
compared.

The cookbook is the dogfood integration point where both producers and the
consumer are import-available, so it is the right place to hold this contract.

See yeongseon/azure-functions-cookbook-python#149.
"""

from __future__ import annotations

import json
from types import SimpleNamespace
from typing import Any

import azure.functions as func
from pydantic import BaseModel, Field
import pytest

# Both endpoint-metadata producers are optional cross-package dependencies. In
# particular ``azure-functions-langgraph`` may be published as an empty wheel
# (see yeongseon/azure-functions-langgraph-python#311), in which case the
# distribution installs but exposes no importable modules. Skip the whole module
# honestly when either producer or the consumer is unavailable, rather than
# failing collection; the assertions run for real the moment a fixed wheel is
# present. These tests exercise only external packages, so skipping does not
# affect this repo's own coverage.
langgraph_endpoint = pytest.importorskip("azure_functions_langgraph._endpoint")
validation_endpoint = pytest.importorskip("azure_functions_validation._endpoint")

from azure_functions_openapi import (  # noqa: E402
    clear_openapi_registry,
    generate_openapi_spec,
    scan_endpoint_metadata,
)
from azure_functions_openapi.registry import OpenAPIRegistry  # noqa: E402

langgraph_build = langgraph_endpoint.build_endpoint_metadata
validation_build = validation_endpoint.build_endpoint_metadata


# --------------------------------------------------------------------------- #
# Models — simple, nested ($defs/$ref), and aliased (by_alias canonicalization)
# --------------------------------------------------------------------------- #
class SimpleRequest(BaseModel):
    name: str
    count: int = 0


class SimpleResponse(BaseModel):
    message: str
    status: str = "ok"


class Nested(BaseModel):
    label: str
    value: int


class NestedRequest(BaseModel):
    title: str
    nested: Nested


class NestedResponse(BaseModel):
    result: Nested
    total: int


class AliasRequest(BaseModel):
    user_name: str = Field(alias="userName")
    is_active: bool = Field(default=True, alias="isActive")


class AliasResponse(BaseModel):
    display_name: str = Field(alias="displayName")


MODEL_CASES = [
    pytest.param(SimpleRequest, SimpleResponse, id="simple"),
    pytest.param(NestedRequest, NestedResponse, id="nested"),
    pytest.param(AliasRequest, AliasResponse, id="alias"),
]


# --------------------------------------------------------------------------- #
# Producers
# --------------------------------------------------------------------------- #
def _validation_payload(
    request_model: type[BaseModel],
    response_model: type[BaseModel],
    success_status_code: int = 200,
) -> dict[str, Any]:
    """Run the validation builder with a minimal config stub.

    Only ``body`` is set (no query/path/header models), so the validation-only
    ``parameters`` do not appear and the comparison focuses on the shared
    request-body/response semantics. The 422 the builder adds for the body
    model is tolerated as producer-specific additive metadata.
    """
    config = SimpleNamespace(
        body=request_model,
        query=None,
        path=None,
        headers=None,
        response_model=response_model,
        success_status_code=success_status_code,
    )
    return dict(validation_build(config))


def _langgraph_payload(
    request_model: type[BaseModel],
    response_model: type[BaseModel],
    success_status_code: int = 200,
) -> dict[str, Any]:
    return dict(
        langgraph_build(
            request_model=request_model,
            response_model=response_model,
            parameters=None,
            success_status_code=success_status_code,
        )
    )


# --------------------------------------------------------------------------- #
# Consumer plumbing — feed a payload through the real openapi consumer
# --------------------------------------------------------------------------- #
def _operation_for(payload: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    """Register a route carrying ``payload`` and return ``(spec, operation)``.

    Builds a fresh ``FunctionApp`` with a single POST route, attaches the
    ``endpoint`` payload under the toolkit convention attribute, scans it into an
    isolated registry via the real consumer, and compiles the OpenAPI spec.
    Returns the whole spec plus the single emitted operation object.
    """
    clear_openapi_registry()
    registry = OpenAPIRegistry()

    app = func.FunctionApp()

    def handler(req: func.HttpRequest) -> func.HttpResponse:  # pragma: no cover
        return func.HttpResponse(status_code=200)

    # Attach the endpoint payload to the *user* function before registration:
    # ``@app.route`` returns a ``FunctionBuilder`` wrapping this object, and the
    # consumer reads the convention attribute off the underlying user handler.
    handler._azure_functions_metadata = {"endpoint": payload}  # type: ignore[attr-defined]
    app.route(route="resource", methods=["POST"])(handler)

    scan_endpoint_metadata(app, registry=registry)
    spec = generate_openapi_spec(registry=registry)

    # Round-trip proves the whole spec (and thus the producer payload) is
    # JSON-serializable — part of the convention's contract.
    spec = json.loads(json.dumps(spec))

    paths = spec["paths"]
    assert len(paths) == 1, f"expected exactly one path, got {list(paths)}"
    ((_, path_item),) = paths.items()
    assert "post" in path_item, f"POST operation not emitted: {list(path_item)}"
    return spec, path_item["post"]


def _resolve_pointer(spec: dict[str, Any], ref: str) -> Any:
    """Resolve a local JSON pointer (``#/a/b/c``) against the whole spec."""
    assert ref.startswith("#/"), f"non-local $ref not allowed: {ref}"
    node: Any = spec
    for token in ref[2:].split("/"):
        token = token.replace("~1", "/").replace("~0", "~")
        assert isinstance(node, dict) and token in node, f"unresolved $ref: {ref}"
        node = node[token]
    return node


def _collect_refs(obj: Any) -> list[str]:
    """Recursively collect every ``$ref`` string in a JSON structure."""
    refs: list[str] = []
    if isinstance(obj, dict):
        for key, value in obj.items():
            if key == "$ref" and isinstance(value, str):
                refs.append(value)
            else:
                refs.extend(_collect_refs(value))
    elif isinstance(obj, list):
        for item in obj:
            refs.extend(_collect_refs(item))
    return refs


def _assert_all_refs_resolve(spec: dict[str, Any], operation: dict[str, Any]) -> None:
    for ref in _collect_refs(operation):
        _resolve_pointer(spec, ref)


def _request_schema(operation: dict[str, Any]) -> dict[str, Any] | None:
    body = operation.get("requestBody")
    if body is None:
        return None
    schema: dict[str, Any] = body["content"]["application/json"]["schema"]
    return schema


def _success_schema(operation: dict[str, Any], status: int) -> dict[str, Any]:
    schema: dict[str, Any] = operation["responses"][str(status)]["content"][
        "application/json"
    ]["schema"]
    return schema


def _field_names(schema: dict[str, Any], spec: dict[str, Any]) -> set[str]:
    """Client-visible field names of a (possibly ``$ref``-headed) object schema."""
    if "$ref" in schema:
        schema = _resolve_pointer(spec, schema["$ref"])
    return set(schema.get("properties", {}))


def _required_names(schema: dict[str, Any], spec: dict[str, Any]) -> set[str]:
    if "$ref" in schema:
        schema = _resolve_pointer(spec, schema["$ref"])
    return set(schema.get("required", []))

def _expected_field_names(model: type[BaseModel]) -> set[str]:
    """Client-visible field names for a model, honoring ``by_alias=True``."""
    return {field.alias or name for name, field in model.model_fields.items()}


# --------------------------------------------------------------------------- #
# Per-producer validity: each producer's output must be consumable
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize("request_model, response_model", MODEL_CASES)
def test_validation_metadata_is_consumable(
    request_model: type[BaseModel], response_model: type[BaseModel]
) -> None:
    spec, op = _operation_for(_validation_payload(request_model, response_model))

    request = _request_schema(op)
    assert request is not None, "validation request body was not consumed"
    assert _field_names(request, spec) == _expected_field_names(request_model)
    assert "200" in op["responses"], "validation success response missing"
    assert _field_names(_success_schema(op, 200), spec) == _expected_field_names(response_model)
    _assert_all_refs_resolve(spec, op)

    # Producer-specific additive metadata: validation documents a 422 for the
    # body model. It is allowed (not required of the convention) and must itself
    # be a well-formed, resolvable response.
    assert "422" in op["responses"], "validation should surface its 422 contract"


@pytest.mark.parametrize("request_model, response_model", MODEL_CASES)
def test_langgraph_metadata_is_consumable(
    request_model: type[BaseModel], response_model: type[BaseModel]
) -> None:
    spec, op = _operation_for(_langgraph_payload(request_model, response_model))

    request = _request_schema(op)
    assert request is not None, "langgraph request body was not consumed"
    assert _field_names(request, spec) == _expected_field_names(request_model)
    assert "200" in op["responses"], "langgraph success response missing"
    assert _field_names(_success_schema(op, 200), spec) == _expected_field_names(response_model)
    _assert_all_refs_resolve(spec, op)

    # langgraph does not emit a 422; the convention does not require one. Its
    # absence must be tolerated (this is the additive-metadata asymmetry).
    assert "422" not in op["responses"], "langgraph unexpectedly emitted a 422"


# --------------------------------------------------------------------------- #
# Cross-producer semantic equivalence (NOT byte equality)
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize("request_model, response_model", MODEL_CASES)
def test_producers_are_semantically_equivalent(
    request_model: type[BaseModel], response_model: type[BaseModel]
) -> None:
    """Both producers must yield the same client-visible operation shape.

    Equivalence is asserted at the level a consumer/client cares about — the
    request-body field set and required-ness, and the success-response field
    set — for the same models. Byte-level schema shape and producer-specific
    additive responses (validation's 422) are intentionally NOT compared.
    """
    v_spec, v_op = _operation_for(_validation_payload(request_model, response_model))
    l_spec, l_op = _operation_for(_langgraph_payload(request_model, response_model))

    v_req = _request_schema(v_op)
    l_req = _request_schema(l_op)
    assert v_req is not None and l_req is not None

    assert _field_names(v_req, v_spec) == _field_names(l_req, l_spec), (
        "request-body field sets diverged between validation and langgraph"
    )
    assert _required_names(v_req, v_spec) == _required_names(l_req, l_spec), (
        "request-body required fields diverged between producers"
    )
    assert v_op["requestBody"]["required"] == l_op["requestBody"]["required"], (
        "request-body required-ness diverged between producers"
    )

    assert _field_names(_success_schema(v_op, 200), v_spec) == _field_names(
        _success_schema(l_op, 200), l_spec
    ), "success-response field sets diverged between producers"


def test_non_default_success_status_is_consumed_by_both() -> None:
    """A non-default success status keys the response identically in both."""
    v_spec, v_op = _operation_for(
        _validation_payload(SimpleRequest, SimpleResponse, success_status_code=201)
    )
    l_spec, l_op = _operation_for(
        _langgraph_payload(SimpleRequest, SimpleResponse, success_status_code=201)
    )
    assert "201" in v_op["responses"], "validation did not key the 201 response"
    assert "201" in l_op["responses"], "langgraph did not key the 201 response"
    assert _field_names(_success_schema(v_op, 201), v_spec) == _field_names(
        _success_schema(l_op, 201), l_spec
    )
