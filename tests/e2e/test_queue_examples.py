"""E2E tests for queue-related examples.

Queue producer has an HTTP endpoint that writes to Azurite queues.
Queue consumer is a trigger-only function (tested indirectly).
output_binding_vs_sdk compares two enqueueing strategies.
"""

from __future__ import annotations

import pytest
import requests

from tests.e2e.conftest import AZURITE_CONN_STR, ensure_azurite_queue, run_func_host

pytestmark = pytest.mark.e2e


# ---------------------------------------------------------------------------
# queue_producer
# ---------------------------------------------------------------------------


class TestQueueProducer:
    """POST /api/enqueue → writes to 'outbound-tasks' queue."""

    EXAMPLE = "messaging-and-pubsub/queue_producer"

    def test_enqueue_valid_payload(self, azurite) -> None:  # noqa: ARG002
        ensure_azurite_queue("outbound-tasks")
        with run_func_host(self.EXAMPLE) as base_url:
            resp = requests.post(
                f"{base_url}/api/enqueue",
                json={"task_type": "email", "payload": {"to": "user@example.com"}},
                timeout=10,
            )
            assert resp.status_code == 202, f"Got {resp.status_code}: {resp.text}"
            data = resp.json()
            assert data["status"] == "accepted"
            assert "message_id" in data

    def test_enqueue_missing_body_returns_400(self, azurite) -> None:  # noqa: ARG002
        ensure_azurite_queue("outbound-tasks")
        with run_func_host(self.EXAMPLE) as base_url:
            resp = requests.post(
                f"{base_url}/api/enqueue",
                data="not json",
                headers={"Content-Type": "text/plain"},
                timeout=10,
            )
            assert resp.status_code == 400


# ---------------------------------------------------------------------------
# output_binding_vs_sdk
# ---------------------------------------------------------------------------


class TestOutputBindingVsSdk:
    """POST /api/enqueue/binding and POST /api/enqueue/sdk."""

    EXAMPLE = "runtime-and-ops/output_binding_vs_sdk"

    def test_enqueue_via_binding(self, azurite) -> None:  # noqa: ARG002
        ensure_azurite_queue("work-items")
        with run_func_host(
            self.EXAMPLE,
            env_vars={"StorageConnection": "UseDevelopmentStorage=true"},
        ) as base_url:
            resp = requests.post(
                f"{base_url}/api/enqueue/binding",
                json={"task": "process-report"},
                timeout=10,
            )
            # binding route returns the JSON directly as string body (200)
            assert resp.status_code == 200

    def test_enqueue_via_sdk(self, azurite) -> None:  # noqa: ARG002
        ensure_azurite_queue("work-items")
        with run_func_host(
            self.EXAMPLE,
            env_vars={
                "StorageConnection": AZURITE_CONN_STR,
            },
        ) as base_url:
            resp = requests.post(
                f"{base_url}/api/enqueue/sdk",
                json={"task": "process-report"},
                timeout=10,
            )
            assert resp.status_code == 202
