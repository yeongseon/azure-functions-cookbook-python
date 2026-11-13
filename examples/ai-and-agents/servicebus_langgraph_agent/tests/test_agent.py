from __future__ import annotations

import sys
from collections.abc import Sequence
from types import ModuleType
from typing import Any

import pytest
from langchain_core.messages import AIMessage, BaseMessage

from app.agent import (
    SAMPLE_ORDERS,
    FakeModel,
    build_graph,
    build_model,
    build_tool,
    final_answer,
    lookup_order_status,
)
from app.settings import (
    AgentSettings,
    ModelMode,
    load_settings,
)


def _run(graph: object, question: str, request_id: str = "r1") -> dict[str, object]:
    from langchain_core.messages import HumanMessage

    result = graph.invoke(  # type: ignore[attr-defined]
        {
            "request_id": request_id,
            "messages": [HumanMessage(content=question, id=f"{request_id}:question")],
        },
        config={"configurable": {"thread_id": "t"}},
    )
    return dict(result)


def test_tool_is_read_only_sample_data() -> None:
    assert "shipped" in lookup_order_status("a-1001")
    assert lookup_order_status("Z-0") == "no such order [sample data]"
    assert set(SAMPLE_ORDERS) == {"A-1001", "A-1002"}


def test_fake_model_calls_the_tool_then_answers() -> None:
    tool = build_tool()
    graph = build_graph(FakeModel(), tool)

    answer = final_answer(_run(graph, "Where is order A-1001?")).text

    assert "shipped, arriving Tuesday" in answer


def test_fake_model_answers_without_a_tool_when_no_order_id() -> None:
    graph = build_graph(FakeModel(), build_tool())

    assert "Send an order ID" in final_answer(_run(graph, "hello")).text


def test_unknown_tool_call_fails_loudly() -> None:
    class RogueModel:
        def invoke(self, messages: Sequence[BaseMessage]) -> AIMessage:
            return AIMessage(
                content="",
                tool_calls=[
                    {"name": "delete_everything", "args": {}, "id": "c", "type": "tool_call"}
                ],
            )

    graph = build_graph(RogueModel(), build_tool())

    with pytest.raises(RuntimeError, match="unknown tool"):
        _run(graph, "go")


def test_tool_calls_on_the_final_turn_are_dropped() -> None:
    class LoopingModel:
        def invoke(self, messages: Sequence[BaseMessage]) -> AIMessage:
            return AIMessage(
                content="",
                tool_calls=[
                    {
                        "name": "lookup_order_status",
                        "args": {"order_id": "A-1001"},
                        "id": "c",
                        "type": "tool_call",
                    }
                ],
            )

    graph = build_graph(LoopingModel(), build_tool())

    assert final_answer(_run(graph, "go")).text == "I could not complete this request."


def test_final_answer_requires_an_assistant_message() -> None:
    with pytest.raises(RuntimeError, match="without an assistant answer"):
        final_answer({"messages": []})


def test_settings_defaults_to_the_credential_free_fake(monkeypatch: pytest.MonkeyPatch) -> None:
    for name in ("AGENT_MODEL_MODE", "SERVICEBUS_QUEUE_NAME", "SERVICEBUS_SESSIONS"):
        monkeypatch.delenv(name, raising=False)

    settings = load_settings()

    assert settings.model_mode is ModelMode.FAKE
    assert (settings.queue_name, settings.sessions) == ("agent-requests", False)
    assert isinstance(build_model(settings, build_tool()), FakeModel)


def test_unknown_model_mode_does_not_fall_back_to_fake(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("AGENT_MODEL_MODE", "typo")

    with pytest.raises(ValueError):
        load_settings()


@pytest.mark.parametrize("value", ["0", "-1", "nan", "inf"])
def test_model_timeout_must_be_finite_and_positive(
    monkeypatch: pytest.MonkeyPatch, value: str
) -> None:
    monkeypatch.setenv("AGENT_MODEL_TIMEOUT_SECONDS", value)

    with pytest.raises(RuntimeError, match="greater than zero"):
        load_settings()


def test_live_mode_lists_missing_settings_by_name(monkeypatch: pytest.MonkeyPatch) -> None:
    for name in (
        "AZURE_OPENAI_ENDPOINT",
        "AZURE_OPENAI_DEPLOYMENT",
        "AZURE_OPENAI_API_KEY",
        "AZURE_OPENAI_USE_ENTRA_ID",
    ):
        monkeypatch.delenv(name, raising=False)
    settings = AgentSettings(ModelMode.AZURE_OPENAI, 30.0, "q", False)

    with pytest.raises(RuntimeError) as error:
        build_model(settings, build_tool())

    message = str(error.value)
    assert "AZURE_OPENAI_ENDPOINT" in message
    assert "AZURE_OPENAI_DEPLOYMENT" in message
    assert "AZURE_OPENAI_API_KEY or AZURE_OPENAI_USE_ENTRA_ID" in message


class _RecordingAzureChat:
    """Stands in for ``langchain_openai.AzureChatOpenAI`` so wiring is checked without the SDK."""

    instances: list[_RecordingAzureChat] = []

    def __init__(self, **kwargs: Any) -> None:
        self.kwargs = kwargs
        self.bound: list[Any] = []
        type(self).instances.append(self)

    def bind_tools(self, tools: list[Any]) -> _RecordingAzureChat:
        self.bound = tools
        return self


@pytest.fixture
def recording_client(monkeypatch: pytest.MonkeyPatch) -> type[_RecordingAzureChat]:
    _RecordingAzureChat.instances = []
    module = ModuleType("langchain_openai")
    module.AzureChatOpenAI = _RecordingAzureChat  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "langchain_openai", module)
    monkeypatch.setenv("AZURE_OPENAI_ENDPOINT", "https://example.openai.azure.com")
    monkeypatch.setenv("AZURE_OPENAI_DEPLOYMENT", "agent")
    monkeypatch.delenv("AZURE_OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("AZURE_OPENAI_USE_ENTRA_ID", raising=False)
    return _RecordingAzureChat


def test_live_mode_uses_an_explicit_key_and_binds_the_tool(
    monkeypatch: pytest.MonkeyPatch, recording_client: type[_RecordingAzureChat]
) -> None:
    monkeypatch.setenv("AZURE_OPENAI_API_KEY", "test-key")
    settings = AgentSettings(ModelMode.AZURE_OPENAI, 12.0, "q", False)
    tool = build_tool()

    build_model(settings, tool)

    (client,) = recording_client.instances
    assert client.kwargs["azure_deployment"] == "agent"
    assert client.kwargs["api_key"] == "test-key"
    assert client.kwargs["timeout"] == 12.0
    assert client.bound == [tool]


def test_live_mode_can_use_entra_id_without_a_key(
    monkeypatch: pytest.MonkeyPatch, recording_client: type[_RecordingAzureChat]
) -> None:
    monkeypatch.setenv("AZURE_OPENAI_USE_ENTRA_ID", "true")
    settings = AgentSettings(ModelMode.AZURE_OPENAI, 30.0, "q", False)

    # Token acquisition is lazy, so no credential or network is needed to build the client.
    build_model(settings, build_tool())

    (client,) = recording_client.instances
    assert callable(client.kwargs["azure_ad_token_provider"])
    assert "api_key" not in client.kwargs
