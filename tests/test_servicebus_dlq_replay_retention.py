"""Regression tests for #376: dead-letter inspection must not consume
messages before an operator can replay them.

No Azure services are contacted: ``ServiceBusClient`` is patched with an
in-process fake receiver/sender, matching the issue's own offline
reproduction methodology.
"""

from __future__ import annotations

import os
from types import SimpleNamespace
from typing import Any
from unittest.mock import patch

from tests._isolation import load_example_module

EXAMPLE_PATH = "messaging-and-pubsub/servicebus_dlq_replay"


class _FakeMessage:
    def __init__(
        self,
        *,
        message_id: str,
        body: bytes,
        dead_letter_reason: str = "MaxDeliveryCountExceeded",
        delivery_count: int = 10,
    ) -> None:
        self.message_id = message_id
        self.body = body
        self.application_properties: dict[str, Any] = {}
        self.content_type = "application/json"
        self.correlation_id = "corr-1"
        self.dead_letter_reason = dead_letter_reason
        self.dead_letter_error_description = "offline fixture"
        self.delivery_count = delivery_count
        self.partition_key = None
        self.reply_to = None
        self.reply_to_session_id = None
        self.session_id = None
        self.subject = None
        self.time_to_live = None
        self.to = None


class _FakeReceiver:
    def __init__(self, messages: list[_FakeMessage]) -> None:
        self._messages = messages
        self.completed: list[_FakeMessage] = []
        self.peek_called = False
        self.receive_called = False

    def __enter__(self) -> _FakeReceiver:
        return self

    def __exit__(self, *exc: object) -> None:
        return None

    def peek_messages(self, *, max_message_count: int) -> list[_FakeMessage]:
        self.peek_called = True
        return list(self._messages[:max_message_count])

    def receive_messages(self, *, max_message_count: int, max_wait_time: int) -> list[_FakeMessage]:
        self.receive_called = True
        return list(self._messages[:max_message_count])

    def complete_message(self, message: _FakeMessage) -> None:
        self.completed.append(message)
        self._messages.remove(message)


class _FakeSender:
    def __init__(self) -> None:
        self.sent: list[object] = []

    def __enter__(self) -> _FakeSender:
        return self

    def __exit__(self, *exc: object) -> None:
        return None

    def send_messages(self, message: object) -> None:
        self.sent.append(message)


class _FakeClient:
    def __init__(self, receiver: _FakeReceiver, sender: _FakeSender) -> None:
        self._receiver = receiver
        self._sender = sender

    def __enter__(self) -> _FakeClient:
        return self

    def __exit__(self, *exc: object) -> None:
        return None

    def get_queue_receiver(self, **kwargs: object) -> _FakeReceiver:
        return self._receiver

    def get_queue_sender(self, **kwargs: object) -> _FakeSender:
        return self._sender


def test_inspect_endpoint_does_not_consume_messages() -> None:
    """GET /servicebus/dlq/inspect must peek, never complete, a message --
    it must remain available to replay_dead_letter_queue afterward."""
    module = load_example_module(EXAMPLE_PATH)
    message = _FakeMessage(message_id="ord-42", body=b'{"order_id": "ord-42"}')
    receiver = _FakeReceiver([message])
    sender = _FakeSender()
    client = _FakeClient(receiver, sender)

    with (
        patch.dict(os.environ, {"ServiceBusConnection": "offline-fake"}),
        patch.object(module.ServiceBusClient, "from_connection_string", return_value=client),
    ):
        req = SimpleNamespace(params={}, get_json=lambda: {})
        response = module.inspect_dead_letter_queue(req)

    assert receiver.peek_called is True
    assert receiver.receive_called is False
    assert receiver.completed == []
    assert message in receiver._messages
    assert response.status_code == 200


def test_module_no_longer_registers_a_dlq_bound_trigger() -> None:
    """The module must not expose any Service Bus trigger binding on the
    DLQ sub-queue -- a trigger that returns successfully is auto-completed
    under the host's default autoCompleteMessages=true, permanently
    discarding the message before an operator could inspect or replay it
    (#376)."""
    module = load_example_module(EXAMPLE_PATH)
    functions = module.app.get_functions()
    function_names = {function.get_function_name() for function in functions}

    assert "log_dead_lettered_message" not in function_names
    assert "inspect_dead_letter_queue" in function_names
    assert "replay_dead_letter_queue" in function_names

    for function in functions:
        for binding in function.get_bindings():
            assert binding.type != "serviceBusTrigger"


def test_replay_still_sends_before_completing() -> None:
    """Replay must publish the repaired message before completing (removing)
    the original DLQ copy, so a failed publish leaves it replayable."""
    module = load_example_module(EXAMPLE_PATH)
    message = _FakeMessage(message_id="ord-43", body=b'{"order_id": "ord-43"}')
    receiver = _FakeReceiver([message])
    sender = _FakeSender()
    client = _FakeClient(receiver, sender)

    with (
        patch.dict(os.environ, {"ServiceBusConnection": "offline-fake"}),
        patch.object(module.ServiceBusClient, "from_connection_string", return_value=client),
    ):
        req = SimpleNamespace(params={}, get_json=lambda: {})
        response = module.replay_dead_letter_queue(req, context=SimpleNamespace())

    assert len(sender.sent) == 1
    assert receiver.completed == [message]
    assert response.status_code == 200
