from app.services.mcp_service import handle_mcp_request


def test_initialize_returns_capabilities() -> None:
    response, status_code = handle_mcp_request(
        {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}}
    )

    assert status_code == 200
    assert response["result"]["protocolVersion"] == "2025-03-26"
    assert response["result"]["serverInfo"]["name"] == "azure-functions-mcp-example"


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
