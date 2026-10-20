"""Regression coverage for #363: accept the MCP initialized notification
over HTTP.

The MCP example advertised protocol version 2025-03-26 and successfully
answered initialize, but rejected the next required message:
notifications/initialized. It fell through to the unknown-method branch
and returned HTTP 404 with an id: null JSON-RPC error, instead of the
protocol's required HTTP 202 with an empty body.

Drives the full real registered HTTP handler through the complete
initialize -> notifications/initialized -> tools/list sequence; no MCP
SDK or model-service dependency and no network calls are involved.
"""

from __future__ import annotations

from collections.abc import Callable
import json

import azure.functions as func

from tests._isolation import load_example_module

EXAMPLE_PATH = "ai-and-agents/mcp_server_example"

McpHandler = Callable[[func.HttpRequest], func.HttpResponse]


def _mcp_request(message: dict[str, object]) -> func.HttpRequest:
    return func.HttpRequest(
        method="POST",
        url="http://localhost/api/mcp",
        params={},
        headers={
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream",
        },
        body=json.dumps(message).encode(),
    )


def _mcp_handler() -> McpHandler:
    module = load_example_module(EXAMPLE_PATH)
    handler: McpHandler = next(
        f.get_user_function() for f in module.app.get_functions() if f.get_function_name() == "mcp"
    )
    return handler


def test_initialized_notification_returns_empty_202() -> None:
    handler = _mcp_handler()

    response = handler(_mcp_request({"jsonrpc": "2.0", "method": "notifications/initialized"}))

    assert response.status_code == 202
    assert response.get_body() == b""


def test_full_initialization_sequence_succeeds() -> None:
    handler = _mcp_handler()

    initialize_response = handler(
        _mcp_request(
            {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2025-03-26",
                    "capabilities": {},
                    "clientInfo": {"name": "test-client", "version": "1.0"},
                },
            }
        )
    )
    assert initialize_response.status_code == 200
    initialize_body = json.loads(initialize_response.get_body())
    assert initialize_body["result"]["protocolVersion"] == "2025-03-26"

    initialized_response = handler(
        _mcp_request({"jsonrpc": "2.0", "method": "notifications/initialized"})
    )
    assert initialized_response.status_code == 202
    assert initialized_response.get_body() == b""

    tools_response = handler(_mcp_request({"jsonrpc": "2.0", "id": 2, "method": "tools/list"}))
    assert tools_response.status_code == 200
    tools_body = json.loads(tools_response.get_body())
    assert tools_body["id"] == 2
    assert len(tools_body["result"]["tools"]) == 2


def test_ordinary_requests_still_return_json_bodies_with_preserved_ids() -> None:
    handler = _mcp_handler()

    response = handler(_mcp_request({"jsonrpc": "2.0", "id": 42, "method": "tools/list"}))

    assert response.status_code == 200
    body = json.loads(response.get_body())
    assert body["id"] == 42
    assert "result" in body


def test_unsupported_method_still_returns_404_json_rpc_error() -> None:
    handler = _mcp_handler()

    response = handler(_mcp_request({"jsonrpc": "2.0", "id": 7, "method": "notifications/bogus"}))

    assert response.status_code == 404
    body = json.loads(response.get_body())
    assert body["error"]["code"] == -32601
