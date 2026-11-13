"""The agent work, kept free of Durable so it runs from a plain activity.

A compiled LangGraph graph drafts a reply. The Durable activity calls ``run_agent``; the
orchestrator never imports this module's model or graph code.
"""

from __future__ import annotations

import os
from typing import Any, Protocol, TypedDict

from langgraph.graph import END, START, StateGraph

from app.core.limits import (
    GRAPH_RECURSION_LIMIT,
    MAX_DRAFT_CHARS,
    MAX_MODEL_OUTPUT_TOKENS,
    MODEL_TIMEOUT_SECONDS,
)


class ChatModel(Protocol):
    def complete(self, prompt: str) -> str: ...


class FakeChatModel:
    """Deterministic, credential-free stand-in used by tests and ``AGENT_MODEL_MODE=fake``."""

    def complete(self, prompt: str) -> str:
        return f"Draft reply to: {prompt}"


class AzureOpenAIChatModel:
    """Azure OpenAI chat completion with explicit timeout and output-token bounds."""

    def __init__(self, client: Any, deployment: str) -> None:
        self._client = client
        self._deployment = deployment

    def complete(self, prompt: str) -> str:
        response = self._client.chat.completions.create(
            model=self._deployment,
            max_tokens=MAX_MODEL_OUTPUT_TOKENS,
            messages=[
                {"role": "system", "content": "Draft a short, factual reply for human review."},
                {"role": "user", "content": prompt},
            ],
        )
        return str(response.choices[0].message.content or "")


def build_model() -> ChatModel:
    """Pick the model from ``AGENT_MODEL_MODE``; a bad configuration fails instead of faking."""
    mode = os.getenv("AGENT_MODEL_MODE", "fake")
    if mode == "fake":
        return FakeChatModel()
    if mode != "azure_openai":
        raise RuntimeError("AGENT_MODEL_MODE must be 'fake' or 'azure_openai'")
    endpoint = os.getenv("AZURE_OPENAI_ENDPOINT", "").rstrip("/")
    if not endpoint:
        raise RuntimeError("AZURE_OPENAI_ENDPOINT is required when AGENT_MODEL_MODE=azure_openai")
    # Local imports keep the fake mode and the tests free of the Azure SDKs.
    from azure.identity import DefaultAzureCredential, get_bearer_token_provider
    from openai import OpenAI

    token_provider = get_bearer_token_provider(
        DefaultAzureCredential(), "https://ai.azure.com/.default"
    )
    client = OpenAI(
        base_url=f"{endpoint}/openai/v1/",
        api_key=token_provider,
        timeout=MODEL_TIMEOUT_SECONDS,
        max_retries=0,  # retries belong to the Durable retry policy, not hidden inside the SDK
    )
    return AzureOpenAIChatModel(client, os.getenv("AZURE_OPENAI_CHAT_DEPLOYMENT", "gpt-4o-mini"))


class DraftState(TypedDict):
    prompt: str
    draft: str


def build_graph(model: ChatModel) -> Any:
    """Two-node graph: normalise the prompt, then ask the model for a draft."""

    def normalise(state: DraftState) -> dict[str, str]:
        return {"prompt": " ".join(state["prompt"].split())}

    def write(state: DraftState) -> dict[str, str]:
        return {"draft": model.complete(state["prompt"])}

    builder = StateGraph(DraftState)
    builder.add_node("normalise", normalise)
    builder.add_node("write", write)
    builder.add_edge(START, "normalise")
    builder.add_edge("normalise", "write")
    builder.add_edge("write", END)
    return builder.compile()


def run_agent(prompt: str, *, run_id: str, model: ChatModel) -> str:
    """Run the graph once and return a draft capped at ``MAX_DRAFT_CHARS``.

    ``run_id`` (the Durable instance id) is attached as the LangGraph thread id and run metadata so
    a LangGraph run can be matched to its orchestration without logging the prompt or the draft.
    The graph has no checkpointer, so the thread id is a label here, not stored state.
    """
    result = build_graph(model).invoke(
        {"prompt": prompt, "draft": ""},
        config={
            "recursion_limit": GRAPH_RECURSION_LIMIT,
            "configurable": {"thread_id": run_id},
            "metadata": {"run_id": run_id},
            "run_name": "durable_agent_draft",
        },
    )
    return str(result["draft"])[:MAX_DRAFT_CHARS]
