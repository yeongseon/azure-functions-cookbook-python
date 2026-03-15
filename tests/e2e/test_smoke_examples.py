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
        module = import_function_app("servicebus/servicebus_worker")
        assert hasattr(module, "app")


# ---------------------------------------------------------------------------
# Event Hub
# ---------------------------------------------------------------------------


class TestEventHubConsumerSmoke:
    def test_module_imports(self) -> None:
        module = import_function_app("eventhub/eventhub_consumer")
        assert hasattr(module, "app")


# ---------------------------------------------------------------------------
# Cosmos DB
# ---------------------------------------------------------------------------


class TestChangeFeedProcessorSmoke:
    def test_module_imports(self) -> None:
        module = import_function_app("cosmosdb/change_feed_processor")
        assert hasattr(module, "app")


# ---------------------------------------------------------------------------
# Timer
# ---------------------------------------------------------------------------


class TestTimerCronJobSmoke:
    def test_module_imports(self) -> None:
        module = import_function_app("timer/timer_cron_job")
        assert hasattr(module, "app")


# ---------------------------------------------------------------------------
# Managed Identity
# ---------------------------------------------------------------------------


class TestManagedIdentityStorageSmoke:
    def test_module_imports(self) -> None:
        module = import_function_app("recipes/managed_identity_storage")
        assert hasattr(module, "app")


class TestManagedIdentityServiceBusSmoke:
    def test_module_imports(self) -> None:
        module = import_function_app("recipes/managed_identity_servicebus")
        assert hasattr(module, "app")


# ---------------------------------------------------------------------------
# host.json / Concurrency tuning
# ---------------------------------------------------------------------------


class TestHostJsonTuningSmoke:
    def test_module_imports(self) -> None:
        module = import_function_app("recipes/host_json_tuning")
        assert hasattr(module, "app")


class TestConcurrencyTuningSmoke:
    def test_module_imports(self) -> None:
        module = import_function_app("recipes/concurrency_tuning")
        assert hasattr(module, "app")


# ---------------------------------------------------------------------------
# Retry and Idempotency
# ---------------------------------------------------------------------------


class TestRetryAndIdempotencySmoke:
    def test_module_imports(self) -> None:
        module = import_function_app("recipes/retry_and_idempotency")
        assert hasattr(module, "app")


# ---------------------------------------------------------------------------
# AI / MCP Server
# ---------------------------------------------------------------------------


class TestMcpServerSmoke:
    def test_module_imports(self) -> None:
        module = import_function_app("ai/mcp_server_example")
        assert hasattr(module, "app")
