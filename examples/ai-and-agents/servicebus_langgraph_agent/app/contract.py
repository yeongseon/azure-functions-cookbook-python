"""The message contract: how a Service Bus message becomes graph input and a thread ID.

Everything here is pure and offline-testable. Error messages name fields, never values, so a
rejected message does not copy producer content into logs.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Any, Final, Protocol

from langchain_core.messages import HumanMessage

MAX_BODY_BYTES: Final = 16 * 1024
MAX_QUESTION_CHARS: Final = 2000
_ID_PATTERN: Final = re.compile(r"[A-Za-z0-9][A-Za-z0-9._:-]{0,63}")
THREAD_PREFIX: Final = "sb:"


class MessageLike(Protocol):
    """The part of ``azure.functions.ServiceBusMessage`` this recipe reads."""

    message_id: str | None

    def get_body(self) -> bytes: ...


class InvalidMessageError(ValueError):
    """The body does not satisfy the contract.

    Redelivery cannot fix a malformed body, so the broker retries it until MaxDeliveryCount and
    then dead-letters it. Validate producers upstream; use the DLQ recipes to inspect and replay.
    """


@dataclass(frozen=True, slots=True)
class AgentRequest:
    request_id: str
    question: str
    conversation_id: str | None


def _identifier(payload: dict[str, Any], field: str) -> str | None:
    value = payload.get(field)
    if value is None:
        return None
    if not isinstance(value, str) or _ID_PATTERN.fullmatch(value) is None:
        raise InvalidMessageError(
            f"field {field!r} must be 1-64 characters of letters, digits, '.', '_', ':' or '-'"
        )
    return value


def parse_request(msg: MessageLike) -> AgentRequest:
    """Validate the JSON body: ``{"request_id", "question", "conversation_id"?}``."""
    body = msg.get_body()
    if len(body) > MAX_BODY_BYTES:
        raise InvalidMessageError(f"body exceeds {MAX_BODY_BYTES} bytes")
    try:
        payload = json.loads(body)
    except (UnicodeDecodeError, ValueError):
        raise InvalidMessageError("body is not valid UTF-8 JSON") from None
    if not isinstance(payload, dict):
        raise InvalidMessageError("body must be a JSON object")
    request_id = _identifier(payload, "request_id")
    if request_id is None:
        raise InvalidMessageError("field 'request_id' is required")
    question = payload.get("question")
    if not isinstance(question, str) or not question.strip():
        raise InvalidMessageError("field 'question' must be a non-empty string")
    if len(question) > MAX_QUESTION_CHARS:
        raise InvalidMessageError(f"field 'question' exceeds {MAX_QUESTION_CHARS} characters")
    return AgentRequest(
        request_id=request_id,
        question=question.strip(),
        conversation_id=_identifier(payload, "conversation_id"),
    )


def map_input(msg: MessageLike) -> dict[str, Any]:
    """``input_mapper``: message -> graph input.

    The human message ``id`` is derived from ``request_id``. LangGraph's ``add_messages`` reducer
    replaces a message that has the same ``id``, so a redelivered message rewrites its own turn
    instead of appending a duplicate to a checkpointed thread.
    """
    request = parse_request(msg)
    return {
        "request_id": request.request_id,
        "messages": [HumanMessage(content=request.question, id=f"{request.request_id}:question")],
    }


def thread_id_for(msg: MessageLike) -> str:
    """``thread_id_factory`` for a non-session queue or subscription.

    ``conversation_id`` selects a shared checkpoint thread; without it each request gets its own
    thread, so a redelivery of the same request always lands on the same thread. IDs are prefixed
    so they cannot collide with HTTP thread IDs. The ID is a partition key chosen by the producer,
    not proof of identity: who may send is decided by Service Bus authorization. In session mode
    do not use this; the adapter uses the message ``session_id`` itself.
    """
    request = parse_request(msg)
    if request.conversation_id is None:
        return f"{THREAD_PREFIX}request:{request.request_id}"
    return f"{THREAD_PREFIX}conversation:{request.conversation_id}"


def session_thread_id(msg: MessageLike) -> str:
    """``thread_id_factory`` for a session-enabled queue: the message ``session_id`` is the thread.

    The trigger is bound with ``is_sessions_enabled`` so Service Bus delivers one session to one
    receiver at a time. A missing or blank ``session_id`` is rejected before the graph runs.
    """
    session_id = getattr(msg, "session_id", None)
    if not isinstance(session_id, str) or not session_id.strip():
        raise InvalidMessageError("session mode requires a non-empty message session_id")
    return session_id
