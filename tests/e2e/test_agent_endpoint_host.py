"""Host-backed gate for azure-functions-langgraph endpoint registration.

Starts the personal LangGraph agent recipe (fake model, in-memory thread memory) on a real Core
Tools host and calls the routes the toolkit registers. Local-host evidence only; no Azure
resource or credential is used.
"""

from __future__ import annotations

import pytest
import requests

from tests.e2e.conftest import run_func_host

pytestmark = [pytest.mark.e2e, pytest.mark.compat, pytest.mark.agent_endpoint]

EXAMPLE = "ai-and-agents/personal_langgraph_agent"


def test_registered_routes_answer_on_the_host() -> None:
    message = {"role": "human", "content": "What is planned for Project Atlas?"}
    body = {"input": {"messages": [message]}, "config": {"configurable": {"thread_id": "compat"}}}
    with run_func_host(EXAMPLE) as base_url:
        health = requests.get(f"{base_url}/api/health", timeout=10)
        invoked = requests.post(
            f"{base_url}/api/graphs/personal_agent/invoke", json=body, timeout=30
        )

    assert health.status_code == 200
    assert invoked.status_code == 200
    assert "human_turns=1" in invoked.text
