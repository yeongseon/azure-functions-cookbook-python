"""Regression coverage for #364: close pending tool calls when the personal
agent reaches its tool-round budget.

The agent's route-to-END branch at the MAX_TOOL_ROUNDS limit left the
model's latest AIMessage (with unanswered tool_calls) as the final
checkpointed message. A valid three-tool-call-round model response
therefore produced an empty final answer and a persisted tool call with
no matching ToolMessage -- invalid chat history per LangGraph's
INVALID_CHAT_HISTORY guidance, which could break a subsequent turn on the
same thread.

Drives the actual exported HTTP route end to end with a deterministic
model stub (substituting only build_model); the real graph, tool node,
and checkpointer all run unmodified.
"""

from __future__ import annotations

import importlib.util
import json
import sys
from types import ModuleType
from typing import Any

import azure.functions as func
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage
import pytest

from tests._isolation import EXAMPLES_DIR, clean_app_modules

EXAMPLE = "ai-and-agents/personal_langgraph_agent"
EXAMPLE_DIR = EXAMPLES_DIR / EXAMPLE


class _ScriptedToolRoundsModel:
    """Requests `tool_rounds` lookup_notes calls, then returns a final answer.

    Also enforces call/reply pairing on every invocation: raises if a human
    message follows an unanswered tool call anywhere in the passed history,
    exposing invalid chat history the same way the issue's probe does.
    """

    def __init__(self, tool_rounds: int) -> None:
        self.tool_rounds = tool_rounds
        self.calls = 0

    def invoke(self, messages: Any) -> AIMessage:
        pending: set[str] = set()
        for message in messages:
            if isinstance(message, AIMessage):
                pending.update(call["id"] for call in message.tool_calls if call["id"] is not None)
            elif isinstance(message, ToolMessage):
                pending.discard(message.tool_call_id)
            elif isinstance(message, HumanMessage) and pending:
                raise ValueError("new user turn preceded replies to " + ",".join(sorted(pending)))

        self.calls += 1
        if self.calls <= self.tool_rounds:
            return AIMessage(
                content="",
                tool_calls=[
                    {
                        "name": "lookup_notes",
                        "args": {"query": "Project Atlas"},
                        "id": f"call-{self.calls}",
                        "type": "tool_call",
                    }
                ],
            )
        return AIMessage(content="Finished looking up the notes.")


def _load_with_scripted_model(
    monkeypatch: pytest.MonkeyPatch, tool_rounds: int, suffix: str
) -> tuple[ModuleType, _ScriptedToolRoundsModel]:
    clean_app_modules()
    monkeypatch.setenv("AGENT_MODEL_MODE", "fake")
    monkeypatch.setenv("AGENT_MEMORY_MODE", "memory")
    monkeypatch.delenv("AZURE_STORAGE_CONNECTION_STRING", raising=False)

    example_dir = str(EXAMPLE_DIR)
    added_to_path = example_dir not in sys.path
    if added_to_path:
        sys.path.insert(0, example_dir)

    # Import the recipe's own model module (not via load_example_module,
    # whose internal clean_app_modules() would wipe this patch before
    # function_app.py re-imports app.core.model) so build_model can be
    # substituted before function_app.py builds the model at import time.
    import app.core.model as model_module  # noqa: PLC0415

    scripted_model = _ScriptedToolRoundsModel(tool_rounds)
    monkeypatch.setattr(model_module, "build_model", lambda settings, tools: scripted_model)

    module_name = f"personal_agent_tool_budget_{suffix}"
    module_path = EXAMPLE_DIR / "function_app.py"
    spec = importlib.util.spec_from_file_location(module_name, module_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)

    if added_to_path:
        sys.path.remove(example_dir)

    return module, scripted_model


def _invoke(module: ModuleType, thread_id: str) -> func.HttpResponse:
    # FunctionApp.get_functions() re-validates name uniqueness against
    # functions_bindings on every call; reset it first so repeated
    # invocations against the same loaded module (as a follow-up turn on
    # the same thread) don't raise a false duplicate-name error.
    module.app.functions_bindings = {}
    functions = {item.get_function_name(): item for item in module.app.get_functions()}
    handler = functions["aflg_personal_agent_invoke"].get_user_function()
    request = func.HttpRequest(
        method="POST",
        url="http://localhost/api/graphs/personal_agent/invoke",
        body=json.dumps(
            {
                "input": {"messages": [{"role": "human", "content": "Look up Project Atlas."}]},
                "config": {"configurable": {"thread_id": thread_id}},
            }
        ).encode(),
        headers={"Content-Type": "application/json"},
    )
    return handler(request)  # type: ignore[no-any-return]


def test_within_budget_two_rounds_leaves_valid_history_and_allows_followup(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    module, scripted_model = _load_with_scripted_model(monkeypatch, tool_rounds=2, suffix="within")
    thread_id = "tool-budget-within"

    response = _invoke(module, thread_id)
    assert response.status_code == 200

    state = module.graph.get_state({"configurable": {"thread_id": thread_id}})
    messages = state.values["messages"]
    requests = {call["id"] for m in messages if isinstance(m, AIMessage) for call in m.tool_calls}
    replies = {m.tool_call_id for m in messages if isinstance(m, ToolMessage)}
    assert requests == replies
    assert messages[-1].content == "Finished looking up the notes."

    followup = _invoke(module, thread_id)
    assert followup.status_code == 200
    assert scripted_model.calls > 2


def test_exceeding_budget_closes_pending_calls_and_leaves_final_answer(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    module, _scripted_model = _load_with_scripted_model(
        monkeypatch, tool_rounds=3, suffix="exceeded"
    )
    thread_id = "tool-budget-exceeded"

    response = _invoke(module, thread_id)
    assert response.status_code == 200

    state = module.graph.get_state({"configurable": {"thread_id": thread_id}})
    messages = state.values["messages"]
    requests = {call["id"] for m in messages if isinstance(m, AIMessage) for call in m.tool_calls}
    replies = {m.tool_call_id for m in messages if isinstance(m, ToolMessage)}

    assert requests - replies == set()
    assert messages[-1].content != ""
    assert isinstance(messages[-1], AIMessage)

    followup = _invoke(module, thread_id)
    assert followup.status_code == 200
