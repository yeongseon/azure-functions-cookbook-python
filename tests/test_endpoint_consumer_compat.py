"""Consumer-level compatibility guard for public endpoint metadata producers.

Both producers are required development dependencies. Importing their public
APIs at collection time is intentional: a missing or broken producer wheel must
fail this compatibility gate instead of silently skipping it.
"""

from __future__ import annotations

import json
from typing import Any

import azure.functions as func
from azure_functions_langgraph import LangGraphApp
from azure_functions_openapi import OpenAPIRegistry, generate_openapi_spec, scan_endpoint_metadata
from azure_functions_validation import validate_http
from pydantic import BaseModel, Field
import pytest


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


class CompatGraph:
    def invoke(
        self, graph_input: dict[str, Any], config: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        return graph_input


def _validation_app(
    request_model: type[BaseModel],
    response_model: type[BaseModel],
    status_code: int = 200,
) -> func.FunctionApp:
    app = func.FunctionApp()

    @app.route(route="resource", methods=["POST"])
    @validate_http(body=request_model, response_model=response_model, status_code=status_code)
    def handler(req: func.HttpRequest, body: BaseModel) -> BaseModel:  # pragma: no cover
        return body

    return app


def _langgraph_app(
    request_model: type[BaseModel], response_model: type[BaseModel]
) -> func.FunctionApp:
    app = LangGraphApp()
    app.register(
        CompatGraph(),
        "compat",
        stream=False,
        request_model=request_model,
        response_model=response_model,
    )
    return app.function_app


def _operation_for(app: func.FunctionApp) -> tuple[dict[str, Any], dict[str, Any]]:
    registry = OpenAPIRegistry()
    scan_endpoint_metadata(app, registry=registry)
    spec = json.loads(json.dumps(generate_openapi_spec(registry=registry)))
    paths = spec["paths"]
    assert len(paths) == 1, f"expected exactly one path, got {list(paths)}"
    ((_, path_item),) = paths.items()
    assert "post" in path_item, f"POST operation not emitted: {list(path_item)}"
    return spec, path_item["post"]


def _resolve_pointer(spec: dict[str, Any], ref: str) -> dict[str, Any]:
    assert ref.startswith("#/"), f"non-local $ref not allowed: {ref}"
    node: Any = spec
    for token in ref[2:].split("/"):
        token = token.replace("~1", "/").replace("~0", "~")
        assert isinstance(node, dict) and token in node, f"unresolved $ref: {ref}"
        node = node[token]
    assert isinstance(node, dict)
    return node


def _collect_refs(value: Any) -> list[str]:
    if isinstance(value, dict):
        return [
            ref
            for key, child in value.items()
            for ref in (
                [child] if key == "$ref" and isinstance(child, str) else _collect_refs(child)
            )
        ]
    if isinstance(value, list):
        return [ref for child in value for ref in _collect_refs(child)]
    return []


def _request_schema(operation: dict[str, Any]) -> dict[str, Any]:
    schema: dict[str, Any] = operation["requestBody"]["content"]["application/json"]["schema"]
    return schema


def _success_schema(operation: dict[str, Any], status: int) -> dict[str, Any]:
    schema: dict[str, Any] = operation["responses"][str(status)]["content"]["application/json"][
        "schema"
    ]
    return schema


def _resolved(schema: dict[str, Any], spec: dict[str, Any]) -> dict[str, Any]:
    return _resolve_pointer(spec, schema["$ref"]) if "$ref" in schema else schema


def _transport_member(schema: dict[str, Any], spec: dict[str, Any], member: str) -> dict[str, Any]:
    envelope = _resolved(schema, spec)
    return _resolved(envelope["properties"][member], spec)


def _field_names(schema: dict[str, Any], spec: dict[str, Any]) -> set[str]:
    return set(_resolved(schema, spec).get("properties", {}))


def _required_names(schema: dict[str, Any], spec: dict[str, Any]) -> set[str]:
    return set(_resolved(schema, spec).get("required", []))


def _expected_field_names(model: type[BaseModel]) -> set[str]:
    return {field.alias or name for name, field in model.model_fields.items()}


@pytest.mark.parametrize("request_model, response_model", MODEL_CASES)
def test_public_producer_metadata_is_consumable(
    request_model: type[BaseModel], response_model: type[BaseModel]
) -> None:
    validation_spec, validation_op = _operation_for(_validation_app(request_model, response_model))
    langgraph_spec, langgraph_op = _operation_for(_langgraph_app(request_model, response_model))

    validation_request = _request_schema(validation_op)
    langgraph_request = _transport_member(_request_schema(langgraph_op), langgraph_spec, "input")
    validation_response = _success_schema(validation_op, 200)
    langgraph_response = _transport_member(
        _success_schema(langgraph_op, 200), langgraph_spec, "output"
    )

    expected_request = _expected_field_names(request_model)
    expected_response = _expected_field_names(response_model)
    assert _field_names(validation_request, validation_spec) == expected_request
    assert _field_names(langgraph_request, langgraph_spec) == expected_request
    assert _required_names(validation_request, validation_spec) == _required_names(
        langgraph_request, langgraph_spec
    )
    assert validation_op["requestBody"]["required"] == langgraph_op["requestBody"]["required"]
    assert _field_names(validation_response, validation_spec) == expected_response
    assert _field_names(langgraph_response, langgraph_spec) == expected_response
    assert "422" in validation_op["responses"]
    assert "422" not in langgraph_op["responses"]

    for spec, operation in (
        (validation_spec, validation_op),
        (langgraph_spec, langgraph_op),
    ):
        for ref in _collect_refs(operation):
            _resolve_pointer(spec, ref)


def test_non_default_validation_status_and_langgraph_transport_status_are_consumed() -> None:
    validation_spec, validation_op = _operation_for(
        _validation_app(SimpleRequest, SimpleResponse, status_code=201)
    )
    langgraph_spec, langgraph_op = _operation_for(_langgraph_app(SimpleRequest, SimpleResponse))

    assert "201" in validation_op["responses"]
    assert "200" in langgraph_op["responses"]
    validation_response = _success_schema(validation_op, 201)
    langgraph_response = _transport_member(
        _success_schema(langgraph_op, 200), langgraph_spec, "output"
    )
    assert _field_names(validation_response, validation_spec) == _field_names(
        langgraph_response, langgraph_spec
    )
