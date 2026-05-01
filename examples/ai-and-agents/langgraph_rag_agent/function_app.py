from __future__ import annotations

import importlib
import json
import logging
import uuid
from typing import Any, Literal, TypedDict

import azure.functions as func
from pydantic import BaseModel, Field


class FallbackLangGraphApp:
    def __init__(self, auth_level: func.AuthLevel = func.AuthLevel.ANONYMOUS):
        self.auth_level = auth_level
        self.function_app = func.FunctionApp(http_auth_level=auth_level)
        self.graph: object | None = None
        self.graph_name: str | None = None
        self.graph_description: str | None = None

    def register(self, graph: object, name: str, description: str | None = None) -> None:
        self.graph = graph
        self.graph_name = name
        self.graph_description = description


def _load_attr(module_name: str, attr_name: str, default: object) -> object:
    try:
        module = importlib.import_module(module_name)
    except ImportError:
        return default
    return getattr(module, attr_name, default)


def _setup_logging_fallback(*args: object, **kwargs: object) -> None:
    logging.basicConfig(level=logging.INFO)


def _get_logger_fallback(name: str) -> logging.Logger:
    return logging.getLogger(name)


def _identity_decorator(*args: object, **kwargs: object):
    def decorator(func_handler):
        return func_handler

    return decorator


def _with_context_fallback(func_handler):
    return func_handler


LangGraphApp = _load_attr("azure_functions_langgraph", "LangGraphApp", FallbackLangGraphApp)
get_logger = _load_attr("azure_functions_logging", "get_logger", _get_logger_fallback)
setup_logging = _load_attr("azure_functions_logging", "setup_logging", _setup_logging_fallback)
with_context = _load_attr("azure_functions_logging", "with_context", _with_context_fallback)
openapi = _load_attr("azure_functions_openapi", "openapi", _identity_decorator)
validate_http = _load_attr("azure_functions_validation", "validate_http", _identity_decorator)

_langgraph_graph = importlib.util.find_spec("langgraph.graph")
if _langgraph_graph is not None:
    _graph_module = importlib.import_module("langgraph.graph")
    END = _graph_module.END
    START = _graph_module.START
    StateGraph = _graph_module.StateGraph
else:
    END = None
    START = None
    StateGraph = None


setup_logging(format="json")
logger = get_logger(__name__)


class Citation(BaseModel):
    title: str
    snippet: str
    source: str


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, description="Latest user message.")
    thread_id: str | None = Field(default=None, description="Conversation identifier.")
    top_k: int = Field(default=3, ge=1, le=5, description="Knowledge results to retrieve.")


class ChatResponse(BaseModel):
    thread_id: str
    route: Literal["knowledge_search", "direct_response"]
    answer: str
    citations: list[Citation] = Field(default_factory=list)
    history_length: int


class AgentState(TypedDict):
    messages: list[dict[str, str]]
    route: Literal["knowledge_search", "direct_response"]
    answer: str
    citations: list[dict[str, str]]
    top_k: int


THREAD_MEMORY: dict[str, list[dict[str, str]]] = {}
SEARCH_HINTS = (
    "search",
    "find",
    "knowledge",
    "docs",
    "documentation",
    "runbook",
    "policy",
    "manual",
    "kb",
    "how do i",
)


def _build_knowledge_client() -> Any | None:
    return None


def _normalize_citations(results: Any) -> list[dict[str, str]]:
    normalized: list[dict[str, str]] = []

    if not results:
        return normalized

    if isinstance(results, dict):
        candidates = results.get("results") or results.get("documents") or [results]
    else:
        candidates = results

    for item in list(candidates)[:5]:
        if isinstance(item, dict):
            normalized.append(
                {
                    "title": str(item.get("title") or item.get("name") or "Knowledge Result"),
                    "snippet": str(
                        item.get("snippet")
                        or item.get("content")
                        or item.get("text")
                        or "No snippet available."
                    ),
                    "source": str(item.get("source") or item.get("url") or "knowledge://result"),
                }
            )
        else:
            normalized.append(
                {
                    "title": "Knowledge Result",
                    "snippet": str(item),
                    "source": "knowledge://result",
                }
            )

    return normalized


def search_knowledge(query: str, top_k: int) -> list[dict[str, str]]:
    client = _build_knowledge_client()

    if client is not None:
        for method_name in ("search", "query", "retrieve"):
            method = getattr(client, method_name, None)
            if callable(method):
                try:
                    return _normalize_citations(method(query=query, top_k=top_k))
                except TypeError:
                    try:
                        return _normalize_citations(method(query, top_k=top_k))
                    except Exception:
                        logger.warning("Knowledge search failed.", exc_info=True)
                except Exception:
                    logger.warning("Knowledge search failed.", exc_info=True)

    return [
        {
            "title": "Onboarding Runbook",
            "snippet": (
                "Reset the password from the Helpdesk portal, then reissue MFA if the "
                "account is still locked."
            ),
            "source": "mock://onboarding-runbook",
        },
        {
            "title": "Access Policy FAQ",
            "snippet": (
                "Temporary passwords expire after 24 hours and must be changed at first sign-in."
            ),
            "source": "mock://access-policy-faq",
        },
    ][:top_k]


def should_search_knowledge(message: str) -> bool:
    lowered = message.lower()
    return any(hint in lowered for hint in SEARCH_HINTS)


def router_node(state: AgentState) -> dict[str, str]:
    latest_message = state["messages"][-1]["content"]
    route: Literal["knowledge_search", "direct_response"]
    route = "knowledge_search" if should_search_knowledge(latest_message) else "direct_response"
    return {"route": route}


def select_route(state: AgentState) -> str:
    return state.get("route", "direct_response")


def knowledge_search_node(state: AgentState) -> AgentState:
    query = state["messages"][-1]["content"]
    citations = search_knowledge(query=query, top_k=state.get("top_k", 3))
    supporting_text = " ".join(citation["snippet"] for citation in citations)
    answer = (
        f"I searched the knowledge base before responding. Relevant guidance: {supporting_text}"
    )
    return {
        "route": "knowledge_search",
        "answer": answer,
        "citations": citations,
        "messages": state["messages"] + [{"role": "assistant", "content": answer}],
    }


def direct_response_node(state: AgentState) -> AgentState:
    query = state["messages"][-1]["content"]
    answer = (
        "I answered directly without retrieval because the request looked conversational. "
        f"You said: {query}"
    )
    return {
        "route": "direct_response",
        "answer": answer,
        "citations": [],
        "messages": state["messages"] + [{"role": "assistant", "content": answer}],
    }


def build_graph() -> Any | None:
    if StateGraph is None or START is None or END is None:
        logger.warning("langgraph is not installed; using direct Python fallback.")
        return None

    builder = StateGraph(AgentState)
    builder.add_node("router", router_node)
    builder.add_node("knowledge_search", knowledge_search_node)
    builder.add_node("direct_response", direct_response_node)
    builder.add_edge(START, "router")
    builder.add_conditional_edges(
        "router",
        select_route,
        {
            "knowledge_search": "knowledge_search",
            "direct_response": "direct_response",
        },
    )
    builder.add_edge("knowledge_search", END)
    builder.add_edge("direct_response", END)
    return builder.compile()


def invoke_agent_graph(state: AgentState) -> AgentState:
    if GRAPH is not None:
        return GRAPH.invoke(state)

    route = router_node(state)["route"]
    routed_state: AgentState = {**state, "route": route}
    if route == "knowledge_search":
        return knowledge_search_node(routed_state)
    return direct_response_node(routed_state)


LANGGRAPH_HOST = LangGraphApp(auth_level=func.AuthLevel.ANONYMOUS)
app = LANGGRAPH_HOST.function_app
GRAPH = build_graph()

if GRAPH is not None:
    LANGGRAPH_HOST.register(
        graph=GRAPH,
        name="langgraph_rag_agent",
        description="LangGraph agent with a knowledge search tool.",
    )


@app.route(route="chat", methods=["POST"])
@with_context
@openapi(
    summary="Chat with a LangGraph RAG agent",
    description=(
        "Stateful conversation endpoint that routes each turn through a LangGraph "
        "agent and optionally calls the knowledge search tool."
    ),
    request_body=ChatRequest,
    response={200: ChatResponse},
    tags=["ai-and-agents"],
)
@validate_http(body=ChatRequest, response_model=ChatResponse)
def chat(req: func.HttpRequest, body: ChatRequest) -> func.HttpResponse:
    thread_id = body.thread_id or str(uuid.uuid4())
    history = list(THREAD_MEMORY.get(thread_id, []))
    messages = history + [{"role": "user", "content": body.message}]

    state: AgentState = {
        "messages": messages,
        "route": "direct_response",
        "answer": "",
        "citations": [],
        "top_k": body.top_k,
    }
    result = invoke_agent_graph(state)
    updated_messages = result.get("messages", messages)
    THREAD_MEMORY[thread_id] = updated_messages

    citations = [Citation(**item) for item in result.get("citations", [])]
    payload = ChatResponse(
        thread_id=thread_id,
        route=result.get("route", "direct_response"),
        answer=result.get("answer", "No answer generated."),
        citations=citations,
        history_length=len(updated_messages),
    )

    logger.info(
        "Processed chat turn.",
        extra={
            "thread_id": thread_id,
            "route": payload.route,
            "history_length": payload.history_length,
            "knowledge_hits": len(payload.citations),
            "request_url": req.url,
        },
    )

    return func.HttpResponse(
        body=payload.model_dump_json(indent=2),
        mimetype="application/json",
    )


@app.route(route="chat/state/{thread_id}", methods=["GET"])
def get_thread_state(req: func.HttpRequest) -> func.HttpResponse:
    thread_id = req.route_params.get("thread_id", "")
    messages = THREAD_MEMORY.get(thread_id, [])
    return func.HttpResponse(
        body=json.dumps({"thread_id": thread_id, "messages": messages}, indent=2),
        mimetype="application/json",
    )
