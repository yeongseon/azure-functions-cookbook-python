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
    thread_id: str


def build_graph() -> Any:
    try:
        from typing import TypedDict

        from langgraph.graph import END, StateGraph

        class AgentState(TypedDict):
            message: str
            response: str

        def process_node(state: AgentState) -> AgentState:
            logger.info("Processing message", extra={"message": state["message"]})
            return {"response": f"Agent received: {state['message']}"}  # type: ignore[return-value]

        graph = StateGraph(AgentState)
        graph.add_node("process", process_node)
        graph.set_entry_point("process")
        graph.add_edge("process", END)
        return graph.compile()
    except ImportError:
        logger.warning("langgraph not installed, using stub")
        return None


graph = build_graph()
if graph and _langgraph_app is not None:
    _langgraph_app.register(graph=graph)


@app.route(route="agent/invoke", methods=["POST"])
@with_context
@openapi(
    summary="Invoke LangGraph agent",
    request_body=InvokeRequest,
    response={200: InvokeResponse},
    tags=["agent"],
)
@validate_http(body=InvokeRequest, response_model=InvokeResponse)
def invoke_agent(req: func.HttpRequest, body: InvokeRequest) -> func.HttpResponse:
    thread_id = body.thread_id or str(uuid.uuid4())
    logger.info("Invoking agent", extra={"thread_id": thread_id})
    result = {"response": f"Agent received: {body.message}", "thread_id": thread_id}
    return func.HttpResponse(
        body=InvokeResponse(**result).model_dump_json(),
        mimetype="application/json",
    )
