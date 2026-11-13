from __future__ import annotations

import json
from collections.abc import Callable
from typing import Any

import azure.functions.servicebus as sb_runtime


def make_message(
    payload: dict[str, Any] | bytes,
    *,
    message_id: str = "sb-msg-1",
    session_id: str | None = None,
    delivery_count: int = 1,
) -> sb_runtime.ServiceBusMessage:
    """A real ``azure.functions`` Service Bus message, as the Python worker would build it."""
    body = payload if isinstance(payload, bytes) else json.dumps(payload).encode()
    return sb_runtime.ServiceBusMessage(
        body=body,
        application_properties={},
        user_properties={},
        message_id=message_id,
        session_id=session_id,
        delivery_count=delivery_count,
    )


Request = Callable[..., sb_runtime.ServiceBusMessage]


def request(
    request_id: str = "req-1",
    question: str = "Where is order A-1001?",
    *,
    conversation_id: str | None = None,
    **message_options: Any,
) -> sb_runtime.ServiceBusMessage:
    payload: dict[str, Any] = {"request_id": request_id, "question": question}
    if conversation_id is not None:
        payload["conversation_id"] = conversation_id
    return make_message(payload, **message_options)
