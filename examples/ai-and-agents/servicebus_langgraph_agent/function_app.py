from __future__ import annotations

import azure.functions as func
from azure_functions_langgraph import LangGraphApp, LoggingRunObserver

from app.agent import build_graph, build_model, build_tool
from app.contract import map_input, thread_id_for
from app.outcomes import InMemoryOutcomeStore, make_result_handler
from app.settings import load_settings

TRIGGER_NAME = "agent_requests"

settings = load_settings()
tool = build_tool()
model = build_model(settings, tool)
graph = build_graph(model, tool)
# Local demo sink. Swap for a durable, idempotent store before production.
store = InMemoryOutcomeStore()

# No HTTP surface is needed, so even the adapter's health probe stays behind a function key.
adapter = LangGraphApp(
    auth_level=func.AuthLevel.FUNCTION,
    health_auth_level=func.AuthLevel.FUNCTION,
    observer=LoggingRunObserver(),
)
adapter.register_service_bus(
    graph,
    TRIGGER_NAME,
    # The setting name is fixed; its value picks the credential. In production set
    # ServiceBusConnection__fullyQualifiedNamespace (managed identity) instead of a string.
    connection="ServiceBusConnection",
    queue_name=settings.queue_name,
    input_mapper=map_input,
    # Session mode: the adapter requires session_id and uses it as the thread_id, so a factory
    # must not be supplied. Otherwise the producer's conversation_id picks the thread.
    thread_id_factory=None if settings.sessions else thread_id_for,
    result_handler=make_result_handler(store),
    lock_timeout=settings.lock_timeout_seconds,
    session=settings.sessions,
)
app = adapter.function_app
