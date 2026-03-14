"""Smoke tests for examples/ projects.

Each test dynamically imports the example's ``function_app.py`` module and
verifies that the Azure Functions app object and its registered functions
are accessible without crashing.
"""

from __future__ import annotations

import hashlib
import hmac
import importlib
from importlib.util import module_from_spec, spec_from_file_location
import json
import os
from pathlib import Path
import sys
from typing import Any
from unittest.mock import MagicMock

import azure.functions as func

EXAMPLES_DIR = Path(__file__).resolve().parents[1] / "examples"


def _load_example_module(example_path: str) -> Any:
    """Import an example's function_app.py and return the module.

    ``example_path`` uses forward-slash separators for nested examples,
    e.g. ``"http/hello_http_minimal"`` or ``"local_run_and_direct_invoke"``.
    """
    module_path = EXAMPLES_DIR / example_path / "function_app.py"
    module_name = f"cookbook_example_{example_path.replace('/', '_')}"

    # For blueprint examples, add the example directory to sys.path so
    # relative imports like ``from bp_users import bp`` resolve correctly.
    example_dir = str(EXAMPLES_DIR / example_path)
    added_to_path = False
    if example_dir not in sys.path:
        sys.path.insert(0, example_dir)
        added_to_path = True

    # Clean up any previously imported version of the module.
    if module_name in sys.modules:
        del sys.modules[module_name]

    spec = spec_from_file_location(module_name, module_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Failed to load example module from {module_path}")
    module = module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)

    if added_to_path:
        sys.path.remove(example_dir)

    return module


# ---------------------------------------------------------------------------
# HTTP — hello_http_minimal
# ---------------------------------------------------------------------------


class TestHelloHttpMinimal:
    """Smoke tests for examples/http/hello_http_minimal."""

    def test_module_loads(self) -> None:
        module = _load_example_module("http/hello_http_minimal")
        assert hasattr(module, "app")

    def test_hello_default_name(self) -> None:
        module = _load_example_module("http/hello_http_minimal")
        req = func.HttpRequest(
            method="GET",
            url="/api/hello",
            body=b"",
            headers={},
        )
        response = module.hello(req)
        assert response.status_code == 200
        assert "Hello, World!" in response.get_body().decode()

    def test_hello_with_name(self) -> None:
        module = _load_example_module("http/hello_http_minimal")
        req = func.HttpRequest(
            method="GET",
            url="/api/hello",
            body=b"",
            headers={},
            params={"name": "Ada"},
        )
        response = module.hello(req)
        assert response.status_code == 200
        assert "Hello, Ada!" in response.get_body().decode()


# ---------------------------------------------------------------------------
# HTTP — http_routing_query_body
# ---------------------------------------------------------------------------


class TestHttpRoutingQueryBody:
    """Smoke tests for examples/http/http_routing_query_body."""

    def test_module_loads(self) -> None:
        module = _load_example_module("http/http_routing_query_body")
        assert hasattr(module, "app")

    def test_list_users(self) -> None:
        module = _load_example_module("http/http_routing_query_body")
        req = func.HttpRequest(method="GET", url="/api/users", body=b"", headers={})
        response = module.list_users(req)
        assert response.status_code == 200
        data = json.loads(response.get_body())
        assert "users" in data
        assert isinstance(data["users"], list)

    def test_get_user_found(self) -> None:
        module = _load_example_module("http/http_routing_query_body")
        req = func.HttpRequest(
            method="GET",
            url="/api/users/1",
            body=b"",
            headers={},
            route_params={"user_id": "1"},
        )
        response = module.get_user(req)
        assert response.status_code == 200
        user = json.loads(response.get_body())
        assert user["id"] == "1"

    def test_get_user_not_found(self) -> None:
        module = _load_example_module("http/http_routing_query_body")
        req = func.HttpRequest(
            method="GET",
            url="/api/users/999",
            body=b"",
            headers={},
            route_params={"user_id": "999"},
        )
        response = module.get_user(req)
        assert response.status_code == 404

    def test_create_user(self) -> None:
        module = _load_example_module("http/http_routing_query_body")
        req = func.HttpRequest(
            method="POST",
            url="/api/users",
            body=json.dumps(
                {"id": "99", "name": "Test User", "email": "test@example.com"}
            ).encode(),
            headers={"Content-Type": "application/json"},
        )
        response = module.create_user(req)
        assert response.status_code == 201
        created = json.loads(response.get_body())
        assert created["name"] == "Test User"

    def test_create_user_missing_fields(self) -> None:
        module = _load_example_module("http/http_routing_query_body")
        req = func.HttpRequest(
            method="POST",
            url="/api/users",
            body=json.dumps({}).encode(),
            headers={"Content-Type": "application/json"},
        )
        response = module.create_user(req)
        assert response.status_code == 400

    def test_search_users(self) -> None:
        module = _load_example_module("http/http_routing_query_body")
        req = func.HttpRequest(
            method="GET",
            url="/api/search",
            body=b"",
            headers={},
            params={"q": "ada"},
        )
        response = module.search_users(req)
        assert response.status_code == 200
        data = json.loads(response.get_body())
        assert "results" in data

    def test_delete_user(self) -> None:
        module = _load_example_module("http/http_routing_query_body")
        req = func.HttpRequest(
            method="DELETE",
            url="/api/users/1",
            body=b"",
            headers={},
            route_params={"user_id": "1"},
        )
        response = module.delete_user(req)
        assert response.status_code == 204


# ---------------------------------------------------------------------------
# HTTP — http_auth_levels
# ---------------------------------------------------------------------------


class TestHttpAuthLevels:
    """Smoke tests for examples/http/http_auth_levels."""

    def test_module_loads(self) -> None:
        module = _load_example_module("http/http_auth_levels")
        assert hasattr(module, "app")

    def test_public_endpoint(self) -> None:
        module = _load_example_module("http/http_auth_levels")
        req = func.HttpRequest(method="GET", url="/api/public", body=b"", headers={})
        response = module.public_endpoint(req)
        assert response.status_code == 200
        assert "public" in response.get_body().decode().lower()

    def test_protected_endpoint(self) -> None:
        module = _load_example_module("http/http_auth_levels")
        req = func.HttpRequest(method="GET", url="/api/protected", body=b"", headers={})
        response = module.protected_endpoint(req)
        assert response.status_code == 200

    def test_admin_endpoint(self) -> None:
        module = _load_example_module("http/http_auth_levels")
        req = func.HttpRequest(method="GET", url="/api/admin-only", body=b"", headers={})
        response = module.admin_endpoint(req)
        assert response.status_code == 200


# ---------------------------------------------------------------------------
# HTTP — webhook_github
# ---------------------------------------------------------------------------


class TestWebhookGithub:
    """Smoke tests for examples/http/webhook_github."""

    def test_module_loads(self) -> None:
        module = _load_example_module("http/webhook_github")
        assert hasattr(module, "app")

    def test_missing_secret_returns_500(self) -> None:
        module = _load_example_module("http/webhook_github")
        # Ensure no secret is set.
        env_backup = os.environ.pop("GITHUB_WEBHOOK_SECRET", None)
        try:
            req = func.HttpRequest(
                method="POST",
                url="/api/github/webhook",
                body=b'{"action": "opened"}',
                headers={"X-GitHub-Event": "push"},
            )
            response = module.github_webhook(req)
            assert response.status_code == 500
        finally:
            if env_backup is not None:
                os.environ["GITHUB_WEBHOOK_SECRET"] = env_backup

    def test_invalid_signature_rejected(self) -> None:
        module = _load_example_module("http/webhook_github")
        os.environ["GITHUB_WEBHOOK_SECRET"] = "test-secret"
        try:
            req = func.HttpRequest(
                method="POST",
                url="/api/github/webhook",
                body=b'{"action": "opened"}',
                headers={
                    "X-Hub-Signature-256": "sha256=invalid",
                    "X-GitHub-Event": "push",
                },
            )
            response = module.github_webhook(req)
            assert response.status_code == 401
        finally:
            os.environ.pop("GITHUB_WEBHOOK_SECRET", None)

    def test_valid_push_event(self) -> None:
        module = _load_example_module("http/webhook_github")
        secret = "test-secret"
        os.environ["GITHUB_WEBHOOK_SECRET"] = secret
        try:
            body = json.dumps(
                {
                    "ref": "refs/heads/main",
                    "repository": {"full_name": "octo/repo"},
                    "commits": [{}],
                }
            ).encode()
            sig = "sha256=" + hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
            req = func.HttpRequest(
                method="POST",
                url="/api/github/webhook",
                body=body,
                headers={
                    "X-Hub-Signature-256": sig,
                    "X-GitHub-Event": "push",
                },
            )
            response = module.github_webhook(req)
            assert response.status_code == 200
            data = json.loads(response.get_body())
            assert data["event"] == "push"
        finally:
            os.environ.pop("GITHUB_WEBHOOK_SECRET", None)

    def test_handle_push_helper(self) -> None:
        module = _load_example_module("http/webhook_github")
        result = module._handle_push(
            {
                "ref": "refs/heads/main",
                "repository": {"full_name": "octo/repo"},
                "commits": [{}],
            }
        )
        assert result["event"] == "push"
        assert result["commits"] == 1

    def test_handle_pull_request_helper(self) -> None:
        module = _load_example_module("http/webhook_github")
        result = module._handle_pull_request(
            {
                "action": "opened",
                "pull_request": {"title": "Fix bug", "number": 42},
            }
        )
        assert result["event"] == "pull_request"
        assert result["number"] == 42

    def test_handle_issues_helper(self) -> None:
        module = _load_example_module("http/webhook_github")
        result = module._handle_issues(
            {
                "action": "closed",
                "issue": {"title": "Track issue", "number": 7},
            }
        )
        assert result["event"] == "issues"
        assert result["number"] == 7


# ---------------------------------------------------------------------------
# Timer — timer_cron_job
# ---------------------------------------------------------------------------


class TestTimerCronJob:
    """Smoke tests for examples/timer/timer_cron_job."""

    def test_module_loads(self) -> None:
        module = _load_example_module("timer/timer_cron_job")
        assert hasattr(module, "app")

    def test_perform_maintenance_helper(self) -> None:
        module = _load_example_module("timer/timer_cron_job")
        result = module._perform_maintenance()
        assert "complete" in result.lower()

    def test_scheduled_cleanup_normal(self) -> None:
        module = _load_example_module("timer/timer_cron_job")
        timer = MagicMock(spec=func.TimerRequest)
        timer.past_due = False
        module.scheduled_cleanup(timer)

    def test_scheduled_cleanup_past_due(self) -> None:
        module = _load_example_module("timer/timer_cron_job")
        timer = MagicMock(spec=func.TimerRequest)
        timer.past_due = True
        module.scheduled_cleanup(timer)


# ---------------------------------------------------------------------------
# Queue — queue_producer
# ---------------------------------------------------------------------------


class TestQueueProducer:
    """Smoke tests for examples/queue/queue_producer."""

    def test_module_loads(self) -> None:
        module = _load_example_module("queue/queue_producer")
        assert hasattr(module, "app")

    def test_validate_payload_valid(self) -> None:
        module = _load_example_module("queue/queue_producer")
        is_valid, error = module._validate_payload({"task_type": "email", "payload": {}})
        assert is_valid is True
        assert error == ""

    def test_validate_payload_missing_task_type(self) -> None:
        module = _load_example_module("queue/queue_producer")
        is_valid, error = module._validate_payload({})
        assert is_valid is False
        assert "task_type" in error


# ---------------------------------------------------------------------------
# Queue — queue_consumer
# ---------------------------------------------------------------------------


class TestQueueConsumer:
    """Smoke tests for examples/queue/queue_consumer."""

    def test_module_loads(self) -> None:
        module = _load_example_module("queue/queue_consumer")
        assert hasattr(module, "app")

    def test_process_task_helper(self) -> None:
        module = _load_example_module("queue/queue_consumer")
        result = module._process_task({"task_type": "email", "payload": {"to": "a@b.com"}})
        assert "email" in result

    def test_process_queue_message_valid(self) -> None:
        module = _load_example_module("queue/queue_consumer")
        msg = MagicMock(spec=func.QueueMessage)
        msg.id = "msg-001"
        msg.dequeue_count = 1
        msg.get_body.return_value = json.dumps(
            {"task_type": "email", "payload": {"to": "a@b.com"}}
        ).encode()
        module.process_queue_message(msg)

    def test_process_queue_message_invalid_json(self) -> None:
        module = _load_example_module("queue/queue_consumer")
        msg = MagicMock(spec=func.QueueMessage)
        msg.id = "msg-002"
        msg.dequeue_count = 1
        msg.get_body.return_value = b"not json"
        module.process_queue_message(msg)


# ---------------------------------------------------------------------------
# Blob — blob_upload_processor
# ---------------------------------------------------------------------------


class TestBlobUploadProcessor:
    """Smoke tests for examples/blob/blob_upload_processor."""

    def test_module_loads(self) -> None:
        module = _load_example_module("blob/blob_upload_processor")
        assert hasattr(module, "app")

    def test_process_blob_helper(self) -> None:
        module = _load_example_module("blob/blob_upload_processor")
        result = module._process_blob(
            blob_name="test.txt",
            blob_size=100,
            metadata={"key": "val"},
            data=b"hello world",
        )
        assert "test.txt" in result
        assert "100" in result


# ---------------------------------------------------------------------------
# Blob — blob_eventgrid_trigger
# ---------------------------------------------------------------------------


class TestBlobEventgridTrigger:
    """Smoke tests for examples/blob/blob_eventgrid_trigger."""

    def test_module_loads(self) -> None:
        module = _load_example_module("blob/blob_eventgrid_trigger")
        assert hasattr(module, "app")


# ---------------------------------------------------------------------------
# Service Bus — servicebus_worker
# ---------------------------------------------------------------------------


class TestServicebusWorker:
    """Smoke tests for examples/servicebus/servicebus_worker."""

    def test_module_loads(self) -> None:
        module = _load_example_module("servicebus/servicebus_worker")
        assert hasattr(module, "app")

    def test_process_helper(self) -> None:
        module = _load_example_module("servicebus/servicebus_worker")
        result = module._process_service_bus_message({"task": "send", "priority": "high"})
        assert "send" in result
        assert "high" in result

    def test_process_message_valid(self) -> None:
        module = _load_example_module("servicebus/servicebus_worker")
        msg = MagicMock(spec=func.ServiceBusMessage)
        msg.correlation_id = "corr-1"
        msg.delivery_count = 1
        msg.get_body.return_value = json.dumps({"task": "send", "priority": "normal"}).encode()
        module.process_service_bus_message(msg)

    def test_process_message_invalid_json(self) -> None:
        module = _load_example_module("servicebus/servicebus_worker")
        msg = MagicMock(spec=func.ServiceBusMessage)
        msg.correlation_id = "corr-2"
        msg.delivery_count = 1
        msg.get_body.return_value = b"not json"
        module.process_service_bus_message(msg)


# ---------------------------------------------------------------------------
# Event Hub — eventhub_consumer
# ---------------------------------------------------------------------------


class TestEventhubConsumer:
    """Smoke tests for examples/eventhub/eventhub_consumer."""

    def test_module_loads(self) -> None:
        module = _load_example_module("eventhub/eventhub_consumer")
        assert hasattr(module, "app")

    def test_process_telemetry_helper(self) -> None:
        module = _load_example_module("eventhub/eventhub_consumer")
        result = module._process_telemetry({"metric": "cpu_usage", "value": 42.5})
        assert "cpu_usage" in result
        assert "42.5" in result


# ---------------------------------------------------------------------------
# Cosmos DB — change_feed_processor
# ---------------------------------------------------------------------------


class TestChangeFeedProcessor:
    """Smoke tests for examples/cosmosdb/change_feed_processor."""

    def test_module_loads(self) -> None:
        module = _load_example_module("cosmosdb/change_feed_processor")
        assert hasattr(module, "app")

    def test_process_change_helper(self) -> None:
        module = _load_example_module("cosmosdb/change_feed_processor")
        result = module._process_change({"id": "doc-1", "category": "orders"})
        assert "doc-1" in result
        assert "orders" in result


# ---------------------------------------------------------------------------
# Recipes — blueprint_modular_app
# ---------------------------------------------------------------------------


class TestBlueprintModularApp:
    """Smoke tests for examples/recipes/blueprint_modular_app."""

    def test_module_loads(self) -> None:
        module = _load_example_module("recipes/blueprint_modular_app")
        assert hasattr(module, "app")

    def test_health_endpoint(self) -> None:
        # Import bp_health directly.
        example_dir = str(EXAMPLES_DIR / "recipes" / "blueprint_modular_app")
        if example_dir not in sys.path:
            sys.path.insert(0, example_dir)
        try:
            bp_health = importlib.import_module("bp_health")
            req = func.HttpRequest(method="GET", url="/api/health", body=b"", headers={})
            response = bp_health.get_health(req)
            assert response.status_code == 200
            data = json.loads(response.get_body())
            assert data["status"] == "healthy"
        finally:
            if example_dir in sys.path:
                sys.path.remove(example_dir)
            sys.modules.pop("bp_health", None)

    def test_users_list(self) -> None:
        example_dir = str(EXAMPLES_DIR / "recipes" / "blueprint_modular_app")
        if example_dir not in sys.path:
            sys.path.insert(0, example_dir)
        try:
            bp_users = importlib.import_module("bp_users")
            req = func.HttpRequest(method="GET", url="/api/users", body=b"", headers={})
            response = bp_users.list_users(req)
            assert response.status_code == 200
        finally:
            if example_dir in sys.path:
                sys.path.remove(example_dir)
            sys.modules.pop("bp_users", None)


# ---------------------------------------------------------------------------
# Recipes — retry_and_idempotency
# ---------------------------------------------------------------------------


class TestRetryAndIdempotency:
    """Smoke tests for examples/recipes/retry_and_idempotency."""

    def test_module_loads(self) -> None:
        module = _load_example_module("recipes/retry_and_idempotency")
        assert hasattr(module, "app")


# ---------------------------------------------------------------------------
# Recipes — output_binding_vs_sdk
# ---------------------------------------------------------------------------


class TestOutputBindingVsSdk:
    """Smoke tests for examples/recipes/output_binding_vs_sdk."""

    def test_module_loads(self) -> None:
        module = _load_example_module("recipes/output_binding_vs_sdk")
        assert hasattr(module, "app")

    def test_build_payload_helper(self) -> None:
        module = _load_example_module("recipes/output_binding_vs_sdk")
        req = func.HttpRequest(
            method="POST",
            url="/api/enqueue/binding",
            body=json.dumps({"task": "process-report"}).encode(),
            headers={"Content-Type": "application/json"},
        )
        payload = module._build_payload(req)
        assert payload["task"] == "process-report"
        assert payload["source"] == "recipe"


# ---------------------------------------------------------------------------
# Recipes — managed_identity_storage
# ---------------------------------------------------------------------------


class TestManagedIdentityStorage:
    """Smoke tests for examples/recipes/managed_identity_storage."""

    def test_module_loads(self) -> None:
        module = _load_example_module("recipes/managed_identity_storage")
        assert hasattr(module, "app")


# ---------------------------------------------------------------------------
# Recipes — managed_identity_servicebus
# ---------------------------------------------------------------------------


class TestManagedIdentityServicebus:
    """Smoke tests for examples/recipes/managed_identity_servicebus."""

    def test_module_loads(self) -> None:
        module = _load_example_module("recipes/managed_identity_servicebus")
        assert hasattr(module, "app")


# ---------------------------------------------------------------------------
# Recipes — host_json_tuning
# ---------------------------------------------------------------------------


class TestHostJsonTuning:
    """Smoke tests for examples/recipes/host_json_tuning."""

    def test_module_loads(self) -> None:
        module = _load_example_module("recipes/host_json_tuning")
        assert hasattr(module, "app")


# ---------------------------------------------------------------------------
# Recipes — concurrency_tuning
# ---------------------------------------------------------------------------


class TestConcurrencyTuning:
    """Smoke tests for examples/recipes/concurrency_tuning."""

    def test_module_loads(self) -> None:
        module = _load_example_module("recipes/concurrency_tuning")
        assert hasattr(module, "app")


# ---------------------------------------------------------------------------
# Durable — durable_hello_sequence
# ---------------------------------------------------------------------------


class TestDurableHelloSequence:
    """Smoke tests for examples/durable/durable_hello_sequence."""

    def test_module_loads(self) -> None:
        module = _load_example_module("durable/durable_hello_sequence")
        assert hasattr(module, "app")

    def test_say_hello_activity(self) -> None:
        module = _load_example_module("durable/durable_hello_sequence")
        result = module.say_hello("Tokyo")
        assert result == "Hello Tokyo!"


# ---------------------------------------------------------------------------
# Durable — durable_fan_out_fan_in
# ---------------------------------------------------------------------------


class TestDurableFanOutFanIn:
    """Smoke tests for examples/durable/durable_fan_out_fan_in."""

    def test_module_loads(self) -> None:
        module = _load_example_module("durable/durable_fan_out_fan_in")
        assert hasattr(module, "app")

    def test_process_item_activity(self) -> None:
        module = _load_example_module("durable/durable_fan_out_fan_in")
        result = module.process_item("item-1")
        assert result == "Processed item-1"


# ---------------------------------------------------------------------------
# Durable — durable_human_interaction
# ---------------------------------------------------------------------------


class TestDurableHumanInteraction:
    """Smoke tests for examples/durable/durable_human_interaction."""

    def test_module_loads(self) -> None:
        module = _load_example_module("durable/durable_human_interaction")
        assert hasattr(module, "app")


# ---------------------------------------------------------------------------
# Durable — durable_entity_counter
# ---------------------------------------------------------------------------


class TestDurableEntityCounter:
    """Smoke tests for examples/durable/durable_entity_counter."""

    def test_module_loads(self) -> None:
        module = _load_example_module("durable/durable_entity_counter")
        assert hasattr(module, "app")


# ---------------------------------------------------------------------------
# Durable — durable_retry_pattern
# ---------------------------------------------------------------------------


class TestDurableRetryPattern:
    """Smoke tests for examples/durable/durable_retry_pattern."""

    def test_module_loads(self) -> None:
        module = _load_example_module("durable/durable_retry_pattern")
        assert hasattr(module, "app")


# ---------------------------------------------------------------------------
# Durable — durable_determinism_gotchas
# ---------------------------------------------------------------------------


class TestDurableDeterminismGotchas:
    """Smoke tests for examples/durable/durable_determinism_gotchas."""

    def test_module_loads(self) -> None:
        module = _load_example_module("durable/durable_determinism_gotchas")
        assert hasattr(module, "app")

    def test_fetch_data_activity(self) -> None:
        module = _load_example_module("durable/durable_determinism_gotchas")
        result = module.fetch_data_activity("resource-1")
        assert "resource-1" in result


# ---------------------------------------------------------------------------
# Durable — durable_unit_testing
# ---------------------------------------------------------------------------


class TestDurableUnitTesting:
    """Smoke tests for examples/durable/durable_unit_testing."""

    def test_module_loads(self) -> None:
        module = _load_example_module("durable/durable_unit_testing")
        assert hasattr(module, "app")

    def test_say_hello_activity(self) -> None:
        module = _load_example_module("durable/durable_unit_testing")
        result = module.say_hello("Seoul")
        assert result == "Hello Seoul!"


# ---------------------------------------------------------------------------
# AI — mcp_server_example
# ---------------------------------------------------------------------------


class TestMcpServerExample:
    """Smoke tests for examples/ai/mcp_server_example."""

    def test_module_loads(self) -> None:
        module = _load_example_module("ai/mcp_server_example")
        assert hasattr(module, "app")

    def test_handle_get_weather(self) -> None:
        module = _load_example_module("ai/mcp_server_example")
        result = module._handle_get_weather({"location": "San Francisco, CA"})
        assert "San Francisco" in result

    def test_handle_calculate(self) -> None:
        module = _load_example_module("ai/mcp_server_example")
        result = module._handle_calculate({"expression": "2 + 3"})
        assert result == "5"

    def test_handle_calculate_invalid(self) -> None:
        module = _load_example_module("ai/mcp_server_example")
        result = module._handle_calculate({"expression": "import os"})
        assert "Error" in result

    def test_mcp_initialize(self) -> None:
        module = _load_example_module("ai/mcp_server_example")
        req = func.HttpRequest(
            method="POST",
            url="/api/mcp",
            body=json.dumps(
                {
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "initialize",
                    "params": {},
                }
            ).encode(),
            headers={"Content-Type": "application/json"},
        )
        response = module.mcp_endpoint(req)
        assert response.status_code == 200
        data = json.loads(response.get_body())
        assert data["result"]["capabilities"]["tools"] is not None

    def test_mcp_tools_list(self) -> None:
        module = _load_example_module("ai/mcp_server_example")
        req = func.HttpRequest(
            method="POST",
            url="/api/mcp",
            body=json.dumps(
                {
                    "jsonrpc": "2.0",
                    "id": 2,
                    "method": "tools/list",
                    "params": {},
                }
            ).encode(),
            headers={"Content-Type": "application/json"},
        )
        response = module.mcp_endpoint(req)
        assert response.status_code == 200
        data = json.loads(response.get_body())
        tools = data["result"]["tools"]
        tool_names = [t["name"] for t in tools]
        assert "get_weather" in tool_names
        assert "calculate" in tool_names

    def test_mcp_tools_call(self) -> None:
        module = _load_example_module("ai/mcp_server_example")
        req = func.HttpRequest(
            method="POST",
            url="/api/mcp",
            body=json.dumps(
                {
                    "jsonrpc": "2.0",
                    "id": 3,
                    "method": "tools/call",
                    "params": {
                        "name": "calculate",
                        "arguments": {"expression": "(2 + 3) * 4"},
                    },
                }
            ).encode(),
            headers={"Content-Type": "application/json"},
        )
        response = module.mcp_endpoint(req)
        assert response.status_code == 200
        data = json.loads(response.get_body())
        assert data["result"]["content"][0]["text"] == "20"

    def test_mcp_unknown_method(self) -> None:
        module = _load_example_module("ai/mcp_server_example")
        req = func.HttpRequest(
            method="POST",
            url="/api/mcp",
            body=json.dumps(
                {
                    "jsonrpc": "2.0",
                    "id": 4,
                    "method": "unknown/method",
                    "params": {},
                }
            ).encode(),
            headers={"Content-Type": "application/json"},
        )
        response = module.mcp_endpoint(req)
        assert response.status_code == 404

    def test_mcp_parse_error(self) -> None:
        module = _load_example_module("ai/mcp_server_example")
        req = func.HttpRequest(
            method="POST",
            url="/api/mcp",
            body=b"not json",
            headers={"Content-Type": "application/json"},
        )
        response = module.mcp_endpoint(req)
        assert response.status_code == 400


# ---------------------------------------------------------------------------
# Local — local_run_and_direct_invoke
# ---------------------------------------------------------------------------


class TestLocalRunAndDirectInvoke:
    """Smoke tests for examples/local_run_and_direct_invoke."""

    def test_module_loads(self) -> None:
        module = _load_example_module("local_run_and_direct_invoke")
        assert hasattr(module, "app")

    def test_greet_with_query_param(self) -> None:
        module = _load_example_module("local_run_and_direct_invoke")
        req = func.HttpRequest(
            method="GET",
            url="/api/greet",
            body=b"",
            headers={},
            params={"name": "Alice"},
        )
        response = module.greet(req)
        assert response.status_code == 200
        data = json.loads(response.get_body())
        assert data["greeting"] == "Hello, Alice!"

    def test_greet_with_json_body(self) -> None:
        module = _load_example_module("local_run_and_direct_invoke")
        req = func.HttpRequest(
            method="POST",
            url="/api/greet",
            body=json.dumps({"name": "Bob"}).encode(),
            headers={"Content-Type": "application/json"},
        )
        response = module.greet(req)
        assert response.status_code == 200
        data = json.loads(response.get_body())
        assert data["greeting"] == "Hello, Bob!"

    def test_greet_missing_name(self) -> None:
        module = _load_example_module("local_run_and_direct_invoke")
        req = func.HttpRequest(
            method="GET",
            url="/api/greet",
            body=b"",
            headers={},
        )
        response = module.greet(req)
        assert response.status_code == 400
