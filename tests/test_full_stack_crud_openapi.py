from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from azure_functions_openapi import (
    clear_openapi_registry,
    get_openapi_json,
    scan_endpoint_metadata,
)
import pytest

from tests._isolation import load_example_module

EXAMPLE = "apis-and-ingress/full_stack_crud_api"


@pytest.fixture
def full_stack_spec(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> dict[str, Any]:
    # Given: the full-stack recipe uses an isolated SQLite database
    monkeypatch.setenv("DB_URL", f"sqlite:///{tmp_path / 'items.db'}")
    clear_openapi_registry()
    module = load_example_module(EXAMPLE)

    # When: validation and explicit endpoint metadata are converged
    scan_endpoint_metadata(module.app)

    # Then: the complete document can be generated without a Functions host
    document: dict[str, Any] = json.loads(
        get_openapi_json(title="Full Stack CRUD API", version="1.0.0")
    )
    return document


def test_full_stack_crud_paths_are_documented(full_stack_spec: dict[str, Any]) -> None:
    assert set(full_stack_spec["paths"]) >= {"/api/items", "/api/items/{id}"}
    assert set(full_stack_spec["paths"]["/api/items"]) >= {"get", "post"}
    assert set(full_stack_spec["paths"]["/api/items/{id}"]) >= {"get", "put", "delete"}


def test_full_stack_crud_response_contracts_are_documented(
    full_stack_spec: dict[str, Any],
) -> None:
    paths = full_stack_spec["paths"]

    assert set(paths["/api/items"]["get"]["responses"]) == {"200", "422"}
    assert set(paths["/api/items"]["post"]["responses"]) == {"201", "422"}
    assert set(paths["/api/items/{id}"]["get"]["responses"]) == {"200", "404"}
    assert set(paths["/api/items/{id}"]["put"]["responses"]) == {"200", "404", "422"}
    assert set(paths["/api/items/{id}"]["delete"]["responses"]) == {"204", "404"}


def test_full_stack_crud_models_are_documented(full_stack_spec: dict[str, Any]) -> None:
    paths = full_stack_spec["paths"]
    list_schema = paths["/api/items"]["get"]["responses"]["200"]["content"]["application/json"][
        "schema"
    ]
    create_request = paths["/api/items"]["post"]["requestBody"]["content"]["application/json"][
        "schema"
    ]
    create_response = paths["/api/items"]["post"]["responses"]["201"]["content"][
        "application/json"
    ]["schema"]
    get_response = paths["/api/items/{id}"]["get"]["responses"]["200"]["content"][
        "application/json"
    ]["schema"]
    update_request = paths["/api/items/{id}"]["put"]["requestBody"]["content"]["application/json"][
        "schema"
    ]
    update_response = paths["/api/items/{id}"]["put"]["responses"]["200"]["content"][
        "application/json"
    ]["schema"]

    assert set(list_schema["properties"]) >= {"page", "page_size", "total", "items", "next_link"}
    assert set(create_request["properties"]) == {"name", "description", "price"}
    response_properties = {
        "id",
        "name",
        "description",
        "price",
        "created_at",
        "updated_at",
    }
    assert set(create_response["properties"]) >= response_properties
    assert get_response == {"$ref": "#/components/schemas/ItemResponse"}
    assert set(update_request["properties"]) == {"name", "description", "price"}
    assert set(update_response["properties"]) >= response_properties
