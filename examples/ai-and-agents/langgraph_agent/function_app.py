import azure.functions as func
from azure_functions_langgraph import LangGraphApp
from azure_functions_logging import setup_logging, with_context, get_logger
from azure_functions_validation import validate_http
from azure_functions_openapi import openapi
from pydantic import BaseModel

setup_logging(format="json")
logger = get_logger(__name__)

langgraph_app = LangGraphApp()
app = func.FunctionApp(http_auth_level=func.AuthLevel.FUNCTION)


class InvokeRequest(BaseModel):
    message: str
    thread_id: str | None = None


class InvokeResponse(BaseModel):
    response: str
    thread_id: str


def build_graph():
    try:
        from langgraph.graph import StateGraph, END
        from typing import TypedDict

        class AgentState(TypedDict):
            message: str
            response: str

        def process_node(state: AgentState) -> AgentState:
            logger.info("Processing message", extra={"message": state["message"]})
            return {"response": f"Agent received: {state['message']}"}

        graph = StateGraph(AgentState)
        graph.add_node("process", process_node)
        graph.set_entry_point("process")
        graph.add_edge("process", END)
        return graph.compile()
    except ImportError:
        logger.warning("langgraph not installed, using stub")
        return None


graph = build_graph()
if graph:
    langgraph_app.register(graph=graph)


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
    import uuid

    thread_id = body.thread_id or str(uuid.uuid4())
    logger.info("Invoking agent", extra={"thread_id": thread_id})

    result = {"response": f"Agent received: {body.message}", "thread_id": thread_id}
    return func.HttpResponse(
        body=InvokeResponse(**result).model_dump_json(),
        mimetype="application/json",
    )
