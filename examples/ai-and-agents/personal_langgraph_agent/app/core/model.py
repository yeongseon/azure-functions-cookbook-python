from __future__ import annotations

import os
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Protocol

from langchain_core.messages import AIMessage, BaseMessage, ToolMessage
from langchain_core.tools import BaseTool

from app.core.settings import AgentSettings, load_azure_openai_settings


class ChatModel(Protocol):
    def invoke(self, messages: Sequence[BaseMessage]) -> AIMessage: ...


@dataclass(frozen=True, slots=True)
class FakeScript:
    tool_name: str
    query: str = "Project Atlas"


class StateAwareFakeModel:
    def __init__(self, script: FakeScript) -> None:
        self._script = script

    def invoke(self, messages: Sequence[BaseMessage]) -> AIMessage:
        human_turns = sum(message.type == "human" for message in messages)
        tool_results = [message for message in messages if isinstance(message, ToolMessage)]
        if tool_results:
            result = tool_results[-1]
            return AIMessage(
                content=(
                    f"[fake model] {self._script.tool_name}(query={self._script.query!r}) "
                    f"returned: {result.content}; human_turns={human_turns}"
                )
            )
        return AIMessage(
            content="",
            tool_calls=[
                {
                    "name": self._script.tool_name,
                    "args": {"query": self._script.query},
                    "id": f"fake-call-{human_turns}",
                    "type": "tool_call",
                }
            ],
        )


def build_model(settings: AgentSettings, tools: Sequence[BaseTool]) -> ChatModel:
    azure = load_azure_openai_settings(settings.model_mode)
    if azure is None:
        script = FakeScript(os.getenv("PERSONAL_AGENT_FAKE_TOOL_NAME", "lookup_notes"))
        available = {tool.name for tool in tools}
        if script.tool_name not in available:
            raise RuntimeError(
                f"Fake script requests {script.tool_name!r}, but tools are {sorted(available)!r}; "
                "update PERSONAL_AGENT_FAKE_TOOL_NAME when replacing the sample tool"
            )
        return StateAwareFakeModel(script)

    from langchain_openai import AzureChatOpenAI

    common = {
        "azure_endpoint": azure.endpoint,
        "azure_deployment": azure.deployment,
        "api_version": azure.api_version,
        "timeout": settings.model_timeout_seconds,
        "max_retries": 1,
    }
    if azure.use_entra_id and azure.api_key is None:
        from azure.identity import DefaultAzureCredential, get_bearer_token_provider

        common["azure_ad_token_provider"] = get_bearer_token_provider(
            DefaultAzureCredential(), "https://cognitiveservices.azure.com/.default"
        )
    else:
        common["api_key"] = azure.api_key
    live_model: ChatModel = AzureChatOpenAI(**common).bind_tools(tools)
    return live_model
