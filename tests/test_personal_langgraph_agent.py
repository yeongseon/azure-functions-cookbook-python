from __future__ import annotations

import json
import sys
from types import ModuleType
from typing import Any

import azure.functions as func
import pytest

from tests._isolation import EXAMPLES_DIR, clean_app_modules, load_example_module

EXAMPLE = "ai-and-agents/personal_langgraph_agent"
EXAMPLE_DIR = EXAMPLES_DIR / EXAMPLE
MODEL_ENV = (
    "AGENT_MODEL_MODE",
    "AZURE_OPENAI_ENDPOINT",
    "AZURE_OPENAI_DEPLOYMENT",
    "AZURE_OPENAI_API_KEY",
    "AZURE_OPENAI_USE_ENTRA_ID",
    "PERSONAL_AGENT_FAKE_TOOL_NAME",
)


def _load(monkeypatch: pytest.MonkeyPatch, **settings: str) -> ModuleType:
    clean_app_modules()
    for name in (*MODEL_ENV, "AGENT_MEMORY_MODE", "AZURE_STORAGE_CONNECTION_STRING"):
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setenv("AGENT_MODEL_MODE", "fake")
    monkeypatch.setenv("AGENT_MEMORY_MODE", "memory")
    for name, value in settings.items():
        monkeypatch.setenv(name, value)
    return load_example_module(EXAMPLE)


def _invoke(module: ModuleType, message: str, thread_id: str) -> tuple[int, dict[str, Any]]:
    module.app.functions_bindings = {}
    functions = {item.get_function_name(): item for item in module.app.get_functions()}
    handler = functions["aflg_personal_agent_invoke"].get_user_function()
    request = func.HttpRequest(
        method="POST",
        url="http://localhost/api/graphs/personal_agent/invoke",
        body=json.dumps(
            {
                "input": {"messages": [{"role": "human", "content": message}]},
                "config": {
                    "configurable": {"thread_id": thread_id},
                    "recursion_limit": 10_000,
                },
            }
        ).encode(),
        headers={"Content-Type": "application/json"},
    )
    response = handler(request)
    return response.status_code, json.loads(response.get_body())


def _message_content(payload: dict[str, Any], message_type: str) -> list[str]:
    messages = payload["output"]["messages"]
    return [str(item["content"]) for item in messages if item["type"] == message_type]


def test_exported_route_executes_real_tool_loop(monkeypatch: pytest.MonkeyPatch) -> None:
    # Given
    module = _load(monkeypatch)

    # When
    status, payload = _invoke(module, "What is planned for Project Atlas?", "tool-proof")

    # Then
    assert status == 200
    assert _message_content(payload, "tool") == [
        "Project Atlas: prepare the launch checklist by Friday. [sample data]"
    ]
    assert _message_content(payload, "ai")[-1] == (
        "[fake model] lookup_notes(query='Project Atlas') returned: "
        "Project Atlas: prepare the launch checklist by Friday. [sample data]; human_turns=1"
    )


def test_thread_memory_is_preserved_and_isolated(monkeypatch: pytest.MonkeyPatch) -> None:
    # Given
    module = _load(monkeypatch)
    _invoke(module, "What is planned for Project Atlas?", "same-thread")

    # When
    _, follow_up = _invoke(module, "Check Project Atlas again", "same-thread")
    _, isolated = _invoke(module, "Check Project Atlas", "other-thread")

    # Then
    assert _message_content(follow_up, "ai")[-1].endswith("human_turns=2")
    assert _message_content(isolated, "ai")[-1].endswith("human_turns=1")


def test_real_mode_lists_only_missing_setting_names(monkeypatch: pytest.MonkeyPatch) -> None:
    # Given
    monkeypatch.setenv("AGENT_MODEL_MODE", "azure_openai")
    monkeypatch.setenv("AGENT_MEMORY_MODE", "memory")
    for name in MODEL_ENV[1:]:
        monkeypatch.delenv(name, raising=False)

    # When / Then
    with pytest.raises(RuntimeError) as exc_info:
        load_example_module(EXAMPLE)
    message = str(exc_info.value)
    assert message == (
        "Missing Azure OpenAI settings: AZURE_OPENAI_ENDPOINT, AZURE_OPENAI_DEPLOYMENT, "
        "AZURE_OPENAI_API_KEY or AZURE_OPENAI_USE_ENTRA_ID"
    )


def test_fake_tool_name_mismatch_is_helpful(monkeypatch: pytest.MonkeyPatch) -> None:
    # Given / When / Then
    with pytest.raises(RuntimeError, match="update PERSONAL_AGENT_FAKE_TOOL_NAME"):
        _load(monkeypatch, PERSONAL_AGENT_FAKE_TOOL_NAME="renamed_lookup")


def test_missing_adapter_package_is_not_replaced(monkeypatch: pytest.MonkeyPatch) -> None:
    # Given
    source = (EXAMPLE_DIR / "function_app.py").read_text()
    for name in tuple(sys.modules):
        if name.startswith("azure_functions_langgraph"):
            monkeypatch.delitem(sys.modules, name)
    monkeypatch.setitem(sys.modules, "azure_functions_langgraph", None)

    # When / Then
    assert "Fallback" not in source
    with pytest.raises(ModuleNotFoundError):
        _load(monkeypatch)
