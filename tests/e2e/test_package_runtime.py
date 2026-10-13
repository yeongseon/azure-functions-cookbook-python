from __future__ import annotations

import pytest
import requests

from tests.e2e.conftest import run_func_host

pytestmark = pytest.mark.e2e
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
