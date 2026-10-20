"""Regression coverage for #375: preserve Service Bus application property
keys during DLQ replay.

_application_properties_dict applied str(key) to every received property
key. The Python Service Bus SDK can expose received AMQP string keys as
bytes, so str(b"region") produced the Python repr "b'region'" instead of
the original property name "region" -- the replay message silently lost
its routing/processing metadata's identity even though the value survived.

Constructs only a real azure.servicebus.ServiceBusMessage (accepting the
same bytes-keyed mapping a received message exposes) and calls the
recipe's real _build_replay_message(); no receiver or live Service Bus
connection is created.
"""

from __future__ import annotations

from typing import Any

from azure.servicebus import ServiceBusMessage

from tests._isolation import load_example_module

EXAMPLE_PATH = "messaging-and-pubsub/servicebus_dlq_replay"


class _FakeReceivedMessage:
    """Thin wrapper exposing a real ServiceBusMessage's properties plus the
    extra ServiceBusReceivedMessage-only fields _build_replay_message reads
    (delivery_count, dead_letter_reason, partition_key, ...), matching the
    issue's own probe shape without needing a real receiver."""

    def __init__(self, sdk_message: ServiceBusMessage) -> None:
        self.application_properties = sdk_message.application_properties
        self.body = sdk_message.body
        self.content_type = sdk_message.content_type
        self.correlation_id = sdk_message.correlation_id
        self.message_id = sdk_message.message_id
        self.partition_key = sdk_message.partition_key
        self.reply_to = sdk_message.reply_to
        self.reply_to_session_id = sdk_message.reply_to_session_id
        self.session_id = sdk_message.session_id
        self.subject = sdk_message.subject
        self.time_to_live = sdk_message.time_to_live
        self.to = sdk_message.to
        self.dead_letter_reason: str | None = None


def _received_message(application_properties: dict[str | bytes, Any]) -> _FakeReceivedMessage:
    sdk_message = ServiceBusMessage(
        body=b'{"id":"one"}',
        application_properties=application_properties,
        message_id="one",
    )
    return _FakeReceivedMessage(sdk_message)


def test_build_replay_message_preserves_bytes_application_property_keys() -> None:
    module = load_example_module(EXAMPLE_PATH)
    incoming = _received_message({b"region": b"west"})

    outgoing, replay_id = module._build_replay_message(incoming)

    assert outgoing.application_properties["region"] == b"west"
    assert "b'region'" not in outgoing.application_properties
    assert replay_id.startswith("one-replay-")


def test_build_replay_message_preserves_string_application_property_keys() -> None:
    module = load_example_module(EXAMPLE_PATH)
    incoming = _received_message({"region": "west"})

    outgoing, _replay_id = module._build_replay_message(incoming)

    assert outgoing.application_properties["region"] == "west"


def test_build_replay_message_still_adds_replay_markers() -> None:
    module = load_example_module(EXAMPLE_PATH)
    incoming = _received_message({b"region": b"west"})
    incoming.dead_letter_reason = "MaxDeliveryCountExceeded"

    outgoing, _replay_id = module._build_replay_message(incoming)

    assert outgoing.application_properties["replayed_from_dlq"] is True
    assert outgoing.application_properties["dead_letter_reason"] == "MaxDeliveryCountExceeded"
    assert outgoing.application_properties["region"] == b"west"
