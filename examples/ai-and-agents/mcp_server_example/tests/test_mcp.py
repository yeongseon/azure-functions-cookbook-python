import pytest

from app.services.mcp_service import handle_mcp_request


def test_initialize_returns_capabilities() -> None:
    response, status_code = handle_mcp_request(
        {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}}
    )

    assert status_code == 200
    assert response["result"]["protocolVersion"] == "2025-03-26"
    assert response["result"]["serverInfo"]["name"] == "azure-functions-mcp-example"


@pytest.mark.parametrize("params", [None, {}, {"_meta": {"client": "example"}}])
def test_initialized_notification_has_no_json_rpc_response(params: dict | None) -> None:
    notification = {"jsonrpc": "2.0", "method": "notifications/initialized"}
    if params is not None:
        notification["params"] = params

    response, status_code = handle_mcp_request(notification)

    assert status_code == 202
    assert response is None


@pytest.mark.parametrize(
    "invalid_fields",
    [
        {"id": 0},
        {"id": ""},
        {"id": None},
        {"jsonrpc": "1.0"},
        {"jsonrpc": None},
        {"params": []},
        {"params": None},
    ],
)
def test_malformed_initialized_notification_is_not_acknowledged(invalid_fields: dict) -> None:
    message = {"jsonrpc": "2.0", "method": "notifications/initialized", **invalid_fields}

    response, status_code = handle_mcp_request(message)

    assert status_code == 400
    assert response["error"]["code"] == -32600
    assert response["id"] == message.get("id")


def test_initialized_notification_requires_json_rpc_version() -> None:
    response, status_code = handle_mcp_request({"method": "notifications/initialized"})

    assert status_code == 400
    assert response["error"]["code"] == -32600


def test_unsupported_notification_is_not_acknowledged() -> None:
    response, status_code = handle_mcp_request(
        {"jsonrpc": "2.0", "method": "notifications/unsupported"}
    )

    assert status_code == 404
    assert response["error"]["code"] == -32601


def test_tools_list_returns_registered_tools() -> None:
    response, status_code = handle_mcp_request(
        {"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}}
    )

    assert status_code == 200
    tools = response["result"]["tools"]
    assert len(tools) == 2
    assert {tool["name"] for tool in tools} == {"get_weather", "calculate"}


def test_tools_call_invokes_calculate() -> None:
    response, status_code = handle_mcp_request(
        {
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call",
            "params": {"name": "calculate", "arguments": {"expression": "(2 + 3) * 4"}},
        }
    )

    assert status_code == 200
    assert response["result"]["content"][0]["text"] == "20"


def test_tools_call_unknown_tool_returns_error() -> None:
    response, status_code = handle_mcp_request(
        {
            "jsonrpc": "2.0",
            "id": 4,
            "method": "tools/call",
            "params": {"name": "unknown", "arguments": {}},
        }
    )

    assert status_code == 404
    assert response["error"]["code"] == -32601
    assert response["error"]["message"] == "Unknown tool: unknown"


def test_unknown_method_returns_error() -> None:
    response, status_code = handle_mcp_request(
        {"jsonrpc": "2.0", "id": 5, "method": "unsupported/method", "params": {}}
    )

    assert status_code == 404
    assert response["error"]["code"] == -32601
    assert response["error"]["message"] == "Method not found: unsupported/method"
