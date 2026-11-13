"""Pure rules (publishing idempotency, parsing) and the LangGraph activity boundary."""

from __future__ import annotations

import logging
from typing import Any

import pytest
from durable_fakes import registered_functions

from app.core.limits import GRAPH_RECURSION_LIMIT, MAX_DRAFT_CHARS, MAX_MODEL_OUTPUT_TOKENS
from app.services import agent
from app.services.agent import (
    AzureOpenAIChatModel,
    FakeChatModel,
    build_graph,
    build_model,
    run_agent,
)
from app.services.workflow import (
    InMemorySink,
    RequestError,
    clamp_timeout,
    is_approval,
    is_terminal,
    normalize_status,
    parse_decision,
    parse_run_request,
    publish_approved,
    publish_key,
)

FUNCTIONS = registered_functions()


# --- publishing: at-least-once delivery ------------------------------------------------------


def test_redelivered_publish_activity_has_one_effect_and_the_same_receipt() -> None:
    sink = InMemorySink()
    first = publish_approved("run-1", "draft text", sink)
    again = publish_approved("run-1", "draft text", sink)
    assert len(sink.records) == 1 and list(sink.records) == [publish_key("run-1")]
    assert first["receipt"] == again["receipt"]
    assert (first["duplicate_delivery"], again["duplicate_delivery"]) == (False, True)


def test_a_different_run_is_a_different_effect() -> None:
    sink = InMemorySink()
    publish_approved("run-1", "d", sink)
    publish_approved("run-2", "d", sink)
    assert len(sink.records) == 2


def test_publish_activity_wrapper_delivers_twice_with_one_effect(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from app.functions import workflow

    sink = InMemorySink()
    monkeypatch.setattr(workflow, "get_sink", lambda: sink)
    publish = FUNCTIONS["publish_approved_result"].get_user_function()
    payload = {"run_id": "r", "draft": "hello"}
    assert publish(payload)["duplicate_delivery"] is False
    assert publish(payload)["duplicate_delivery"] is True
    assert len(sink.records) == 1


def test_publish_failure_raises_fixed_text_and_logs_the_cause(
    monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    from app.functions import workflow

    class Broken(InMemorySink):
        def record(self, key: str, summary: dict[str, Any]) -> bool:
            raise ConnectionError("password=hunter2")

    monkeypatch.setattr(workflow, "get_sink", lambda: Broken())
    caplog.set_level(logging.INFO)
    with pytest.raises(workflow.AgentActivityError) as info:
        FUNCTIONS["publish_approved_result"].get_user_function()({"run_id": "r", "draft": "d"})
    assert str(info.value) == "publish_failed" and info.value.__cause__ is None
    assert "Publish failed run_id=r" in caplog.text


def test_get_sink_and_model_are_cached(monkeypatch: pytest.MonkeyPatch) -> None:
    from app.functions import workflow

    workflow.get_sink.cache_clear()
    assert workflow.get_sink() is workflow.get_sink()
    workflow.get_model.cache_clear()
    monkeypatch.delenv("AGENT_MODEL_MODE", raising=False)
    assert workflow.get_model() is workflow.get_model()
    workflow.get_model.cache_clear()
    workflow.get_sink.cache_clear()


# --- agent activity boundary ----------------------------------------------------------------


def test_draft_activity_runs_the_graph_and_logs_lengths_not_text(
    monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    from app.functions import workflow

    monkeypatch.setattr(workflow, "get_model", lambda: FakeChatModel())
    caplog.set_level(logging.INFO)
    out = FUNCTIONS["run_agent_draft"].get_user_function()(
        {"run_id": "run-9", "prompt": "SECRET   PROMPT"}
    )
    assert out == {"draft": "Draft reply to: SECRET PROMPT"}
    assert "run_id=run-9" in caplog.text and "draft_chars=" in caplog.text
    assert "SECRET" not in caplog.text


def test_draft_activity_failure_has_fixed_text_and_no_chained_cause(
    monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    from app.functions import workflow

    class Boom:
        def complete(self, prompt: str) -> str:
            raise TimeoutError("api-key=abc123")

    monkeypatch.setattr(workflow, "get_model", lambda: Boom())
    with pytest.raises(workflow.AgentActivityError) as info:
        FUNCTIONS["run_agent_draft"].get_user_function()({"run_id": "r", "prompt": "p"})
    assert str(info.value) == "agent_draft_failed" and info.value.__cause__ is None
    assert "Agent draft failed run_id=r" in caplog.text


def test_graph_run_carries_run_id_as_thread_and_metadata_and_a_recursion_limit() -> None:
    seen: dict[str, Any] = {}

    class Spy:
        def __init__(self, graph: Any) -> None:
            self.graph = graph

        def invoke(self, state: Any, config: Any) -> Any:
            seen.update(config)
            return self.graph.invoke(state, config)

    original = agent.build_graph
    try:
        agent.build_graph = lambda model: Spy(original(model))
        run_agent("hi", run_id="abc", model=FakeChatModel())
    finally:
        agent.build_graph = original
    assert seen["configurable"] == {"thread_id": "abc"}
    assert seen["metadata"] == {"run_id": "abc"}
    assert seen["recursion_limit"] == GRAPH_RECURSION_LIMIT


def test_graph_is_a_real_compiled_langgraph_graph() -> None:
    assert build_graph(FakeChatModel()).invoke({"prompt": " a  b ", "draft": ""})["draft"] == (
        "Draft reply to: a b"
    )


def test_draft_is_capped() -> None:
    class Long:
        def complete(self, prompt: str) -> str:
            return "x" * (MAX_DRAFT_CHARS * 3)

    assert len(run_agent("p", run_id="r", model=Long())) == MAX_DRAFT_CHARS


def test_azure_openai_model_sets_output_token_bound_and_deployment() -> None:
    calls: list[dict[str, Any]] = []

    class Completions:
        def create(self, **kwargs: Any) -> Any:
            calls.append(kwargs)
            message = type("M", (), {"content": None})()
            return type("R", (), {"choices": [type("C", (), {"message": message})()]})()

    client = type("C", (), {"chat": type("Chat", (), {"completions": Completions()})()})()
    assert AzureOpenAIChatModel(client, "dep").complete("q") == ""
    assert calls[0]["model"] == "dep" and calls[0]["max_tokens"] == MAX_MODEL_OUTPUT_TOKENS


def test_build_model_modes(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("AGENT_MODEL_MODE", raising=False)
    assert isinstance(build_model(), FakeChatModel)
    monkeypatch.setenv("AGENT_MODEL_MODE", "bogus")
    with pytest.raises(RuntimeError, match="must be"):
        build_model()
    monkeypatch.setenv("AGENT_MODEL_MODE", "azure_openai")
    monkeypatch.delenv("AZURE_OPENAI_ENDPOINT", raising=False)
    with pytest.raises(RuntimeError, match="AZURE_OPENAI_ENDPOINT"):
        build_model()
    monkeypatch.setenv("AZURE_OPENAI_ENDPOINT", "https://oai.example/")
    model = build_model()  # builds clients lazily; makes no network call here
    assert isinstance(model, AzureOpenAIChatModel)


# --- parsing and status helpers --------------------------------------------------------------


def test_parse_run_request_defaults_and_bounds() -> None:
    parsed = parse_run_request(b'{"prompt": "hi"}')
    assert (parsed.prompt, parsed.approval_timeout_seconds) == ("hi", 86400)
    with pytest.raises(RequestError):
        parse_run_request(b'{"prompt": "hi", "approval_timeout_seconds": true}')


def test_parse_decision() -> None:
    assert parse_decision(b'{"approved": false}') is False
    with pytest.raises(RequestError):
        parse_decision(b"")


def test_small_helpers() -> None:
    assert clamp_timeout(120) == 120 and clamp_timeout("x") == 86400
    assert is_approval({"approved": True}) and not is_approval({"approved": "True"})
    assert is_terminal("Completed") and not is_terminal("Running") and not is_terminal(None)
    assert normalize_status(None, None, None) is None
    assert normalize_status("ContinuedAsNew", None, None) == {"status": "running", "stage": None}
