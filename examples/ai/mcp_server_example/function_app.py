"""MCP server hosted on Azure Functions Python.

This example demonstrates hosting a Model Context Protocol (MCP) server
as an Azure Function. The function handles MCP JSON-RPC requests over HTTP,
enabling AI agents to discover and invoke tools.

For production deployments, consider using the official
``azure-functions-extension-mcp`` package when available.
"""

from __future__ import annotations

import json
import logging
from typing import Any

import azure.functions as func

app = func.FunctionApp()
logger = logging.getLogger(__name__)

# --- Tool Registry ---

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
    """Simulate weather lookup."""
    location = arguments.get("location", "Unknown")
    return f"The weather in {location} is sunny, 22C."


def _handle_calculate(arguments: dict[str, Any]) -> str:
    """Evaluate a safe math expression."""
    expression = arguments.get("expression", "0")
    # Only allow digits, operators, spaces, parentheses, and decimal points
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
    """Build a JSON-RPC 2.0 success response."""
    return {"jsonrpc": "2.0", "id": request_id, "result": result}


def _json_rpc_error(request_id: Any, code: int, message: str) -> dict[str, Any]:
    """Build a JSON-RPC 2.0 error response."""
    return {
        "jsonrpc": "2.0",
        "id": request_id,
        "error": {"code": code, "message": message},
    }


@app.route(route="mcp", methods=["POST"], auth_level=func.AuthLevel.FUNCTION)
def mcp_endpoint(req: func.HttpRequest) -> func.HttpResponse:
    """Handle MCP JSON-RPC requests.

    Supported methods:
    - initialize: Server capability handshake
    - tools/list: Return available tools
    - tools/call: Execute a tool
    """
    try:
        body = req.get_json()
    except ValueError:
        resp = _json_rpc_error(None, -32700, "Parse error")
        return func.HttpResponse(
            json.dumps(resp),
            mimetype="application/json",
            status_code=400,
        )

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
    elif method == "tools/list":
        tools_list = [
            {
                "name": name,
                "description": t["description"],
                "inputSchema": t["inputSchema"],
            }
            for name, t in TOOLS.items()
        ]
        result = {"tools": tools_list}
    elif method == "tools/call":
        tool_name = params.get("name", "")
        arguments = params.get("arguments", {})
        handler = TOOL_HANDLERS.get(tool_name)
        if handler is None:
            resp = _json_rpc_error(request_id, -32601, f"Unknown tool: {tool_name}")
            return func.HttpResponse(
                json.dumps(resp),
                mimetype="application/json",
                status_code=404,
            )
        output = handler(arguments)
        result = {"content": [{"type": "text", "text": output}]}
    else:
        resp = _json_rpc_error(request_id, -32601, f"Method not found: {method}")
        return func.HttpResponse(
            json.dumps(resp),
            mimetype="application/json",
            status_code=404,
        )

    resp = _json_rpc_response(request_id, result)
    return func.HttpResponse(json.dumps(resp), mimetype="application/json", status_code=200)
