"""Smoke tests for examples/ projects.

Each test dynamically imports the example's ``function_app.py`` module and
verifies that the Azure Functions app object and its registered functions
are accessible without crashing.  Service-layer helpers are tested via
direct imports from ``app.services.*``.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import os

import azure.functions as func

from tests._isolation import (
    EXAMPLES_DIR,
)
from tests._isolation import (
    import_function_module as _import_function_module,
)
from tests._isolation import (
    import_service as _import_service,
)
from tests._isolation import (
    load_example_module as _load_example_module,
)


class TestHelloHttpMinimal:
    """Smoke tests for examples/apis-and-ingress/hello_http_minimal."""

    def test_build_greeting_default(self) -> None:
        _load_example_module("apis-and-ingress/hello_http_minimal")
        svc = _import_service("apis-and-ingress/hello_http_minimal", "app.services.hello_service")
        assert svc.build_greeting("World") == "Hello, World!"

    def test_build_greeting_with_name(self) -> None:
        _load_example_module("apis-and-ingress/hello_http_minimal")
        svc = _import_service("apis-and-ingress/hello_http_minimal", "app.services.hello_service")
        assert svc.build_greeting("Ada") == "Hello, Ada!"


class TestHttpRoutingQueryBody:
    """Smoke tests for examples/apis-and-ingress/http_routing_query_body."""

    def test_list_all_users(self) -> None:
        _load_example_module("apis-and-ingress/http_routing_query_body")
        svc = _import_service(
            "apis-and-ingress/http_routing_query_body", "app.services.user_service"
        )
        result = svc.list_all_users()
        assert "users" in result
        assert isinstance(result["users"], list)

    def test_get_user_found(self) -> None:
        _load_example_module("apis-and-ingress/http_routing_query_body")
        svc = _import_service(
            "apis-and-ingress/http_routing_query_body", "app.services.user_service"
        )
        user = svc.get_user_by_id("1")
        assert user is not None
        assert user["id"] == "1"

    def test_get_user_not_found(self) -> None:
        _load_example_module("apis-and-ingress/http_routing_query_body")
        svc = _import_service(
            "apis-and-ingress/http_routing_query_body", "app.services.user_service"
        )
        user = svc.get_user_by_id("999")
        assert user is None

    def test_create_user(self) -> None:
        _load_example_module("apis-and-ingress/http_routing_query_body")
        svc = _import_service(
            "apis-and-ingress/http_routing_query_body", "app.services.user_service"
        )
        result, status = svc.create_user(
            {"id": "99", "name": "Test User", "email": "test@example.com"}
        )
        assert status == 201
        assert result["name"] == "Test User"

    def test_create_user_missing_fields(self) -> None:
        _load_example_module("apis-and-ingress/http_routing_query_body")
        svc = _import_service(
            "apis-and-ingress/http_routing_query_body", "app.services.user_service"
        )
        result, status = svc.create_user({})
        assert status == 400

    def test_search_users(self) -> None:
        _load_example_module("apis-and-ingress/http_routing_query_body")
        svc = _import_service(
            "apis-and-ingress/http_routing_query_body", "app.services.user_service"
        )
        result = svc.search_users("ada", 10)
        assert "results" in result

    def test_delete_user(self) -> None:
        _load_example_module("apis-and-ingress/http_routing_query_body")
        svc = _import_service(
            "apis-and-ingress/http_routing_query_body", "app.services.user_service"
        )
        _result, status = svc.delete_user("1")
        assert status == 204


class TestHttpAuthLevels:
    """Smoke tests for examples/apis-and-ingress/http_auth_levels."""

    def test_public_message(self) -> None:
        _load_example_module("apis-and-ingress/http_auth_levels")
        svc = _import_service("apis-and-ingress/http_auth_levels", "app.services.auth_service")
        msg = svc.get_public_message()
        assert "public" in msg.lower()

    def test_protected_message(self) -> None:
        _load_example_module("apis-and-ingress/http_auth_levels")
        svc = _import_service("apis-and-ingress/http_auth_levels", "app.services.auth_service")
        msg = svc.get_protected_message()
        assert isinstance(msg, str)

    def test_admin_message(self) -> None:
        _load_example_module("apis-and-ingress/http_auth_levels")
        svc = _import_service("apis-and-ingress/http_auth_levels", "app.services.auth_service")
        msg = svc.get_admin_message()
        assert isinstance(msg, str)


class TestWebhookGithub:
    """Smoke tests for examples/apis-and-ingress/webhook_github."""

    def test_missing_secret_returns_500(self) -> None:
        _load_example_module("apis-and-ingress/webhook_github")
        fn = _import_function_module("apis-and-ingress/webhook_github", "app.functions.webhook")
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
        _load_example_module("apis-and-ingress/webhook_github")
        fn = _import_function_module("apis-and-ingress/webhook_github", "app.functions.webhook")
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
        _load_example_module("apis-and-ingress/webhook_github")
        fn = _import_function_module("apis-and-ingress/webhook_github", "app.functions.webhook")
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
        _load_example_module("apis-and-ingress/webhook_github")
        svc = _import_service("apis-and-ingress/webhook_github", "app.services.webhook_service")
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
        _load_example_module("apis-and-ingress/webhook_github")
        svc = _import_service("apis-and-ingress/webhook_github", "app.services.webhook_service")
        result = svc._handle_pull_request(
            {
                "action": "opened",
                "pull_request": {"title": "Fix bug", "number": 42},
            }
        )
        assert result["event"] == "pull_request"
        assert result["number"] == 42

    def test_handle_issues_helper(self) -> None:
        _load_example_module("apis-and-ingress/webhook_github")
        svc = _import_service("apis-and-ingress/webhook_github", "app.services.webhook_service")
        result = svc._handle_issues(
            {
                "action": "closed",
                "issue": {"title": "Track issue", "number": 7},
            }
        )
        assert result["event"] == "issues"
        assert result["number"] == 7


class TestTimerCronJob:
    """Smoke tests for examples/scheduled-and-background/timer_cron_job."""

    def test_perform_maintenance_helper(self) -> None:
        _load_example_module("scheduled-and-background/timer_cron_job")
        svc = _import_service(
            "scheduled-and-background/timer_cron_job", "app.services.maintenance_service"
        )
        result = svc.perform_maintenance()
        assert "complete" in result.lower()


class TestQueueProducer:
    """Smoke tests for examples/messaging-and-pubsub/queue_producer."""

    def test_validate_payload_valid(self) -> None:
        _load_example_module("messaging-and-pubsub/queue_producer")
        svc = _import_service("messaging-and-pubsub/queue_producer", "app.services.enqueue_service")
        is_valid, error = svc.validate_payload({"task_type": "email", "payload": {}})
        assert is_valid is True
        assert error == ""

    def test_validate_payload_missing_task_type(self) -> None:
        _load_example_module("messaging-and-pubsub/queue_producer")
        svc = _import_service("messaging-and-pubsub/queue_producer", "app.services.enqueue_service")
        is_valid, error = svc.validate_payload({})
        assert is_valid is False
        assert "task_type" in error


class TestQueueConsumer:
    """Smoke tests for examples/messaging-and-pubsub/queue_consumer."""

    def test_process_task_helper(self) -> None:
        _load_example_module("messaging-and-pubsub/queue_consumer")
        svc = _import_service("messaging-and-pubsub/queue_consumer", "app.services.task_service")
        result = svc.process_task({"task_type": "email", "payload": {"to": "a@b.com"}})
        assert "email" in result


class TestBlobUploadProcessor:
    """Smoke tests for examples/blob-and-file-triggers/blob_upload_processor."""

    def test_process_blob_helper(self) -> None:
        _load_example_module("blob-and-file-triggers/blob_upload_processor")
        svc = _import_service(
            "blob-and-file-triggers/blob_upload_processor", "app.services.blob_service"
        )
        result = svc.process_blob(
            blob_name="test.txt",
            blob_size=100,
            metadata={"key": "val"},
            data=b"hello world",
        )
        assert "test.txt" in result
        assert "100" in result


class TestServicebusWorker:
    """Smoke tests for examples/messaging-and-pubsub/servicebus_worker."""

    def test_process_message_helper(self) -> None:
        _load_example_module("messaging-and-pubsub/servicebus_worker")
        svc = _import_service(
            "messaging-and-pubsub/servicebus_worker", "app.services.servicebus_service"
        )
        result = svc.process_message({"task": "send", "priority": "high"})
        assert "send" in result
        assert "high" in result


class TestEventhubConsumer:
    """Smoke tests for examples/streams-and-telemetry/eventhub_consumer."""

    def test_process_telemetry_helper(self) -> None:
        _load_example_module("streams-and-telemetry/eventhub_consumer")
        svc = _import_service(
            "streams-and-telemetry/eventhub_consumer", "app.services.telemetry_service"
        )
        result = svc.process_telemetry({"metric": "cpu_usage", "value": 42.5})
        assert "cpu_usage" in result
        assert "42.5" in result


class TestChangeFeedProcessor:
    """Smoke tests for examples/data-and-pipelines/change_feed_processor."""

    def test_process_change_helper(self) -> None:
        _load_example_module("data-and-pipelines/change_feed_processor")
        svc = _import_service(
            "data-and-pipelines/change_feed_processor", "app.services.change_service"
        )
        result = svc.process_change({"id": "doc-1", "category": "orders"})
        assert "doc-1" in result
        assert "orders" in result


class TestBlueprintModularApp:
    """Smoke tests for examples/runtime-and-ops/blueprint_modular_app."""

    def test_health_service(self) -> None:
        _load_example_module("runtime-and-ops/blueprint_modular_app")
        svc = _import_service(
            "runtime-and-ops/blueprint_modular_app", "app.services.health_service"
        )
        payload = svc.get_health_payload()
        assert payload["status"] == "healthy"

    def test_user_service_list(self) -> None:
        _load_example_module("runtime-and-ops/blueprint_modular_app")
        svc = _import_service("runtime-and-ops/blueprint_modular_app", "app.services.user_service")
        users = svc.list_users()
        assert isinstance(users, list)


class TestOutputBindingVsSdk:
    """Smoke tests for examples/runtime-and-ops/output_binding_vs_sdk."""

    def test_build_payload_helper(self) -> None:
        _load_example_module("runtime-and-ops/output_binding_vs_sdk")
        svc = _import_service(
            "runtime-and-ops/output_binding_vs_sdk", "app.services.payload_service"
        )
        req = func.HttpRequest(
            method="POST",
            url="/api/enqueue/binding",
            body=json.dumps({"task": "process-report"}).encode(),
            headers={"Content-Type": "application/json"},
        )
        payload = svc.build_payload(req)
        assert payload["task"] == "process-report"
        assert payload["source"] == "recipe"


class TestDurableHelloSequence:
    """Smoke tests for examples/orchestration-and-workflows/durable_hello_sequence."""

    def test_greet_activity(self) -> None:
        _load_example_module("orchestration-and-workflows/durable_hello_sequence")
        svc = _import_service(
            "orchestration-and-workflows/durable_hello_sequence", "app.services.greeting_service"
        )
        result = svc.greet("Tokyo")
        assert result == "Hello Tokyo!"


class TestDurableFanOutFanIn:
    """Smoke tests for examples/orchestration-and-workflows/durable_fan_out_fan_in."""

    def test_process_item_activity(self) -> None:
        _load_example_module("orchestration-and-workflows/durable_fan_out_fan_in")
        svc = _import_service(
            "orchestration-and-workflows/durable_fan_out_fan_in", "app.services.processing_service"
        )
        result = svc.process_item("item-1")
        assert result == "Processed item-1"


class TestDurableDeterminismGotchas:
    """Smoke tests for examples/orchestration-and-workflows/durable_determinism_gotchas."""

    def test_fetch_data_activity(self) -> None:
        _load_example_module("orchestration-and-workflows/durable_determinism_gotchas")
        svc = _import_service(
            "orchestration-and-workflows/durable_determinism_gotchas", "app.services.data_service"
        )
        result = svc.fetch_data("resource-1")
        assert "resource-1" in result


class TestDurableUnitTesting:
    """Smoke tests for examples/orchestration-and-workflows/durable_unit_testing."""

    def test_greet_activity(self) -> None:
        _load_example_module("orchestration-and-workflows/durable_unit_testing")
        svc = _import_service(
            "orchestration-and-workflows/durable_unit_testing", "app.services.greeting_service"
        )
        result = svc.greet("Seoul")
        assert result == "Hello Seoul!"


class TestMcpServerExample:
    """Smoke tests for examples/ai-and-agents/mcp_server_example."""

    def test_handle_get_weather(self) -> None:
        _load_example_module("ai-and-agents/mcp_server_example")
        svc = _import_service("ai-and-agents/mcp_server_example", "app.services.mcp_service")
        result = svc._handle_get_weather({"location": "San Francisco, CA"})
        assert "San Francisco" in result

    def test_handle_calculate(self) -> None:
        _load_example_module("ai-and-agents/mcp_server_example")
        svc = _import_service("ai-and-agents/mcp_server_example", "app.services.mcp_service")
        result = svc._handle_calculate({"expression": "2 + 3"})
        assert result == "5"

    def test_handle_calculate_invalid(self) -> None:
        _load_example_module("ai-and-agents/mcp_server_example")
        svc = _import_service("ai-and-agents/mcp_server_example", "app.services.mcp_service")
        result = svc._handle_calculate({"expression": "import os"})
        assert "Error" in result

    def test_mcp_initialize(self) -> None:
        _load_example_module("ai-and-agents/mcp_server_example")
        fn = _import_function_module("ai-and-agents/mcp_server_example", "app.functions.mcp")
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
        _load_example_module("ai-and-agents/mcp_server_example")
        fn = _import_function_module("ai-and-agents/mcp_server_example", "app.functions.mcp")
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
        _load_example_module("ai-and-agents/mcp_server_example")
        fn = _import_function_module("ai-and-agents/mcp_server_example", "app.functions.mcp")
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
        _load_example_module("ai-and-agents/mcp_server_example")
        fn = _import_function_module("ai-and-agents/mcp_server_example", "app.functions.mcp")
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
        _load_example_module("ai-and-agents/mcp_server_example")
        fn = _import_function_module("ai-and-agents/mcp_server_example", "app.functions.mcp")
        req = func.HttpRequest(
            method="POST",
            url="/api/mcp",
            body=b"not json",
            headers={"Content-Type": "application/json"},
        )
        response = fn.mcp(req)
        assert response.status_code == 400


class TestLocalRunAndDirectInvoke:
    """Smoke tests for examples/local_run_and_direct_invoke."""

    def test_greet_with_query_param(self) -> None:
        _load_example_module("guides/local_run_and_direct_invoke")
        fn = _import_function_module("guides/local_run_and_direct_invoke", "app.functions.greet")
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
        _load_example_module("guides/local_run_and_direct_invoke")
        fn = _import_function_module("guides/local_run_and_direct_invoke", "app.functions.greet")
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
        _load_example_module("guides/local_run_and_direct_invoke")
        fn = _import_function_module("guides/local_run_and_direct_invoke", "app.functions.greet")
        req = func.HttpRequest(
            method="GET",
            url="/api/greet",
            body=b"",
            headers={},
        )
        response = fn.greet(req)
        assert response.status_code == 400


class TestAuthEasyAuth:
    """Smoke tests for examples/apis-and-ingress/auth_easyauth."""

    def test_decode_client_principal_valid(self) -> None:
        import base64

        _load_example_module("apis-and-ingress/auth_easyauth")
        svc = _import_service("apis-and-ingress/auth_easyauth", "app.services.auth_service")
        raw = base64.b64encode(
            json.dumps(
                {
                    "auth_typ": "aad",
                    "name_typ": "http://schemas.xmlsoap.org/ws/2005/05/identity/claims/name",
                    "role_typ": "http://schemas.microsoft.com/ws/2008/06/identity/claims/role",
                    "claims": [{"typ": "name", "val": "Alice"}],
                }
            ).encode()
        ).decode()
        principal = svc.decode_client_principal(raw)
        assert principal is not None
        assert principal["auth_typ"] == "aad"

    def test_decode_client_principal_none(self) -> None:
        _load_example_module("apis-and-ingress/auth_easyauth")
        svc = _import_service("apis-and-ingress/auth_easyauth", "app.services.auth_service")
        assert svc.decode_client_principal(None) is None
        assert svc.decode_client_principal("") is None

    def test_extract_claims(self) -> None:
        _load_example_module("apis-and-ingress/auth_easyauth")
        svc = _import_service("apis-and-ingress/auth_easyauth", "app.services.auth_service")
        principal = {
            "auth_typ": "aad",
            "name_typ": "",
            "role_typ": "",
            "claims": [
                {"typ": "name", "val": "Alice"},
                {"typ": "email", "val": "alice@example.com"},
            ],
        }
        claims = svc.extract_claims(principal)
        assert claims["name"] == "Alice"
        assert claims["email"] == "alice@example.com"

    def test_get_roles(self) -> None:
        _load_example_module("apis-and-ingress/auth_easyauth")
        svc = _import_service("apis-and-ingress/auth_easyauth", "app.services.auth_service")
        principal = {
            "auth_typ": "aad",
            "name_typ": "",
            "role_typ": "",
            "claims": [{"typ": "roles", "val": "admin"}, {"typ": "roles", "val": "reader"}],
        }
        roles = svc.get_roles(principal)
        assert "admin" in roles
        assert "reader" in roles

    def test_has_role(self) -> None:
        _load_example_module("apis-and-ingress/auth_easyauth")
        svc = _import_service("apis-and-ingress/auth_easyauth", "app.services.auth_service")
        principal = {
            "auth_typ": "aad",
            "name_typ": "",
            "role_typ": "",
            "claims": [{"typ": "roles", "val": "admin"}],
        }
        assert svc.has_role(principal, "admin") is True
        assert svc.has_role(principal, "superuser") is False

    def test_get_user_claims_response(self) -> None:
        _load_example_module("apis-and-ingress/auth_easyauth")
        svc = _import_service("apis-and-ingress/auth_easyauth", "app.services.auth_service")
        principal = {
            "auth_typ": "aad",
            "name_typ": "",
            "role_typ": "",
            "claims": [
                {"typ": "name", "val": "Alice"},
                {"typ": "roles", "val": "admin"},
                {
                    "typ": "http://schemas.xmlsoap.org/ws/2005/05/identity/claims/nameidentifier",
                    "val": "user-1",
                },
            ],
        }
        body, status = svc.get_user_claims_response(principal)
        assert status == 200
        assert body["user_id"] == "user-1"
        assert body["identity_provider"] == "aad"
        assert "admin" in body["roles"]

    def test_get_admin_response_with_role(self) -> None:
        _load_example_module("apis-and-ingress/auth_easyauth")
        svc = _import_service("apis-and-ingress/auth_easyauth", "app.services.auth_service")
        principal = {
            "auth_typ": "aad",
            "name_typ": "",
            "role_typ": "",
            "claims": [{"typ": "roles", "val": "admin"}],
        }
        body, status = svc.get_admin_response(principal)
        assert status == 200
        assert body["message"] == "Welcome, admin!"

    def test_get_admin_response_without_role(self) -> None:
        _load_example_module("apis-and-ingress/auth_easyauth")
        svc = _import_service("apis-and-ingress/auth_easyauth", "app.services.auth_service")
        principal = {
            "auth_typ": "aad",
            "name_typ": "",
            "role_typ": "",
            "claims": [{"typ": "name", "val": "Alice"}],
        }
        body, status = svc.get_admin_response(principal)
        assert status == 403


class TestAuthJwtValidation:
    """Smoke tests for examples/apis-and-ingress/auth_jwt_validation."""

    def test_extract_bearer_token_valid(self) -> None:
        _load_example_module("apis-and-ingress/auth_jwt_validation")
        svc = _import_service("apis-and-ingress/auth_jwt_validation", "app.services.jwt_service")
        assert svc.extract_bearer_token("Bearer abc123") == "abc123"

    def test_extract_bearer_token_missing(self) -> None:
        _load_example_module("apis-and-ingress/auth_jwt_validation")
        svc = _import_service("apis-and-ingress/auth_jwt_validation", "app.services.jwt_service")
        assert svc.extract_bearer_token(None) is None
        assert svc.extract_bearer_token("") is None
        assert svc.extract_bearer_token("Basic abc") is None
        assert svc.extract_bearer_token("Bearer ") is None

    def test_has_claim_present(self) -> None:
        _load_example_module("apis-and-ingress/auth_jwt_validation")
        svc = _import_service("apis-and-ingress/auth_jwt_validation", "app.services.jwt_service")
        claims = {"sub": "user-1", "roles": "api.read"}
        assert svc.has_claim(claims, "sub") is True
        assert svc.has_claim(claims, "roles", "api.read") is True
        assert svc.has_claim(claims, "roles", "api.write") is False

    def test_has_claim_boolean(self) -> None:
        _load_example_module("apis-and-ingress/auth_jwt_validation")
        svc = _import_service("apis-and-ingress/auth_jwt_validation", "app.services.jwt_service")
        claims = {"email_verified": True}
        assert svc.has_claim(claims, "email_verified", "true") is True
        assert svc.has_claim(claims, "email_verified", "false") is False

    def test_has_claim_missing(self) -> None:
        _load_example_module("apis-and-ingress/auth_jwt_validation")
        svc = _import_service("apis-and-ingress/auth_jwt_validation", "app.services.jwt_service")
        claims = {"sub": "user-1"}
        assert svc.has_claim(claims, "email") is False

    def test_get_profile_response(self) -> None:
        _load_example_module("apis-and-ingress/auth_jwt_validation")
        svc = _import_service("apis-and-ingress/auth_jwt_validation", "app.services.jwt_service")
        claims = {"sub": "user-1", "name": "Alice", "email": "alice@example.com", "iat": 123}
        body, status = svc.get_profile_response(claims)
        assert status == 200
        assert body["subject"] == "user-1"
        assert body["name"] == "Alice"
        assert "iat" not in body["claims"]

    def test_get_protected_response_with_claim(self) -> None:
        _load_example_module("apis-and-ingress/auth_jwt_validation")
        svc = _import_service("apis-and-ingress/auth_jwt_validation", "app.services.jwt_service")
        claims = {"sub": "user-1", "roles": "api.read"}
        body, status = svc.get_protected_response(claims)
        assert status == 200
        assert body["message"] == "Access granted to protected resource."

    def test_get_protected_response_without_claim(self) -> None:
        _load_example_module("apis-and-ingress/auth_jwt_validation")
        svc = _import_service("apis-and-ingress/auth_jwt_validation", "app.services.jwt_service")
        claims = {"sub": "user-1"}
        body, status = svc.get_protected_response(claims)
        assert status == 403


class TestAuthMultitenant:
    """Smoke tests for examples/apis-and-ingress/auth_multitenant."""

    def test_decode_client_principal_valid(self) -> None:
        import base64

        _load_example_module("apis-and-ingress/auth_multitenant")
        svc = _import_service("apis-and-ingress/auth_multitenant", "app.services.tenant_service")
        raw = base64.b64encode(
            json.dumps(
                {
                    "auth_typ": "aad",
                    "name_typ": "",
                    "role_typ": "",
                    "claims": [{"typ": "tid", "val": "tenant-1"}],
                }
            ).encode()
        ).decode()
        principal = svc.decode_client_principal(raw)
        assert principal is not None
        assert principal["auth_typ"] == "aad"

    def test_decode_client_principal_none(self) -> None:
        _load_example_module("apis-and-ingress/auth_multitenant")
        svc = _import_service("apis-and-ingress/auth_multitenant", "app.services.tenant_service")
        assert svc.decode_client_principal(None) is None
        assert svc.decode_client_principal("") is None

    def test_extract_tenant_id(self) -> None:
        _load_example_module("apis-and-ingress/auth_multitenant")
        svc = _import_service("apis-and-ingress/auth_multitenant", "app.services.tenant_service")
        principal = {"claims": [{"typ": "tid", "val": "tenant-1"}]}
        assert svc.extract_tenant_id(principal) == "tenant-1"

    def test_extract_tenant_id_missing(self) -> None:
        _load_example_module("apis-and-ingress/auth_multitenant")
        svc = _import_service("apis-and-ingress/auth_multitenant", "app.services.tenant_service")
        principal = {"claims": [{"typ": "name", "val": "Alice"}]}
        assert svc.extract_tenant_id(principal) is None

    def test_parse_allowed_tenants(self) -> None:
        _load_example_module("apis-and-ingress/auth_multitenant")
        svc = _import_service("apis-and-ingress/auth_multitenant", "app.services.tenant_service")
        assert svc.parse_allowed_tenants("") == []
        assert svc.parse_allowed_tenants("a,b,c") == ["a", "b", "c"]
        assert svc.parse_allowed_tenants(" a , b ") == ["a", "b"]

    def test_is_tenant_allowed(self) -> None:
        _load_example_module("apis-and-ingress/auth_multitenant")
        svc = _import_service("apis-and-ingress/auth_multitenant", "app.services.tenant_service")
        assert svc.is_tenant_allowed("tenant-1", ["tenant-1", "tenant-2"]) is True
        assert svc.is_tenant_allowed("tenant-3", ["tenant-1", "tenant-2"]) is False
        assert svc.is_tenant_allowed("tenant-1", []) is False

    def test_get_data_response(self) -> None:
        _load_example_module("apis-and-ingress/auth_multitenant")
        svc = _import_service("apis-and-ingress/auth_multitenant", "app.services.tenant_service")
        principal = {
            "auth_typ": "aad",
            "name_typ": "",
            "role_typ": "",
            "claims": [
                {
                    "typ": "http://schemas.xmlsoap.org/ws/2005/05/identity/claims/nameidentifier",
                    "val": "user-1",
                },
            ],
        }
        body, status = svc.get_data_response(principal, "tenant-1")
        assert status == 200
        assert body["tenant_id"] == "tenant-1"
        assert body["user_id"] == "user-1"


class TestDoctorDiagnosticsEndpoint:
    """Smoke tests for examples/runtime-and-ops/doctor_diagnostics_endpoint."""

    def test_health_service(self) -> None:
        _load_example_module("runtime-and-ops/doctor_diagnostics_endpoint")
        svc = _import_service(
            "runtime-and-ops/doctor_diagnostics_endpoint",
            "app.services.diagnostics_service",
        )
        assert svc.get_health_payload() == {"status": "healthy"}

    def test_run_project_diagnostics_returns_section_list(self) -> None:
        _load_example_module("runtime-and-ops/doctor_diagnostics_endpoint")
        svc = _import_service(
            "runtime-and-ops/doctor_diagnostics_endpoint",
            "app.services.diagnostics_service",
        )
        target = str(EXAMPLES_DIR / "runtime-and-ops" / "doctor_diagnostics_endpoint")
        sections = svc.run_project_diagnostics(target)
        assert isinstance(sections, list)
        assert sections, "Doctor should return at least one section for the recipe project"
        for section in sections:
            assert "title" in section
            assert "category" in section
            assert "status" in section

    def test_summarize_reduces_sections(self) -> None:
        _load_example_module("runtime-and-ops/doctor_diagnostics_endpoint")
        svc = _import_service(
            "runtime-and-ops/doctor_diagnostics_endpoint",
            "app.services.diagnostics_service",
        )
        fixture = [
            {"title": "T1", "category": "c1", "status": "pass", "items": []},
            {"title": "T2", "category": "c2", "status": "pass", "items": []},
        ]
        result = svc.summarize(fixture)
        assert result["overall"] == "pass"
        assert len(result["sections"]) == 2


class TestScaffoldWalkthroughApp:
    """Smoke tests for examples/apis-and-ingress/scaffold_walkthrough_app."""

    def test_health_endpoint(self) -> None:
        _load_example_module("apis-and-ingress/scaffold_walkthrough_app")
        fn = _import_function_module(
            "apis-and-ingress/scaffold_walkthrough_app", "app.functions.health"
        )
        request = func.HttpRequest(
            method="GET",
            url="http://localhost/api/health",
            params={},
            body=b"",
        )
        response = fn.health(request)
        assert response.status_code == 200
        body = json.loads(response.get_body())
        assert body == {"status": "ok"}

    def test_health_service(self) -> None:
        _load_example_module("apis-and-ingress/scaffold_walkthrough_app")
        svc = _import_service(
            "apis-and-ingress/scaffold_walkthrough_app", "app.services.health_service"
        )
        assert svc.check_health() == {"status": "ok"}

    def test_webhook_service_signature_verification(self) -> None:
        _load_example_module("apis-and-ingress/scaffold_walkthrough_app")
        svc = _import_service(
            "apis-and-ingress/scaffold_walkthrough_app", "app.services.webhook_service"
        )
        secret = "test-secret"
        payload = b'{"event": "test"}'
        digest = hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()
        assert svc.verify_signature(payload, f"sha256={digest}", secret) is True
        assert svc.verify_signature(payload, "sha256=invalid", secret) is False
        assert svc.verify_signature(payload, "no-prefix", secret) is False


class TestOpenaiDirectChat:
    def test_complete_chat_fallback_returns_expected_response(self) -> None:
        module = _load_example_module("ai-and-agents/openai_direct_chat")
        endpoint_backup = os.environ.pop("AZURE_OPENAI_ENDPOINT", None)
        api_key_backup = os.environ.pop("AZURE_OPENAI_KEY", None)
        try:
            result = module._complete_chat("test message", "system prompt")
            assert result == (
                "Fallback response: Azure Functions can call Azure OpenAI from an HTTP "
                "trigger and return the generated answer as JSON."
            )
        finally:
            if endpoint_backup is not None:
                os.environ["AZURE_OPENAI_ENDPOINT"] = endpoint_backup
            if api_key_backup is not None:
                os.environ["AZURE_OPENAI_KEY"] = api_key_backup

    def test_complete_chat_fallback_is_deterministic(self) -> None:
        module = _load_example_module("ai-and-agents/openai_direct_chat")
        endpoint_backup = os.environ.pop("AZURE_OPENAI_ENDPOINT", None)
        api_key_backup = os.environ.pop("AZURE_OPENAI_KEY", None)
        try:
            first = module._complete_chat("first prompt", "system prompt")
            second = module._complete_chat("second prompt", "different prompt")
            assert first == second
            assert "Azure Functions" in first
        finally:
            if endpoint_backup is not None:
                os.environ["AZURE_OPENAI_ENDPOINT"] = endpoint_backup
            if api_key_backup is not None:
                os.environ["AZURE_OPENAI_KEY"] = api_key_backup


class TestDurableAiPipeline:
    def test_openai_and_search_clients_return_none_without_env_vars(self) -> None:
        module = _load_example_module("ai-and-agents/durable_ai_pipeline")
        endpoint_backup = os.environ.pop("AZURE_OPENAI_ENDPOINT", None)
        openai_key_backup = os.environ.pop("AZURE_OPENAI_KEY", None)
        search_endpoint_backup = os.environ.pop("AI_SEARCH_ENDPOINT", None)
        search_key_backup = os.environ.pop("AI_SEARCH_KEY", None)
        search_index_backup = os.environ.pop("AI_SEARCH_INDEX", None)
        try:
            assert module._openai_client() is None
            assert module._search_client() is None
        finally:
            if endpoint_backup is not None:
                os.environ["AZURE_OPENAI_ENDPOINT"] = endpoint_backup
            if openai_key_backup is not None:
                os.environ["AZURE_OPENAI_KEY"] = openai_key_backup
            if search_endpoint_backup is not None:
                os.environ["AI_SEARCH_ENDPOINT"] = search_endpoint_backup
            if search_key_backup is not None:
                os.environ["AI_SEARCH_KEY"] = search_key_backup
            if search_index_backup is not None:
                os.environ["AI_SEARCH_INDEX"] = search_index_backup

    def test_embed_query_fallback_returns_mock_vector(self) -> None:
        module = _load_example_module("ai-and-agents/durable_ai_pipeline")
        endpoint_backup = os.environ.pop("AZURE_OPENAI_ENDPOINT", None)
        openai_key_backup = os.environ.pop("AZURE_OPENAI_KEY", None)
        try:
            result = module.embed_query({"question": "What is Azure Functions?"})
            assert result == [0.12, 0.34, 0.56]
        finally:
            if endpoint_backup is not None:
                os.environ["AZURE_OPENAI_ENDPOINT"] = endpoint_backup
            if openai_key_backup is not None:
                os.environ["AZURE_OPENAI_KEY"] = openai_key_backup

    def test_search_documents_fallback_returns_mock_results(self) -> None:
        module = _load_example_module("ai-and-agents/durable_ai_pipeline")
        search_endpoint_backup = os.environ.pop("AI_SEARCH_ENDPOINT", None)
        search_key_backup = os.environ.pop("AI_SEARCH_KEY", None)
        search_index_backup = os.environ.pop("AI_SEARCH_INDEX", None)
        try:
            result = module.search_documents({"vector": [0.12, 0.34, 0.56], "top_k": 3})
            assert len(result) == 1
            assert result[0]["id"] == "doc-1"
            assert "Azure Functions" in result[0]["title"]
            assert result[0]["score"] == 0.91
        finally:
            if search_endpoint_backup is not None:
                os.environ["AI_SEARCH_ENDPOINT"] = search_endpoint_backup
            if search_key_backup is not None:
                os.environ["AI_SEARCH_KEY"] = search_key_backup
            if search_index_backup is not None:
                os.environ["AI_SEARCH_INDEX"] = search_index_backup

    def test_generate_answer_fallback_returns_expected_text(self) -> None:
        module = _load_example_module("ai-and-agents/durable_ai_pipeline")
        endpoint_backup = os.environ.pop("AZURE_OPENAI_ENDPOINT", None)
        openai_key_backup = os.environ.pop("AZURE_OPENAI_KEY", None)
        try:
            result = module.generate_answer(
                {
                    "question": "How does Azure Functions scale?",
                    "documents": [
                        {"content": "Azure Functions automatically scales based on demand."}
                    ],
                }
            )
            assert result.startswith("Fallback durable answer:")
            assert "scales automatically based on demand" in result
        finally:
            if endpoint_backup is not None:
                os.environ["AZURE_OPENAI_ENDPOINT"] = endpoint_backup
            if openai_key_backup is not None:
                os.environ["AZURE_OPENAI_KEY"] = openai_key_backup


class TestStreamingAiResponse:
    def test_stream_frames_fallback_contains_message_and_data_lines(self) -> None:
        module = _load_example_module("ai-and-agents/streaming_ai_response")
        endpoint_backup = os.environ.pop("AZURE_OPENAI_ENDPOINT", None)
        api_key_backup = os.environ.pop("AZURE_OPENAI_KEY", None)
        try:
            result = module._stream_frames("test message", "system prompt")
            assert "data: " in result
            assert "test message" in result
            assert '{"delta": "Azure Functions "}' in result
            assert '{"delta": "can stream Azure OpenAI output "}' in result
        finally:
            if endpoint_backup is not None:
                os.environ["AZURE_OPENAI_ENDPOINT"] = endpoint_backup
            if api_key_backup is not None:
                os.environ["AZURE_OPENAI_KEY"] = api_key_backup

    def test_stream_frames_fallback_includes_done_event(self) -> None:
        module = _load_example_module("ai-and-agents/streaming_ai_response")
        endpoint_backup = os.environ.pop("AZURE_OPENAI_ENDPOINT", None)
        api_key_backup = os.environ.pop("AZURE_OPENAI_KEY", None)
        try:
            result = module._stream_frames("test message", "system prompt")
            assert "event: done\n" in result
            assert 'data: {"status": "completed"}' in result
        finally:
            if endpoint_backup is not None:
                os.environ["AZURE_OPENAI_ENDPOINT"] = endpoint_backup
            if api_key_backup is not None:
                os.environ["AZURE_OPENAI_KEY"] = api_key_backup


class TestAiImageGeneration:
    def test_generate_image_fallback_returns_example_image(self) -> None:
        module = _load_example_module("ai-and-agents/ai_image_generation")
        endpoint_backup = os.environ.pop("AZURE_OPENAI_ENDPOINT", None)
        api_key_backup = os.environ.pop("AZURE_OPENAI_KEY", None)
        deployment_backup = os.environ.pop("AZURE_OPENAI_IMAGE_DEPLOYMENT", None)
        try:
            result = module._generate_image("draw a function app", "1024x1024")
            assert result.image_url == (
                "https://example.blob.core.windows.net/generated/fallback-image.png"
            )
            assert result.revised_prompt == "draw a function app"
            assert result.deployment == "dall-e-3"
        finally:
            if endpoint_backup is not None:
                os.environ["AZURE_OPENAI_ENDPOINT"] = endpoint_backup
            if api_key_backup is not None:
                os.environ["AZURE_OPENAI_KEY"] = api_key_backup
            if deployment_backup is not None:
                os.environ["AZURE_OPENAI_IMAGE_DEPLOYMENT"] = deployment_backup

    def test_generate_image_fallback_honors_deployment_env(self) -> None:
        module = _load_example_module("ai-and-agents/ai_image_generation")
        endpoint_backup = os.environ.pop("AZURE_OPENAI_ENDPOINT", None)
        api_key_backup = os.environ.pop("AZURE_OPENAI_KEY", None)
        deployment_backup = os.environ.get("AZURE_OPENAI_IMAGE_DEPLOYMENT")
        os.environ["AZURE_OPENAI_IMAGE_DEPLOYMENT"] = "image-test-deployment"
        try:
            result = module._generate_image("draw a queue", "1792x1024")
            assert result.deployment == "image-test-deployment"
            assert result.revised_prompt == "draw a queue"
        finally:
            if endpoint_backup is not None:
                os.environ["AZURE_OPENAI_ENDPOINT"] = endpoint_backup
            if api_key_backup is not None:
                os.environ["AZURE_OPENAI_KEY"] = api_key_backup
            if deployment_backup is None:
                os.environ.pop("AZURE_OPENAI_IMAGE_DEPLOYMENT", None)
            else:
                os.environ["AZURE_OPENAI_IMAGE_DEPLOYMENT"] = deployment_backup


class TestEmbeddingVectorSearch:
    def test_openai_and_search_clients_return_none_without_env_vars(self) -> None:
        module = _load_example_module("ai-and-agents/embedding_vector_search")
        endpoint_backup = os.environ.pop("AZURE_OPENAI_ENDPOINT", None)
        openai_key_backup = os.environ.pop("AZURE_OPENAI_KEY", None)
        search_endpoint_backup = os.environ.pop("AI_SEARCH_ENDPOINT", None)
        search_key_backup = os.environ.pop("AI_SEARCH_KEY", None)
        search_index_backup = os.environ.pop("AI_SEARCH_INDEX", None)
        try:
            assert module._openai_client() is None
            assert module._search_client() is None
        finally:
            if endpoint_backup is not None:
                os.environ["AZURE_OPENAI_ENDPOINT"] = endpoint_backup
            if openai_key_backup is not None:
                os.environ["AZURE_OPENAI_KEY"] = openai_key_backup
            if search_endpoint_backup is not None:
                os.environ["AI_SEARCH_ENDPOINT"] = search_endpoint_backup
            if search_key_backup is not None:
                os.environ["AI_SEARCH_KEY"] = search_key_backup
            if search_index_backup is not None:
                os.environ["AI_SEARCH_INDEX"] = search_index_backup

    def test_vector_search_fallback_returns_mock_search_result(self) -> None:
        module = _load_example_module("ai-and-agents/embedding_vector_search")
        endpoint_backup = os.environ.pop("AZURE_OPENAI_ENDPOINT", None)
        openai_key_backup = os.environ.pop("AZURE_OPENAI_KEY", None)
        search_endpoint_backup = os.environ.pop("AI_SEARCH_ENDPOINT", None)
        search_key_backup = os.environ.pop("AI_SEARCH_KEY", None)
        search_index_backup = os.environ.pop("AI_SEARCH_INDEX", None)
        try:
            result = module._vector_search("azure functions scaling", 5)
            assert len(result) == 1
            assert result[0].id == "doc-1"
            assert result[0].title == "Azure Functions overview"
            assert "scales based on demand" in result[0].content
            assert result[0].score == 0.92
        finally:
            if endpoint_backup is not None:
                os.environ["AZURE_OPENAI_ENDPOINT"] = endpoint_backup
            if openai_key_backup is not None:
                os.environ["AZURE_OPENAI_KEY"] = openai_key_backup
            if search_endpoint_backup is not None:
                os.environ["AI_SEARCH_ENDPOINT"] = search_endpoint_backup
            if search_key_backup is not None:
                os.environ["AI_SEARCH_KEY"] = search_key_backup
            if search_index_backup is not None:
                os.environ["AI_SEARCH_INDEX"] = search_index_backup

    def test_vector_search_fallback_returns_search_result_models(self) -> None:
        module = _load_example_module("ai-and-agents/embedding_vector_search")
        endpoint_backup = os.environ.pop("AZURE_OPENAI_ENDPOINT", None)
        openai_key_backup = os.environ.pop("AZURE_OPENAI_KEY", None)
        search_endpoint_backup = os.environ.pop("AI_SEARCH_ENDPOINT", None)
        search_key_backup = os.environ.pop("AI_SEARCH_KEY", None)
        search_index_backup = os.environ.pop("AI_SEARCH_INDEX", None)
        try:
            result = module._vector_search("test query", 1)
            assert isinstance(result[0], module.SearchResult)
            assert result[0].model_dump() == {
                "id": "doc-1",
                "title": "Azure Functions overview",
                "content": "Azure Functions automatically scales based on demand.",
                "score": 0.92,
            }
        finally:
            if endpoint_backup is not None:
                os.environ["AZURE_OPENAI_ENDPOINT"] = endpoint_backup
            if openai_key_backup is not None:
                os.environ["AZURE_OPENAI_KEY"] = openai_key_backup
            if search_endpoint_backup is not None:
                os.environ["AI_SEARCH_ENDPOINT"] = search_endpoint_backup
            if search_key_backup is not None:
                os.environ["AI_SEARCH_KEY"] = search_key_backup
            if search_index_backup is not None:
                os.environ["AI_SEARCH_INDEX"] = search_index_backup
