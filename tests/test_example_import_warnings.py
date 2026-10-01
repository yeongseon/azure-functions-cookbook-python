from __future__ import annotations

import warnings

import pytest

from tests._isolation import load_example_module


@pytest.mark.parametrize(
    "example_path",
    [
        "ai-and-agents/ai_image_generation",
        "ai-and-agents/embedding_vector_search",
        "ai-and-agents/langgraph_agent",
        "ai-and-agents/langgraph_rag_agent",
        "ai-and-agents/langgraph_tool_use",
        "ai-and-agents/openai_direct_chat",
        "ai-and-agents/rag_knowledge_api",
        "ai-and-agents/streaming_ai_response",
        "apis-and-ingress/apim_function_backend",
        "data-and-pipelines/db_input_output",
        "realtime/websocket_proxy",
        "security-and-tenancy/tenant_isolation",
    ],
)
def test_example_import_emits_no_runtime_warning(example_path: str) -> None:
    with warnings.catch_warnings():
        warnings.simplefilter("error", RuntimeWarning)
        load_example_module(example_path)
