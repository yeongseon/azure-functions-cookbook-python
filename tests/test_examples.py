"""Smoke tests for examples/ projects.

Each test dynamically imports the example's ``function_app.py`` module and
verifies that the Azure Functions app object and its registered functions
are accessible without crashing.  Service-layer helpers are tested via
direct imports from ``app.services.*``.
"""

from __future__ import annotations

import hashlib
import hmac
import importlib
import json
import os
from pathlib import Path
import sys
from typing import Any

import azure.functions as func

EXAMPLES_DIR = Path(__file__).resolve().parents[1] / "examples"


def _clean_app_modules() -> None:
    """Remove all ``app`` and ``app.*`` modules from ``sys.modules``.

    Blueprint examples use a local ``app`` package.  When loading multiple
    examples in the same process the cached ``app`` from one example will
    conflict with the next.  Cleaning these entries forces a fresh import.
    """
    for mod_name in list(sys.modules):
        if mod_name == "app" or mod_name.startswith("app."):
            del sys.modules[mod_name]


def _load_example_module(example_path: str) -> Any:
    """Import an example's function_app.py and return the module.

    ``example_path`` uses forward-slash separators for nested examples,
    e.g. ``"http/hello_http_minimal"`` or ``"local_run_and_direct_invoke"``.
    """
    module_path = EXAMPLES_DIR / example_path / "function_app.py"
    module_name = f"cookbook_example_{example_path.replace('/', '_')}"

    example_dir = str(EXAMPLES_DIR / example_path)

    # Clean previous app.* modules to avoid import collisions.
    _clean_app_modules()

    if module_name in sys.modules:
        del sys.modules[module_name]

    added_to_path = False
    if example_dir not in sys.path:
        sys.path.insert(0, example_dir)
        added_to_path = True

    from importlib.util import module_from_spec, spec_from_file_location

    try:
        spec = spec_from_file_location(module_name, module_path)
        if spec is None or spec.loader is None:
            raise RuntimeError(f"Failed to load example module from {module_path}")
        module = module_from_spec(spec)
        sys.modules[module_name] = module
        spec.loader.exec_module(module)
    finally:
        if added_to_path and example_dir in sys.path:
            sys.path.remove(example_dir)

    return module


def _import_service(example_path: str, service_module: str) -> Any:
    """Import a service module from an example directory.

    Must be called *after* ``_load_example_module`` for the same example so
    that any ``app.core`` side-effects (e.g. ``configure_logging``) have
    already been executed.

    Args:
        example_path: Relative example path, e.g. ``"http/hello_http_minimal"``.
        service_module: Fully-qualified module name,
            e.g. ``"app.services.hello_service"``.
    """
    example_dir = str(EXAMPLES_DIR / example_path)

    # Clean cached ``app.*`` to ensure we load from the correct example.
    _clean_app_modules()

    added_to_path = False
    if example_dir not in sys.path:
        sys.path.insert(0, example_dir)
        added_to_path = True

    try:
        return importlib.import_module(service_module)
    finally:
        if added_to_path and example_dir in sys.path:
            sys.path.remove(example_dir)


def _import_function_module(example_path: str, function_module: str) -> Any:
    """Import a function Blueprint module from an example directory.

    Used when tests need to call the actual Azure Function handler
    (e.g. ``github_webhook``, ``mcp_endpoint``).
    """
    example_dir = str(EXAMPLES_DIR / example_path)

    # Clean cached ``app.*`` to ensure we load from the correct example.
    _clean_app_modules()

    added_to_path = False
    if example_dir not in sys.path:
        sys.path.insert(0, example_dir)
        added_to_path = True

    try:
        return importlib.import_module(function_module)
    finally:
        if added_to_path and example_dir in sys.path:
            sys.path.remove(example_dir)


# ---------------------------------------------------------------------------
# HTTP — hello_http_minimal
# ---------------------------------------------------------------------------


class TestHelloHttpMinimal:
    """Smoke tests for examples/http/hello_http_minimal."""

    def test_module_loads(self) -> None:
        module = _load_example_module("http/hello_http_minimal")
        assert hasattr(module, "app")

    def test_build_greeting_default(self) -> None:
        _load_example_module("http/hello_http_minimal")
        svc = _import_service("http/hello_http_minimal", "app.services.hello_service")
        assert svc.build_greeting("World") == "Hello, World!"

    def test_build_greeting_with_name(self) -> None:
        _load_example_module("http/hello_http_minimal")
        svc = _import_service("http/hello_http_minimal", "app.services.hello_service")
        assert svc.build_greeting("Ada") == "Hello, Ada!"


# ---------------------------------------------------------------------------
# HTTP — http_routing_query_body
# ---------------------------------------------------------------------------


class TestHttpRoutingQueryBody:
    """Smoke tests for examples/http/http_routing_query_body."""

    def test_module_loads(self) -> None:
        module = _load_example_module("http/http_routing_query_body")
        assert hasattr(module, "app")

    def test_list_all_users(self) -> None:
        _load_example_module("http/http_routing_query_body")
        svc = _import_service("http/http_routing_query_body", "app.services.user_service")
        result = svc.list_all_users()
        assert "users" in result
        assert isinstance(result["users"], list)

    def test_get_user_found(self) -> None:
        _load_example_module("http/http_routing_query_body")
        svc = _import_service("http/http_routing_query_body", "app.services.user_service")
        user = svc.get_user_by_id("1")
        assert user is not None
        assert user["id"] == "1"

    def test_get_user_not_found(self) -> None:
        _load_example_module("http/http_routing_query_body")
        svc = _import_service("http/http_routing_query_body", "app.services.user_service")
        user = svc.get_user_by_id("999")
        assert user is None

    def test_create_user(self) -> None:
        _load_example_module("http/http_routing_query_body")
        svc = _import_service("http/http_routing_query_body", "app.services.user_service")
        result, status = svc.create_user(
            {"id": "99", "name": "Test User", "email": "test@example.com"}
        )
        assert status == 201
        assert result["name"] == "Test User"

    def test_create_user_missing_fields(self) -> None:
        _load_example_module("http/http_routing_query_body")
        svc = _import_service("http/http_routing_query_body", "app.services.user_service")
        result, status = svc.create_user({})
        assert status == 400

    def test_search_users(self) -> None:
        _load_example_module("http/http_routing_query_body")
        svc = _import_service("http/http_routing_query_body", "app.services.user_service")
        result = svc.search_users("ada", 10)
        assert "results" in result

    def test_delete_user(self) -> None:
        _load_example_module("http/http_routing_query_body")
        svc = _import_service("http/http_routing_query_body", "app.services.user_service")
        _result, status = svc.delete_user("1")
        assert status == 204


# ---------------------------------------------------------------------------
# HTTP — http_auth_levels
# ---------------------------------------------------------------------------


class TestHttpAuthLevels:
    """Smoke tests for examples/http/http_auth_levels."""

    def test_module_loads(self) -> None:
        module = _load_example_module("http/http_auth_levels")
        assert hasattr(module, "app")

    def test_public_message(self) -> None:
        _load_example_module("http/http_auth_levels")
        svc = _import_service("http/http_auth_levels", "app.services.auth_service")
        msg = svc.get_public_message()
        assert "public" in msg.lower()

    def test_protected_message(self) -> None:
        _load_example_module("http/http_auth_levels")
        svc = _import_service("http/http_auth_levels", "app.services.auth_service")
        msg = svc.get_protected_message()
        assert isinstance(msg, str)

    def test_admin_message(self) -> None:
        _load_example_module("http/http_auth_levels")
        svc = _import_service("http/http_auth_levels", "app.services.auth_service")
        msg = svc.get_admin_message()
        assert isinstance(msg, str)


# ---------------------------------------------------------------------------
# HTTP — webhook_github
# ---------------------------------------------------------------------------


class TestWebhookGithub:
    """Smoke tests for examples/http/webhook_github."""

    def test_module_loads(self) -> None:
        module = _load_example_module("http/webhook_github")
        assert hasattr(module, "app")

    def test_missing_secret_returns_500(self) -> None:
        _load_example_module("http/webhook_github")
        fn = _import_function_module("http/webhook_github", "app.functions.webhook")
        env_backup = os.environ.pop("GITHUB_WEBHOOK_SECRET", None)
        try:
            req = func.HttpRequest(
                method="POST",
                url="/api/github/webhook",
                body=b'{"action": "opened"}',
                headers={"X-GitHub-Event": "push"},
            )
            response = fn.github_webhook(req)
            assert response.status_code == 500
        finally:
            if env_backup is not None:
                os.environ["GITHUB_WEBHOOK_SECRET"] = env_backup

    def test_invalid_signature_rejected(self) -> None:
        _load_example_module("http/webhook_github")
        fn = _import_function_module("http/webhook_github", "app.functions.webhook")
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
            response = fn.github_webhook(req)
            assert response.status_code == 401
        finally:
            os.environ.pop("GITHUB_WEBHOOK_SECRET", None)

    def test_valid_push_event(self) -> None:
        _load_example_module("http/webhook_github")
        fn = _import_function_module("http/webhook_github", "app.functions.webhook")
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
            response = fn.github_webhook(req)
            assert response.status_code == 200
            data = json.loads(response.get_body())
            assert data["event"] == "push"
        finally:
            os.environ.pop("GITHUB_WEBHOOK_SECRET", None)

    def test_handle_push_helper(self) -> None:
        _load_example_module("http/webhook_github")
        svc = _import_service("http/webhook_github", "app.services.webhook_service")
        result = svc._handle_push(
            {
                "ref": "refs/heads/main",
                "repository": {"full_name": "octo/repo"},
                "commits": [{}],
            }
        )
        assert result["event"] == "push"
        assert result["commits"] == 1

    def test_handle_pull_request_helper(self) -> None:
        _load_example_module("http/webhook_github")
        svc = _import_service("http/webhook_github", "app.services.webhook_service")
        result = svc._handle_pull_request(
            {
                "action": "opened",
                "pull_request": {"title": "Fix bug", "number": 42},
            }
        )
        assert result["event"] == "pull_request"
        assert result["number"] == 42

    def test_handle_issues_helper(self) -> None:
        _load_example_module("http/webhook_github")
        svc = _import_service("http/webhook_github", "app.services.webhook_service")
        result = svc._handle_issues(
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
        _load_example_module("timer/timer_cron_job")
        svc = _import_service("timer/timer_cron_job", "app.services.maintenance_service")
        result = svc.perform_maintenance()
        assert "complete" in result.lower()


# ---------------------------------------------------------------------------
# Queue — queue_producer
# ---------------------------------------------------------------------------


class TestQueueProducer:
    """Smoke tests for examples/queue/queue_producer."""

    def test_module_loads(self) -> None:
        module = _load_example_module("queue/queue_producer")
        assert hasattr(module, "app")

    def test_validate_payload_valid(self) -> None:
        _load_example_module("queue/queue_producer")
        svc = _import_service("queue/queue_producer", "app.services.enqueue_service")
        is_valid, error = svc.validate_payload({"task_type": "email", "payload": {}})
        assert is_valid is True
        assert error == ""

    def test_validate_payload_missing_task_type(self) -> None:
        _load_example_module("queue/queue_producer")
        svc = _import_service("queue/queue_producer", "app.services.enqueue_service")
        is_valid, error = svc.validate_payload({})
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
        _load_example_module("queue/queue_consumer")
        svc = _import_service("queue/queue_consumer", "app.services.task_service")
        result = svc.process_task({"task_type": "email", "payload": {"to": "a@b.com"}})
        assert "email" in result


# ---------------------------------------------------------------------------
# Blob — blob_upload_processor
# ---------------------------------------------------------------------------


class TestBlobUploadProcessor:
    """Smoke tests for examples/blob/blob_upload_processor."""

    def test_module_loads(self) -> None:
        module = _load_example_module("blob/blob_upload_processor")
        assert hasattr(module, "app")

    def test_process_blob_helper(self) -> None:
        _load_example_module("blob/blob_upload_processor")
        svc = _import_service("blob/blob_upload_processor", "app.services.blob_service")
        result = svc.process_blob(
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

    def test_process_message_helper(self) -> None:
        _load_example_module("servicebus/servicebus_worker")
        svc = _import_service("servicebus/servicebus_worker", "app.services.servicebus_service")
        result = svc.process_message({"task": "send", "priority": "high"})
        assert "send" in result
        assert "high" in result


# ---------------------------------------------------------------------------
# Event Hub — eventhub_consumer
# ---------------------------------------------------------------------------


class TestEventhubConsumer:
    """Smoke tests for examples/eventhub/eventhub_consumer."""

    def test_module_loads(self) -> None:
        module = _load_example_module("eventhub/eventhub_consumer")
        assert hasattr(module, "app")

    def test_process_telemetry_helper(self) -> None:
        _load_example_module("eventhub/eventhub_consumer")
        svc = _import_service("eventhub/eventhub_consumer", "app.services.telemetry_service")
        result = svc.process_telemetry({"metric": "cpu_usage", "value": 42.5})
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
        _load_example_module("cosmosdb/change_feed_processor")
        svc = _import_service("cosmosdb/change_feed_processor", "app.services.change_service")
        result = svc.process_change({"id": "doc-1", "category": "orders"})
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

    def test_health_service(self) -> None:
        _load_example_module("recipes/blueprint_modular_app")
        svc = _import_service("recipes/blueprint_modular_app", "app.services.health_service")
        payload = svc.get_health_payload()
        assert payload["status"] == "healthy"

    def test_user_service_list(self) -> None:
        _load_example_module("recipes/blueprint_modular_app")
        svc = _import_service("recipes/blueprint_modular_app", "app.services.user_service")
        users = svc.list_users()
        assert isinstance(users, list)


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
        _load_example_module("recipes/output_binding_vs_sdk")
        svc = _import_service("recipes/output_binding_vs_sdk", "app.services.payload_service")
        req = func.HttpRequest(
            method="POST",
            url="/api/enqueue/binding",
            body=json.dumps({"task": "process-report"}).encode(),
            headers={"Content-Type": "application/json"},
        )
        payload = svc.build_payload(req)
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

    def test_greet_activity(self) -> None:
        _load_example_module("durable/durable_hello_sequence")
        svc = _import_service("durable/durable_hello_sequence", "app.services.greeting_service")
        result = svc.greet("Tokyo")
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
        _load_example_module("durable/durable_fan_out_fan_in")
        svc = _import_service("durable/durable_fan_out_fan_in", "app.services.processing_service")
        result = svc.process_item("item-1")
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
        _load_example_module("durable/durable_determinism_gotchas")
        svc = _import_service("durable/durable_determinism_gotchas", "app.services.data_service")
        result = svc.fetch_data("resource-1")
        assert "resource-1" in result


# ---------------------------------------------------------------------------
# Durable — durable_unit_testing
# ---------------------------------------------------------------------------


class TestDurableUnitTesting:
    """Smoke tests for examples/durable/durable_unit_testing."""

    def test_module_loads(self) -> None:
        module = _load_example_module("durable/durable_unit_testing")
        assert hasattr(module, "app")

    def test_greet_activity(self) -> None:
        _load_example_module("durable/durable_unit_testing")
        svc = _import_service("durable/durable_unit_testing", "app.services.greeting_service")
        result = svc.greet("Seoul")
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
        _load_example_module("ai/mcp_server_example")
        svc = _import_service("ai/mcp_server_example", "app.services.mcp_service")
        result = svc._handle_get_weather({"location": "San Francisco, CA"})
        assert "San Francisco" in result

    def test_handle_calculate(self) -> None:
        _load_example_module("ai/mcp_server_example")
        svc = _import_service("ai/mcp_server_example", "app.services.mcp_service")
        result = svc._handle_calculate({"expression": "2 + 3"})
        assert result == "5"

    def test_handle_calculate_invalid(self) -> None:
        _load_example_module("ai/mcp_server_example")
        svc = _import_service("ai/mcp_server_example", "app.services.mcp_service")
        result = svc._handle_calculate({"expression": "import os"})
        assert "Error" in result

    def test_mcp_initialize(self) -> None:
        _load_example_module("ai/mcp_server_example")
        fn = _import_function_module("ai/mcp_server_example", "app.functions.mcp")
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
        response = fn.mcp(req)
        assert response.status_code == 200
        data = json.loads(response.get_body())
        assert data["result"]["capabilities"]["tools"] is not None

    def test_mcp_tools_list(self) -> None:
        _load_example_module("ai/mcp_server_example")
        fn = _import_function_module("ai/mcp_server_example", "app.functions.mcp")
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
        response = fn.mcp(req)
        assert response.status_code == 200
        data = json.loads(response.get_body())
        tools = data["result"]["tools"]
        tool_names = [t["name"] for t in tools]
        assert "get_weather" in tool_names
        assert "calculate" in tool_names

    def test_mcp_tools_call(self) -> None:
        _load_example_module("ai/mcp_server_example")
        fn = _import_function_module("ai/mcp_server_example", "app.functions.mcp")
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
        response = fn.mcp(req)
        assert response.status_code == 200
        data = json.loads(response.get_body())
        assert data["result"]["content"][0]["text"] == "20"

    def test_mcp_unknown_method(self) -> None:
        _load_example_module("ai/mcp_server_example")
        fn = _import_function_module("ai/mcp_server_example", "app.functions.mcp")
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
        response = fn.mcp(req)
        assert response.status_code == 404

    def test_mcp_parse_error(self) -> None:
        _load_example_module("ai/mcp_server_example")
        fn = _import_function_module("ai/mcp_server_example", "app.functions.mcp")
        req = func.HttpRequest(
            method="POST",
            url="/api/mcp",
            body=b"not json",
            headers={"Content-Type": "application/json"},
        )
        response = fn.mcp(req)
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
        _load_example_module("local_run_and_direct_invoke")
        fn = _import_function_module("local_run_and_direct_invoke", "app.functions.greet")
        req = func.HttpRequest(
            method="GET",
            url="/api/greet",
            body=b"",
            headers={},
            params={"name": "Alice"},
        )
        response = fn.greet(req)
        assert response.status_code == 200
        data = json.loads(response.get_body())
        assert data["greeting"] == "Hello, Alice!"

    def test_greet_with_json_body(self) -> None:
        _load_example_module("local_run_and_direct_invoke")
        fn = _import_function_module("local_run_and_direct_invoke", "app.functions.greet")
        req = func.HttpRequest(
            method="POST",
            url="/api/greet",
            body=json.dumps({"name": "Bob"}).encode(),
            headers={"Content-Type": "application/json"},
        )
        response = fn.greet(req)
        assert response.status_code == 200
        data = json.loads(response.get_body())
        assert data["greeting"] == "Hello, Bob!"

    def test_greet_missing_name(self) -> None:
        _load_example_module("local_run_and_direct_invoke")
        fn = _import_function_module("local_run_and_direct_invoke", "app.functions.greet")
        req = func.HttpRequest(
            method="GET",
            url="/api/greet",
            body=b"",
            headers={},
        )
        response = fn.greet(req)
        assert response.status_code == 400
