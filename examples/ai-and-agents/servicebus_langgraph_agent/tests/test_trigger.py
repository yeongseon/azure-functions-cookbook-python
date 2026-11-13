"""Run the real generated Service Bus handler with synthetic messages. No broker, no Azure."""

from __future__ import annotations

import importlib.util
import logging
import sys
from collections.abc import Callable, Sequence
from pathlib import Path
from types import ModuleType
from typing import Any

import azure.functions as func
import pytest
from azure_functions_langgraph.locks import InProcessThreadLock
from azure_functions_langgraph.triggers.service_bus import ThreadContentionError
from conftest import make_message, request
from langchain_core.messages import AIMessage, BaseMessage

from app.outcomes import InMemoryOutcomeStore

PROJECT = Path(__file__).resolve().parents[1]
FUNCTION_NAME = "aflg_sb_agent_requests"
Handler = Callable[[func.ServiceBusMessage], None]


def _functions(app: Any) -> dict[str, Any]:
    # Build once: asking a FunctionApp for its functions twice re-registers them.
    return {item.get_function_name(): item for item in app.get_functions()}


def _thread_messages(graph: Any, thread_id: str) -> list[tuple[str | None, str]]:
    state = graph.get_state({"configurable": {"thread_id": thread_id}})
    return [(m.id, str(m.content)) for m in state.values.get("messages", [])]


def _load_function_app(monkeypatch: pytest.MonkeyPatch, **env: str) -> ModuleType:
    """Import the real ``function_app.py`` under the given settings."""
    for name in ("SERVICEBUS_SESSIONS", "SERVICEBUS_QUEUE_NAME", "AGENT_MODEL_MODE"):
        monkeypatch.delenv(name, raising=False)
    for name, value in env.items():
        monkeypatch.setenv(name, value)
    monkeypatch.syspath_prepend(str(PROJECT))
    for name in [n for n in sys.modules if n == "app" or n.startswith("app.")]:
        monkeypatch.delitem(sys.modules, name)
    spec = importlib.util.spec_from_file_location(
        "sb_agent_function_app", PROJECT / "function_app.py"
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    monkeypatch.setitem(sys.modules, spec.name, module)
    spec.loader.exec_module(module)
    return module


class _Setup:
    def __init__(self, monkeypatch: pytest.MonkeyPatch, **env: str) -> None:
        self.module = _load_function_app(monkeypatch, **env)
        self.store: InMemoryOutcomeStore = self.module.store
        self.graph: Any = self.module.graph
        self.functions = _functions(self.module.app)
        self.handle: Handler = self.functions[FUNCTION_NAME].get_user_function()


@pytest.fixture
def setup(monkeypatch: pytest.MonkeyPatch) -> _Setup:
    return _Setup(monkeypatch)


@pytest.fixture
def session_setup(monkeypatch: pytest.MonkeyPatch) -> _Setup:
    return _Setup(monkeypatch, SERVICEBUS_SESSIONS="true")


def test_function_app_registers_the_trigger_and_no_anonymous_route(setup: _Setup) -> None:
    bindings = {name: item.get_trigger().get_dict_repr() for name, item in setup.functions.items()}

    trigger = bindings[FUNCTION_NAME]
    assert trigger["type"] == "serviceBusTrigger"
    assert (trigger["connection"], trigger["queueName"]) == (
        "ServiceBusConnection",
        "agent-requests",
    )
    assert "isSessionsEnabled" not in trigger
    http_levels = {b["authLevel"] for b in bindings.values() if b["type"] == "httpTrigger"}
    assert http_levels == {func.AuthLevel.FUNCTION}


def test_session_mode_enables_sessions_on_the_trigger(session_setup: _Setup) -> None:
    trigger = session_setup.functions[FUNCTION_NAME].get_trigger().get_dict_repr()

    assert trigger["isSessionsEnabled"] is True


def test_message_is_mapped_run_and_recorded(setup: _Setup) -> None:
    setup.handle(request("req-1", "Where is order A-1001?"))

    outcome = setup.store.get("req-1")
    assert outcome is not None
    assert "shipped, arriving Tuesday" in outcome.answer


def test_message_without_conversation_id_gets_its_own_thread(setup: _Setup) -> None:
    setup.handle(request("req-1"))

    assert _thread_messages(setup.graph, "sb:request:req-1")[0][0] == "req-1:question"
    assert _thread_messages(setup.graph, "req-1") == []


def test_conversation_id_maps_to_one_namespaced_thread(setup: _Setup) -> None:
    setup.handle(request("req-1", "Where is order A-1001?", conversation_id="conv-1"))
    setup.handle(request("req-2", "And order A-1002?", conversation_id="conv-1"))
    setup.handle(request("req-3", "Where is order A-1002?", conversation_id="conv-2"))

    first = [
        message_id for message_id, _ in _thread_messages(setup.graph, "sb:conversation:conv-1")
    ]
    assert [i for i in first if i and i.endswith(":question")] == [
        "req-1:question",
        "req-2:question",
    ]
    assert _thread_messages(setup.graph, "sb:conversation:conv-2")[0][0] == "req-3:question"
    assert _thread_messages(setup.graph, "conv-1") == []  # the raw producer ID is not a thread


def test_redelivery_is_idempotent_for_state_and_sink(setup: _Setup) -> None:
    setup.handle(request("req-1", "Where is order A-1001?", conversation_id="conv-1"))
    once = _thread_messages(setup.graph, "sb:conversation:conv-1")

    setup.handle(
        request("req-1", "Where is order A-1001?", conversation_id="conv-1", delivery_count=2)
    )

    assert _thread_messages(setup.graph, "sb:conversation:conv-1") == once
    assert len(setup.store) == 1


def test_redelivery_after_a_mid_run_failure_leaves_a_clean_thread(
    setup: _Setup, monkeypatch: pytest.MonkeyPatch
) -> None:
    model = setup.module.model
    healthy_invoke = model.invoke

    def fails_on_the_final_turn(messages: Sequence[BaseMessage]) -> AIMessage:
        if messages[-1].type == "tool":
            raise TimeoutError("model timed out")
        result: AIMessage = healthy_invoke(messages)
        return result

    message = request("req-1", "Where is order A-1001?", conversation_id="conv-1")
    monkeypatch.setattr(model, "invoke", fails_on_the_final_turn)

    with pytest.raises(TimeoutError):
        setup.handle(message)  # the exception reaches Service Bus, which abandons the message
    assert setup.store.get("req-1") is None  # no outcome for a failed run

    monkeypatch.setattr(model, "invoke", healthy_invoke)
    setup.handle(message)  # the redelivery

    ids = [message_id for message_id, _ in _thread_messages(setup.graph, "sb:conversation:conv-1")]
    assert ids == ["req-1:question", "req-1:agent", "req-1:tool:0", "req-1:final"]
    assert setup.store.get("req-1") is not None


def test_invalid_message_fails_without_running_the_graph(setup: _Setup) -> None:
    # Match by base class: each fixture reloads ``app``, so the exception class is per-load.
    with pytest.raises(ValueError, match="'question' must be a non-empty string"):
        setup.handle(make_message(b'{"request_id": "r"}'))

    assert len(setup.store) == 0


def test_sink_failure_fails_the_message(setup: _Setup, monkeypatch: pytest.MonkeyPatch) -> None:
    def unavailable(outcome: Any) -> None:
        raise ConnectionError("sink unavailable")

    monkeypatch.setattr(setup.store, "put", unavailable)

    with pytest.raises(ConnectionError):
        setup.handle(request("req-1"))


def test_session_id_is_the_thread_id(session_setup: _Setup) -> None:
    session_setup.handle(request("req-1", session_id="order-77"))
    session_setup.handle(request("req-2", "And A-1002?", session_id="order-77"))
    session_setup.handle(request("req-3", session_id="order-78"))

    questions = [
        i for i, _ in _thread_messages(session_setup.graph, "order-77") if i and "question" in i
    ]
    assert questions == ["req-1:question", "req-2:question"]
    assert _thread_messages(session_setup.graph, "order-78")[0][0] == "req-3:question"


def test_session_mode_rejects_a_message_without_a_session_id(session_setup: _Setup) -> None:
    with pytest.raises(ValueError, match="session_id"):
        session_setup.handle(request("req-1", session_id=None))

    assert len(session_setup.store) == 0


def test_contended_thread_fails_for_broker_retry_without_running_the_graph(
    setup: _Setup, monkeypatch: pytest.MonkeyPatch
) -> None:
    # A lock that is always held by another delivery. Patched at the class so it works for any
    # adapter version, whether acquire() waits (0.13 default) or returns immediately (0.12).
    monkeypatch.setattr(InProcessThreadLock, "acquire", lambda self, *a, **k: None)

    with pytest.raises(ThreadContentionError):
        setup.handle(request("req-1", conversation_id="conv-1"))

    assert len(setup.store) == 0


def test_logs_carry_correlation_but_no_prompt_answer_or_body(
    setup: _Setup, caplog: pytest.LogCaptureFixture
) -> None:
    question = "Where is order A-1001? my-private-detail"
    caplog.set_level(logging.DEBUG)

    setup.handle(request("req-1", question, conversation_id="conv-1", message_id="sb-msg-42"))

    outcome = setup.store.get("req-1")
    assert outcome is not None
    text = "\n".join(
        record.getMessage() + repr(getattr(record, "langgraph_run", ""))
        for record in caplog.records
    )
    assert "sb-msg-42" in text and "sb:conversation:conv-1" in text and "service_bus" in text
    assert "my-private-detail" not in text
    assert outcome.answer not in text
