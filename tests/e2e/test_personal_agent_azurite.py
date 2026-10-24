"""Azurite e2e test for the personal LangGraph agent's Blob-backed thread memory."""

from __future__ import annotations

import uuid

import pytest

from tests.e2e.conftest import AZURITE_CONN_STR
from tests.test_personal_langgraph_agent import _invoke, _load, _message_content

pytestmark = pytest.mark.e2e


@pytest.mark.usefixtures("azurite")
def test_azurite_state_survives_app_recreation(monkeypatch: pytest.MonkeyPatch) -> None:
    """Azurite: a recreated app and checkpointer still see the thread's earlier turn."""
    # Given
    settings = {
        "AGENT_MEMORY_MODE": "blob",
        "AZURE_STORAGE_CONNECTION_STRING": AZURITE_CONN_STR,
        "LANGGRAPH_BLOB_CONTAINER": f"personal-agent-test-{uuid.uuid4().hex}",
        "LANGGRAPH_AUTO_CREATE_STORAGE": "true",
    }
    first = _load(monkeypatch, **settings)
    _invoke(first, "What is planned for Project Atlas?", "restart-thread")

    # When
    second = _load(monkeypatch, **settings)
    _, payload = _invoke(second, "Check Project Atlas again", "restart-thread")

    # Then
    assert _message_content(payload, "ai")[-1].endswith("human_turns=2")
