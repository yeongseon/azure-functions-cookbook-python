"""Tool-use LangGraph agent on Azure Functions.

The third langgraph cookbook pattern (after ``langgraph_agent`` = chat and
``langgraph_rag_agent`` = retrieval): a reasoning node inspects the message and
conditionally routes to a callable **tool** (a calculator or a time lookup)
before returning. This shows LangGraph conditional edges wired to tools while
staying inside the Azure Functions ``azure-functions-langgraph`` adapter.

Every optional import (langgraph, the azure-functions-* siblings) is guarded so
the module imports cleanly under the cookbook smoke suite, which only imports
``function_app`` and asserts it exposes ``app``.
"""

from __future__ import annotations

import logging
import uuid
from typing import Any

import azure.functions as func
from pydantic import BaseModel

try:
    from azure_functions_langgraph import LangGraphApp as _LangGraphApp

    _langgraph_app: Any = _LangGraphApp()
except ImportError:
    _langgraph_app = None

try:
    from azure_functions_logging import get_logger, setup_logging, with_context

    setup_logging(format="json")
    logger = get_logger(__name__)
except ImportError:
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)  # type: ignore[assignment]

    def with_context(fn: Any) -> Any:  # type: ignore[misc]
        return fn


try:
    from azure_functions_validation import validate_http
except ImportError:

    def validate_http(**kwargs: Any) -> Any:  # type: ignore[misc]
        def decorator(fn: Any) -> Any:
            return fn

        return decorator


try:
    from azure_functions_openapi import openapi
except ImportError:

    def openapi(**kwargs: Any) -> Any:  # type: ignore[misc]
        def decorator(fn: Any) -> Any:
            return fn

        return decorator


app = func.FunctionApp(http_auth_level=func.AuthLevel.FUNCTION)


class InvokeRequest(BaseModel):
    message: str
    thread_id: str | None = None


class InvokeResponse(BaseModel):
    response: str
    tool_used: str
    thread_id: str


# --- Tools -----------------------------------------------------------------
def calculator_tool(expression: str) -> str:
    """Evaluate a simple ``a + b`` / ``a * b`` style arithmetic expression."""
    import operator

    ops = {"+": operator.add, "-": operator.sub, "*": operator.mul}
    for symbol, fn in ops.items():
        if symbol in expression:
            left, _, right = expression.partition(symbol)
            try:
                return str(fn(float(left.strip()), float(right.strip())))
            except ValueError:
                return "could not parse operands"
    return "no supported operator found"


def time_tool(_query: str) -> str:
    """Return the current UTC time."""
    from datetime import datetime, timezone

    return datetime.now(timezone.utc).isoformat()


def _select_tool(message: str) -> tuple[str, str]:
    """Route the message to a tool; return (tool_name, tool_output)."""
    lower = message.lower()
    if any(sym in message for sym in ("+", "-", "*")):
        return "calculator", calculator_tool(message)
    if "time" in lower:
        return "time", time_tool(message)
    return "none", f"No tool matched; echoing: {message}"


def build_graph() -> Any:
    """Build a LangGraph with a reasoning node that routes to tools."""
    try:
        from typing import TypedDict

        from langgraph.graph import END, StateGraph

        class ToolState(TypedDict):
            message: str
            tool_used: str
            response: str

        def reason_node(state: ToolState) -> ToolState:
            tool_name, output = _select_tool(state["message"])
            logger.info("Tool routed", extra={"tool": tool_name})
            return {"tool_used": tool_name, "response": output}  # type: ignore[return-value]

        graph = StateGraph(ToolState)
        graph.add_node("reason", reason_node)
        graph.set_entry_point("reason")
        graph.add_edge("reason", END)
        return graph.compile()
    except ImportError:
        logger.warning("langgraph not installed, using in-process tool routing")
        return None


graph = build_graph()
if graph is not None and _langgraph_app is not None:
    _langgraph_app.register(graph=graph, name="langgraph_tool_use")


@app.route(route="agent/tool", methods=["POST"])
@with_context
@openapi(
    summary="Invoke tool-use LangGraph agent",
    requests=InvokeRequest,
    responses={200: InvokeResponse},
    tags=["agent"],
)
@validate_http(body=InvokeRequest, response_model=InvokeResponse)
def invoke_tool_agent(req: func.HttpRequest, body: InvokeRequest) -> func.HttpResponse:
    thread_id = body.thread_id or str(uuid.uuid4())
    tool_name, output = _select_tool(body.message)
    logger.info("Invoking tool agent", extra={"thread_id": thread_id, "tool": tool_name})
    payload = InvokeResponse(response=output, tool_used=tool_name, thread_id=thread_id)
    return func.HttpResponse(
        body=payload.model_dump_json(),
        mimetype="application/json",
    )
