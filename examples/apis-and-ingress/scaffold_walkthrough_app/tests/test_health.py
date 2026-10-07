from __future__ import annotations

import json
from types import SimpleNamespace

import azure.functions as func

from app.functions.health import health


def test_health_returns_ok_status() -> None:
    request = func.HttpRequest(
        method="GET",
        url="http://localhost/api/health",
        params={},
        body=b"",
    )

    context = SimpleNamespace(invocation_id="test", function_name="health", trace_context=None)
    response = health(request, context)

    assert response.status_code == 200
    body = json.loads(response.get_body())
    assert body == {"status": "ok"}
