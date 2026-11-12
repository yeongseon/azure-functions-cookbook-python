from __future__ import annotations

from pathlib import Path

import pytest
import requests

from tests.e2e.conftest import run_func_host

pytestmark = [pytest.mark.e2e, pytest.mark.compat]
EXAMPLE = "apis-and-ingress/full_stack_crud_api"


@pytest.mark.package_validation
def test_validation_accepts_valid_body_and_rejects_invalid_body() -> None:
    with run_func_host(EXAMPLE) as base_url:
        valid = requests.post(
            f"{base_url}/api/items",
            json={"name": "Widget", "description": "Runtime gate", "price": 9.99},
            timeout=10,
        )
        invalid = requests.post(
            f"{base_url}/api/items",
            json={"name": "", "description": "", "price": -1},
            timeout=10,
        )

    assert valid.status_code == 201
    assert invalid.status_code == 422
    assert "detail" in invalid.json()


@pytest.mark.package_logging
def test_logging_configuration_survives_live_invocation() -> None:
    with run_func_host(EXAMPLE) as base_url:
        response = requests.get(f"{base_url}/api/items", timeout=10)

    assert response.status_code == 200


@pytest.mark.package_openapi
def test_openapi_document_and_documented_endpoint_are_live() -> None:
    with run_func_host(EXAMPLE) as base_url:
        document = requests.get(f"{base_url}/api/openapi.json", timeout=10)
        endpoint = requests.get(f"{base_url}/api/items", timeout=10)

    assert document.status_code == 200
    assert "/api/items" in document.json()["paths"]
    assert endpoint.status_code == 200


@pytest.mark.package_db
def test_db_item_round_trips_through_the_host(tmp_path: Path) -> None:
    """azure-functions-db: a created row is read back through the Functions host."""
    db_url = f"sqlite:///{tmp_path / 'items.db'}"
    with run_func_host(EXAMPLE, env_vars={"DB_URL": db_url}) as base_url:
        created = requests.post(
            f"{base_url}/api/items",
            json={"name": "Round trip", "description": "DB gate", "price": 1.5},
            timeout=10,
        )
        item_id = created.json()["id"]
        fetched = requests.get(f"{base_url}/api/items/{item_id}", timeout=10)

    assert created.status_code == 201
    assert fetched.status_code == 200
    assert fetched.json()["name"] == "Round trip"
