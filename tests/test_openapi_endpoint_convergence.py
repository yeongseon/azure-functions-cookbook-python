"""Convergence guard: the OpenAPI spec must stay identical after producers
switch to the ``endpoint`` metadata namespace.

The cookbook is the dogfood integration point where ``azure-functions-validation``
(producer) and ``azure-functions-openapi`` (consumer) run together. This test
imports a recipe that uses ``@validate_http`` + ``@openapi``, generates the
OpenAPI spec in-process (no ``func`` host required), and asserts it matches a
committed golden snapshot. If the ``endpoint`` convergence ever changes the
generated spec, this test fails loudly.

Regenerate the snapshot intentionally with::

    hatch run python -m tests.regen_openapi_snapshot

See yeongseon/azure-functions-python-cookbook#119.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from azure_functions_openapi import (
    clear_openapi_registry,
    get_openapi_json,
    scan_endpoint_metadata,
)

from tests._isolation import load_example_module

# Recipe that exercises both producers/consumer:
#   @app.route + @openapi + @validate_http(path=..., response_model=...)
EXAMPLE = "apis-and-ingress/apim_function_backend"

SNAPSHOT_PATH = Path(__file__).resolve().parent / "data" / "apim_function_backend.openapi.json"


def _generate_spec() -> dict[str, object]:
    """Generate the OpenAPI spec for ``EXAMPLE`` from a clean registry.

    Discovery is exercised end-to-end: after importing the recipe module we run
    :func:`scan_endpoint_metadata` over its ``FunctionApp`` so that the
    ``@validate_http`` endpoint metadata (path model, response model) is folded
    into the registry before the spec is compiled. Without this scan the spec
    would only reflect the literal ``@openapi`` fields, which is exactly the
    false-positive convergence the guard used to have (#135).
    """
    clear_openapi_registry()
    module = load_example_module(EXAMPLE)
    scan_endpoint_metadata(module.app)
    spec: dict[str, object] = json.loads(get_openapi_json())
    return spec


def _catalog_get_operation(spec: dict[str, object]) -> dict[str, Any]:
    """Return the GET operation object for the catalog recipe path."""
    paths = spec["paths"]
    assert isinstance(paths, dict)
    path_item = paths["/api/catalog/{item_id}"]
    assert isinstance(path_item, dict)
    operation: dict[str, Any] = path_item["get"]
    assert isinstance(operation, dict)
    return operation


def test_spec_matches_committed_snapshot() -> None:
    """The generated spec must equal the committed golden snapshot.

    This is the end-to-end proof that the ``endpoint`` metadata namespace
    produces the expected OpenAPI output. Any drift is an intentional-change
    signal, not a silent regression.
    """
    expected = json.loads(SNAPSHOT_PATH.read_text(encoding="utf-8"))
    actual = _generate_spec()
    assert actual == expected, (
        "Generated OpenAPI spec drifted from the committed snapshot. "
        "If this change is intentional, regenerate "
        f"{SNAPSHOT_PATH.relative_to(SNAPSHOT_PATH.parents[2])}."
    )


def test_spec_generation_is_deterministic() -> None:
    """Regenerating the spec twice yields byte-identical output."""
    first = json.dumps(_generate_spec(), sort_keys=True)
    second = json.dumps(_generate_spec(), sort_keys=True)
    assert first == second


def test_path_parameter_is_discovered_from_endpoint_metadata() -> None:
    """The ``item_id`` path parameter must come from the scanned path model.

    ``@openapi`` alone never declares ``item_id``; it only reaches the spec
    because :func:`scan_endpoint_metadata` folds ``CatalogPath`` from the
    ``@validate_http`` endpoint metadata into the registry (#135).
    """
    operation = _catalog_get_operation(_generate_spec())
    parameters = operation.get("parameters", [])
    assert isinstance(parameters, list)
    path_params = {
        p["name"]: p
        for p in parameters
        if isinstance(p, dict) and p.get("in") == "path"
    }
    assert "item_id" in path_params, (
        "item_id path parameter missing: endpoint-metadata discovery did not run"
    )
    assert path_params["item_id"].get("required") is True
    assert path_params["item_id"]["schema"]["type"] == "string"


def test_success_response_uses_scanned_response_model() -> None:
    """The 200 body must reflect ``CatalogResponse`` from endpoint metadata.

    Before discovery the 200 body was a generic ``{"type": "object"}``; after
    :func:`scan_endpoint_metadata` runs it carries the concrete
    ``CatalogResponse`` fields (#135).
    """
    operation = _catalog_get_operation(_generate_spec())
    schema = operation["responses"]["200"]["content"]["application/json"]["schema"]
    assert isinstance(schema, dict)
    properties = schema.get("properties")
    assert isinstance(properties, dict), (
        "200 body is not a concrete object schema: response model was not scanned"
    )
    assert set(properties) >= {
        "item_id",
        "routed_by",
        "correlation_id",
        "cache_status",
    }


def test_validation_error_response_is_present() -> None:
    """A 422 validation-error response surfaces from endpoint metadata.

    ``azure-functions-validation`` >= 0.10 emits a 422 validation-error
    response in the ``endpoint`` namespace (#286); ``scan_endpoint_metadata``
    folds it into the OpenAPI spec. This is the read side of the convergence
    contract -- the deferred/xfail placeholder was removed once validation
    0.10.0 shipped the emit (#135).
    """
    operation = _catalog_get_operation(_generate_spec())
    responses = operation["responses"]
    assert "422" in responses, (
        "422 validation-error response missing: endpoint-metadata discovery did "
        "not surface the validation error contract"
    )
    schema = responses["422"]["content"]["application/json"]["schema"]
    assert isinstance(schema, dict)
    assert "detail" in schema.get("properties", {}), (
        "422 body is missing the validation-error 'detail' field"
    )
