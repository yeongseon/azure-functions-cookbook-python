from __future__ import annotations

import logging
import math
from typing import TypeAlias, TypedDict

from app.services.calculator import InvalidExpression, calculate

Json: TypeAlias = None | bool | int | float | str | list["Json"] | dict[str, "Json"]

logger = logging.getLogger(__name__)


class InputSchema(TypedDict):
    type: str
    properties: dict[str, dict[str, str]]
    required: list[str]


class Tool(TypedDict):
    description: str
    inputSchema: InputSchema


TOOLS: dict[str, Tool] = {
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


def _handle_get_weather(location: str) -> str:
    return f"The weather in {location} is sunny, 22C."


TOOL_HANDLERS = {
    "get_weather": _handle_get_weather,
    "calculate": calculate,
}


def _json_rpc_response(request_id: Json, result: Json) -> dict[str, Json]:
    return {"jsonrpc": "2.0", "id": request_id, "result": result}


def _json_rpc_error(request_id: Json, code: int, message: str) -> dict[str, Json]:
    return {
        "jsonrpc": "2.0",
        "id": request_id,
        "error": {"code": code, "message": message},
    }


def handle_mcp_request(body: Json) -> tuple[dict[str, Json] | None, int]:
    if not isinstance(body, dict):
        return _json_rpc_error(None, -32600, "Invalid request"), 400
    request_id = body.get("id")
    method = body.get("method", "")
    params = body.get("params", {})
    if type(request_id) not in (str, int, float, type(None)) or (
        isinstance(request_id, float) and not math.isfinite(request_id)
    ):
        return _json_rpc_error(None, -32600, "Invalid request"), 400
    if body.get("jsonrpc") != "2.0" or not isinstance(method, str) or not method:
        return _json_rpc_error(request_id, -32600, "Invalid request"), 400
    if method == "notifications/initialized":
        if "id" in body or not isinstance(params, dict):
            return _json_rpc_error(request_id, -32600, "Invalid initialized notification"), 400
        return None, 202
    if not isinstance(params, dict):
        return _json_rpc_error(request_id, -32602, "Invalid params"), 400

    logger.info("MCP request received")

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
        tool_name = params.get("name")
        arguments = params.get("arguments")
        if not isinstance(tool_name, str) or not tool_name or not isinstance(arguments, dict):
            return _json_rpc_error(request_id, -32602, "Invalid tool arguments"), 400
        handler = TOOL_HANDLERS.get(tool_name)
        if handler is None:
            return _json_rpc_error(request_id, -32601, "Unknown tool"), 404
        schema = TOOLS[tool_name]["inputSchema"]
        field = schema["required"][0]
        value = arguments.get(field)
        if not isinstance(value, str):
            return _json_rpc_error(request_id, -32602, "Invalid tool arguments"), 400
        try:
            output = handler(value)
        except InvalidExpression:
            return _json_rpc_error(request_id, -32602, "Invalid calculator expression"), 400
        result = {"content": [{"type": "text", "text": output}]}
        return _json_rpc_response(request_id, result), 200

    return _json_rpc_error(request_id, -32601, "Method not found"), 404
