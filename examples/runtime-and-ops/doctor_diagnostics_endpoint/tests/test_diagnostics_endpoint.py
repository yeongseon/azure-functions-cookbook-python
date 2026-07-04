from __future__ import annotations

import json

import azure.functions as func

from app.functions import diagnostics as diagnostics_module


def _make_request(url: str = "http://localhost/api/health") -> func.HttpRequest:
    return func.HttpRequest(method="GET", url=url, body=None)


def test_get_health_returns_healthy_json() -> None:
    response = diagnostics_module.get_health(_make_request())
    assert response.status_code == 200
    assert response.mimetype == "application/json"
    assert json.loads(response.get_body()) == {"status": "healthy"}
