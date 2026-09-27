"""Spec-level proof for the OpenAPI inference recipes.

These tests are the read-side contract for issue #573. They import each recipe,
run :func:`scan_endpoint_metadata` over its ``FunctionApp`` (the same discovery
path the cookbook uses in production), and assert the generated OpenAPI ``200``
schema proves the documented behavior:

* ``openapi_inference`` — the 200 schema is *inferred* from the return
  annotation (registry flag ``_response_inferred`` is ``True``).
* ``openapi_supersedes`` — a validation ``response_model`` *supersedes* the
  inferred annotation (``_response_inferred`` is ``False`` and the richer model
  wins the 200 schema).
"""

from __future__ import annotations

import json
import logging
from typing import Any

import azure.functions as func
import pytest

from azure_functions_openapi import (
    clear_openapi_registry,
    get_openapi_json,
    scan_endpoint_metadata,
)
from azure_functions_openapi.decorator import get_openapi_registry

from tests._isolation import load_example_module

INFERENCE_EXAMPLE = "apis-and-ingress/openapi_inference"
SUPERSEDES_EXAMPLE = "apis-and-ingress/openapi_supersedes"


def _spec_and_registry(example: str) -> tuple[dict[str, Any], dict[str, Any]]:
    clear_openapi_registry()
    module = load_example_module(example)
    scan_endpoint_metadata(module.app)
    spec: dict[str, Any] = json.loads(get_openapi_json())
    registry: dict[str, Any] = dict(get_openapi_registry())
    return spec, registry


def _get_operation(spec: dict[str, Any], path: str) -> dict[str, Any]:
    paths = spec["paths"]
    assert isinstance(paths, dict)
    path_item = paths[path]
    assert isinstance(path_item, dict)
    operation: dict[str, Any] = path_item["get"]
    assert isinstance(operation, dict)
    return operation


def _success_schema(operation: dict[str, Any]) -> dict[str, Any]:
    schema = operation["responses"]["200"]["content"]["application/json"]["schema"]
    assert isinstance(schema, dict)
    return schema


def _resolve_schema(spec: dict[str, Any], schema: dict[str, Any]) -> dict[str, Any]:
    ref = schema.get("$ref")
    if ref is None:
        return schema
    name = ref.split("/")[-1]
    resolved = spec["components"]["schemas"][name]
    assert isinstance(resolved, dict)
    return resolved


def test_inference_recipe_infers_response_from_return_annotation() -> None:
    spec, registry = _spec_and_registry(INFERENCE_EXAMPLE)
    operation = _get_operation(spec, "/api/openapi/inference/greeting")

    assert operation.get("summary") == "Return-type inference demo"
    assert operation.get("description") == (
        "The 200 response schema is inferred from the return annotation."
    )

    schema = _resolve_schema(spec, _success_schema(operation))
    assert set(schema.get("properties", {})) == {"message", "source"}

    assert registry["inferred_greeting"]["_response_inferred"] is True


def test_supersedes_recipe_prefers_validation_response_model() -> None:
    spec, registry = _spec_and_registry(SUPERSEDES_EXAMPLE)
    operation = _get_operation(spec, "/api/openapi/supersedes/greeting")

    assert operation.get("summary") == "Validation supersedes inference"

    schema = _resolve_schema(spec, _success_schema(operation))
    assert set(schema.get("properties", {})) == {"message", "source", "precedence"}, (
        "200 schema must come from the validation response_model, not the "
        "single-field return annotation"
    )

    assert registry["supersedes_greeting"]["_response_inferred"] is False


def test_supersedes_beats_the_bare_inferred_annotation() -> None:
    """The winning schema must be strictly richer than the return annotation.

    The handler is annotated ``-> InferredGreetingResponse`` (only ``message``);
    if inference had won, ``source`` and ``precedence`` would be absent. Their
    presence is the proof that validation superseded inference.
    """
    spec, _ = _spec_and_registry(SUPERSEDES_EXAMPLE)
    operation = _get_operation(spec, "/api/openapi/supersedes/greeting")
    schema = _resolve_schema(spec, _success_schema(operation))
    properties = schema.get("properties", {})
    assert "source" in properties
    assert "precedence" in properties


@pytest.mark.parametrize(
    ("example", "handler_name", "route"),
    [
        (INFERENCE_EXAMPLE, "inferred_greeting", "/api/openapi/inference/greeting"),
        (SUPERSEDES_EXAMPLE, "supersedes_greeting", "/api/openapi/supersedes/greeting"),
    ],
)
def test_recipe_handler_actually_serves_a_request(
    caplog: pytest.LogCaptureFixture, example: str, handler_name: str, route: str
) -> None:
    """Invoke the handler for real; the registry tests never execute one.

    INFO must be enabled explicitly. ``logger.info`` only builds a ``LogRecord``
    when the level passes, so a handler that corrupts the record -- for example
    by passing a reserved key through ``extra`` -- raises in production and
    stays silent in a default-level test run.
    """
    clear_openapi_registry()
    module = load_example_module(example)
    handler = getattr(module, handler_name)

    request = func.HttpRequest(method="GET", url=route, body=b"", params={"name": "Ada"})

    with caplog.at_level(logging.INFO):
        response = handler(request)

    assert response.status_code == 200
    assert json.loads(response.get_body())["message"] == "Hello, Ada!"
