"""Regression coverage for #358: align SDK message encoding with the output
binding example.

enqueue_via_sdk constructed QueueClient without a message encoding policy,
so it sent raw JSON. The Functions Queue binding's default
messageEncoding is base64, so the two producers in this comparison recipe
wrote incompatible wire formats for the same queue under their documented
defaults.

Replaces only the generated REST send operation with an in-process
capture; QueueClient construction, its message encode policy, and the
actual registered HTTP route are all real.
"""

from __future__ import annotations

import base64
from datetime import UTC, datetime, timedelta
import json
import os
from types import SimpleNamespace
from typing import Any
from unittest.mock import patch

from azure.storage.queue import QueueClient

from tests._isolation import load_example_module

EXAMPLE_PATH = "runtime-and-ops/output_binding_vs_sdk"
_FAKE_CONNECTION_STRING = (
    "DefaultEndpointsProtocol=https;AccountName=offline;"
    "AccountKey=b2ZmbGluZQ==;EndpointSuffix=core.windows.net"
)


def _request(body: bytes) -> Any:
    import azure.functions as func

    return func.HttpRequest(
        method="POST",
        url="https://example.invalid/api/enqueue/sdk",
        params={},
        body=body,
        headers={"Content-Type": "application/json"},
    )


def _capturing_queue_client_factory(captured_message_texts: list[str]) -> Any:
    real_from_connection_string = QueueClient.from_connection_string

    def make_client(*, conn_str: str, queue_name: str, **kwargs: Any) -> Any:
        client = real_from_connection_string(conn_str=conn_str, queue_name=queue_name, **kwargs)

        def capture(*, queue_message: Any, **_kwargs: Any) -> Any:
            captured_message_texts.append(queue_message.message_text)
            now = datetime.now(UTC)
            return SimpleNamespace(
                items_property=[
                    SimpleNamespace(
                        message_id="offline",
                        insertion_time=now,
                        expiration_time=now + timedelta(days=1),
                        pop_receipt="offline",
                        time_next_visible=now,
                    )
                ]
            )

        client._client.queue.send_message = capture
        return client

    return make_client


def test_enqueue_via_sdk_sends_base64_encoded_message_text() -> None:
    module = load_example_module(EXAMPLE_PATH)
    handler = next(
        f.get_user_function()
        for f in module.app.get_functions()
        if f.get_function_name() == "enqueue_via_sdk"
    )

    captured: list[str] = []
    with (
        patch.dict(os.environ, {"StorageConnection": _FAKE_CONNECTION_STRING}),
        patch.object(
            QueueClient,
            "from_connection_string",
            side_effect=_capturing_queue_client_factory(captured),
        ),
    ):
        response = handler(req=_request(json.dumps({"task": "demo"}).encode()))

    assert response.status_code == 202
    assert len(captured) == 1

    decoded = base64.b64decode(captured[0], validate=True).decode()
    payload = json.loads(decoded)
    assert payload["task"] == "demo"
    assert payload["method"] == "sdk"
