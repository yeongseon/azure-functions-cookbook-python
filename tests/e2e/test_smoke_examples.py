"""Smoke tests for examples that cannot be fully E2E tested locally.

These tests verify that each example's ``function_app.py`` module can be
imported without errors, confirming that the Blueprint structure is valid
and all dependencies are resolvable.

Non-emulatable triggers include:
- Service Bus (no Azurite support)
- Event Hub (no Azurite support)
- Cosmos DB change feed (no Azurite support)
- Timer/cron (no HTTP endpoint)
- Managed Identity examples (require real Azure credentials)
- MCP Server (requires FUNCTION-level auth key)
- host.json / concurrency tuning (timer + queue only)
- Retry and idempotency (timer + queue only)
"""

from __future__ import annotations

import pytest

from tests.e2e.conftest import import_function_app

pytestmark = pytest.mark.smoke

# ---------------------------------------------------------------------------
# Service Bus
# ---------------------------------------------------------------------------


class TestServiceBusWorkerSmoke:
    def test_module_imports(self) -> None:
        module = import_function_app("messaging-and-pubsub/servicebus_worker")
        assert hasattr(module, "app")


# ---------------------------------------------------------------------------
# Event Hub
# ---------------------------------------------------------------------------


class TestEventHubConsumerSmoke:
    def test_module_imports(self) -> None:
        module = import_function_app("streams-and-telemetry/eventhub_consumer")
        assert hasattr(module, "app")


# ---------------------------------------------------------------------------
# Cosmos DB
# ---------------------------------------------------------------------------


class TestChangeFeedProcessorSmoke:
    def test_module_imports(self) -> None:
        module = import_function_app("data-and-pipelines/change_feed_processor")
        assert hasattr(module, "app")


# ---------------------------------------------------------------------------
# Timer
# ---------------------------------------------------------------------------


class TestTimerCronJobSmoke:
    def test_module_imports(self) -> None:
        module = import_function_app("scheduled-and-background/timer_cron_job")
        assert hasattr(module, "app")


class TestDurableTimerReminderSmoke:
    def test_module_imports(self) -> None:
        module = import_function_app("scheduled-and-background/durable_timer_reminder")
        assert hasattr(module, "app")


class TestQueueScheduledDispatchSmoke:
    def test_module_imports(self) -> None:
        module = import_function_app("scheduled-and-background/queue_scheduled_dispatch")
        assert hasattr(module, "app")


# ---------------------------------------------------------------------------
# Managed Identity
# ---------------------------------------------------------------------------


class TestManagedIdentityStorageSmoke:
    def test_module_imports(self) -> None:
        module = import_function_app("security-and-tenancy/managed_identity_storage")
        assert hasattr(module, "app")


class TestManagedIdentityServiceBusSmoke:
    def test_module_imports(self) -> None:
        module = import_function_app("security-and-tenancy/managed_identity_servicebus")
        assert hasattr(module, "app")


# ---------------------------------------------------------------------------
# host.json / Concurrency tuning
# ---------------------------------------------------------------------------


class TestHostJsonTuningSmoke:
    def test_module_imports(self) -> None:
        module = import_function_app("runtime-and-ops/host_json_tuning")
        assert hasattr(module, "app")


class TestConcurrencyTuningSmoke:
    def test_module_imports(self) -> None:
        module = import_function_app("runtime-and-ops/concurrency_tuning")
        assert hasattr(module, "app")


# ---------------------------------------------------------------------------
# Retry and Idempotency
# ---------------------------------------------------------------------------


class TestRetryAndIdempotencySmoke:
    def test_module_imports(self) -> None:
        module = import_function_app("reliability/retry_and_idempotency")
        assert hasattr(module, "app")


# ---------------------------------------------------------------------------
# AI / MCP Server
# ---------------------------------------------------------------------------


class TestMcpServerSmoke:
    def test_module_imports(self) -> None:
        module = import_function_app("ai-and-agents/mcp_server_example")
        assert hasattr(module, "app")


class TestSignalRGroupChatSmoke:
    @pytest.mark.xfail(reason="SignalR bindings not available in azure-functions < 1.25")
    def test_module_imports(self) -> None:
        module = import_function_app("realtime/signalr_group_chat")
        assert hasattr(module, "app")


class TestWebsocketProxySmoke:
    def test_module_imports(self) -> None:
        module = import_function_app("realtime/websocket_proxy")
        assert hasattr(module, "app")


class TestBlobThumbnailGeneratorSmoke:
    def test_module_imports(self) -> None:
        module = import_function_app("blob-and-file-triggers/blob_thumbnail_generator")
        assert hasattr(module, "app")


class TestBlobCsvToTableSmoke:
    def test_module_imports(self) -> None:
        module = import_function_app("blob-and-file-triggers/blob_csv_to_table")
        assert hasattr(module, "app")


class TestApimFunctionBackendSmoke:
    def test_module_imports(self) -> None:
        module = import_function_app("apis-and-ingress/apim_function_backend")
        assert hasattr(module, "app")


class TestClaimCheckPatternSmoke:
    def test_module_imports(self) -> None:
        module = import_function_app("messaging-and-pubsub/claim_check_pattern")
        assert hasattr(module, "app")


class TestDurableSingletonMonitorSmoke:
    def test_module_imports(self) -> None:
        module = import_function_app("orchestration-and-workflows/durable_singleton_monitor")
        assert hasattr(module, "app")
