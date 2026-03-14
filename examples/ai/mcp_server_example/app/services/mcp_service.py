from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)

TOOLS: dict[str, dict[str, Any]] = {
    "get_weather": {
        "description": "Get current weather for a location",
        "inputSchema": {
            "type": "object",
            "properties": {
                "location": {
                    "type": "string",
                    "description": "City and state, e.g. San Francisco, CA",
                },
            },
            "required": ["location"],
        },
    },
    "calculate": {
        "description": "Evaluate a simple math expression",
        "inputSchema": {
            "type": "object",
            "properties": {
                "expression": {
                    "type": "string",
                    "description": "Math expression to evaluate, e.g. '2 + 2'",
                },
            },
            "required": ["expression"],
        },
    },
}


def _handle_get_weather(arguments: dict[str, Any]) -> str:
    location = arguments.get("location", "Unknown")
    return f"The weather in {location} is sunny, 22C."


def _handle_calculate(arguments: dict[str, Any]) -> str:
    expression = arguments.get("expression", "0")
    allowed = set("0123456789+-*/() .")
    if not all(c in allowed for c in expression):
        return "Error: expression contains invalid characters"
    try:
        result = eval(expression)  # noqa: S307 - restricted character set above
        return str(result)
    except Exception:
        return "Error: could not evaluate expression"


TOOL_HANDLERS: dict[str, Any] = {
    "get_weather": _handle_get_weather,
    "calculate": _handle_calculate,
}


def _json_rpc_response(request_id: Any, result: Any) -> dict[str, Any]:
    return {"jsonrpc": "2.0", "id": request_id, "result": result}


def _json_rpc_error(request_id: Any, code: int, message: str) -> dict[str, Any]:
    return {
        "jsonrpc": "2.0",
        "id": request_id,
        "error": {"code": code, "message": message},
    }


def handle_mcp_request(body: dict) -> tuple[dict, int]:
    request_id = body.get("id")
    method = body.get("method", "")
    params = body.get("params", {})

    logger.info("MCP request: method=%s id=%s", method, request_id)

    if method == "initialize":
        result = {
            "protocolVersion": "2025-03-26",
            "capabilities": {"tools": {"listChanged": False}},
            "serverInfo": {
                "name": "azure-functions-mcp-example",
                "version": "0.1.0",
            },
        }
        return _json_rpc_response(request_id, result), 200

    if method == "tools/list":
        tools_list = [
            {
                "name": name,
                "description": tool["description"],
                "inputSchema": tool["inputSchema"],
            }
            for name, tool in TOOLS.items()
        ]
        return _json_rpc_response(request_id, {"tools": tools_list}), 200

    if method == "tools/call":
        tool_name = params.get("name", "") if isinstance(params, dict) else ""
        arguments = params.get("arguments", {}) if isinstance(params, dict) else {}
        handler = TOOL_HANDLERS.get(tool_name)
        if handler is None:
            return _json_rpc_error(request_id, -32601, f"Unknown tool: {tool_name}"), 404
        output = handler(arguments)
        result = {"content": [{"type": "text", "text": output}]}
        return _json_rpc_response(request_id, result), 200

    return _json_rpc_error(request_id, -32601, f"Method not found: {method}"), 404
