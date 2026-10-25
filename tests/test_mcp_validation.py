from __future__ import annotations

from collections.abc import Callable
import json

import azure.functions as func
import pytest

from tests._isolation import load_example_module

Json = None | bool | int | float | str | list["Json"] | dict[str, "Json"]


@pytest.fixture
def mcp_handler() -> Callable[[func.HttpRequest], func.HttpResponse]:
    module = load_example_module("ai-and-agents/mcp_server_example")
    handler: Callable[[func.HttpRequest], func.HttpResponse] = next(
        f.get_user_function() for f in module.app.get_functions() if f.get_function_name() == "mcp"
    )
    return handler


@pytest.mark.parametrize(
    "message,code",
    [
        (None, -32600),
        ([], -32600),
        ("secret-canary", -32600),
        (5, -32600),
        ({}, -32600),
        ({"jsonrpc": "1.0", "method": "tools/list"}, -32600),
        ({"jsonrpc": "2.0", "method": []}, -32600),
        ({"jsonrpc": "2.0", "method": ""}, -32600),
        ({"jsonrpc": "2.0", "method": "tools/list", "id": []}, -32600),
        ({"jsonrpc": "2.0", "method": "tools/list", "id": True}, -32600),
        ({"jsonrpc": "2.0", "method": "tools/list", "params": None}, -32602),
        ({"jsonrpc": "2.0", "method": "initialize", "params": []}, -32602),
        ({"jsonrpc": "2.0", "method": "tools/call", "params": "secret-canary"}, -32602),
    ],
)
def test_invalid_envelope_returns_protocol_error(
    mcp_handler: Callable[[func.HttpRequest], func.HttpResponse], message: Json, code: int
) -> None:
    # Given an untrusted JSON value, not necessarily a JSON-RPC request.
    request = func.HttpRequest(
        method="POST", url="http://localhost/api/mcp", params={}, body=json.dumps(message).encode()
    )
    # When the registered HTTP handler processes it.
    response = mcp_handler(request)
    # Then the response is a redacted protocol error, not a server exception.
    assert response.status_code == 400
    payload = json.loads(response.get_body())
    assert payload["error"]["code"] == code
    assert payload["id"] is None
    assert b"secret-canary" not in response.get_body()


@pytest.mark.parametrize(
    "params",
    [
        {},
        {"name": None},
        {"name": []},
        {"name": {}},
        {"name": 1},
        {"name": ""},
        {"name": "calculate"},
        {"name": "calculate", "arguments": None},
        {"name": "calculate", "arguments": []},
        {"name": "calculate", "arguments": "secret-canary"},
        {"name": "calculate", "arguments": {}},
        {"name": "calculate", "arguments": {"expression": None}},
        {"name": "calculate", "arguments": {"expression": 1}},
        {"name": "calculate", "arguments": {"expression": True}},
        {"name": "calculate", "arguments": {"expression": ["2+2"]}},
        {"name": "get_weather", "arguments": {}},
        {"name": "get_weather", "arguments": {"location": 1}},
        {"name": "get_weather", "arguments": {"location": None}},
        {"name": "get_weather", "arguments": {"location": {}}},
    ],
)
def test_invalid_tool_arguments_return_invalid_params(
    mcp_handler: Callable[[func.HttpRequest], func.HttpResponse], params: Json
) -> None:
    # Given a valid envelope with malformed tool parameters.
    request = func.HttpRequest(
        method="POST",
        url="http://localhost/api/mcp",
        params={},
        body=json.dumps(
            {"jsonrpc": "2.0", "id": "request-426", "method": "tools/call", "params": params}
        ).encode(),
    )
    # When the registered route is invoked.
    response = mcp_handler(request)
    # Then validation rejects the call without reflecting the input.
    assert response.status_code == 400
    payload = json.loads(response.get_body())
    assert payload == {
        "jsonrpc": "2.0",
        "id": "request-426",
        "error": {"code": -32602, "message": "Invalid tool arguments"},
    }


def test_parse_error_remains_json_rpc_error(
    mcp_handler: Callable[[func.HttpRequest], func.HttpResponse],
) -> None:
    # Given invalid JSON.
    request = func.HttpRequest(
        method="POST", url="http://localhost/api/mcp", params={}, body=b'{"secret-canary":'
    )
    # When parsed by the real route.
    response = mcp_handler(request)
    # Then parsing details are not exposed.
    assert response.status_code == 400
    assert json.loads(response.get_body())["error"] == {"code": -32700, "message": "Parse error"}
