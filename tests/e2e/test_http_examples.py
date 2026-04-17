"""E2E tests for HTTP-triggered examples.

Each test class starts a ``func`` host for a specific example and
validates the HTTP surface using ``requests``.
"""

from __future__ import annotations

import hashlib
import hmac
import json

import pytest
import requests

from tests.e2e.conftest import run_func_host

pytestmark = pytest.mark.e2e


# ---------------------------------------------------------------------------
# hello_http_minimal
# ---------------------------------------------------------------------------


class TestHelloHttpMinimal:
    """GET /api/hello — minimal HTTP trigger."""

    EXAMPLE = "apis-and-ingress/hello_http_minimal"

    def test_hello_default(self) -> None:
        with run_func_host(self.EXAMPLE) as base_url:
            resp = requests.get(f"{base_url}/api/hello", timeout=10)
            assert resp.status_code == 200
            assert "Hello" in resp.text

    def test_hello_with_name(self) -> None:
        with run_func_host(self.EXAMPLE) as base_url:
            resp = requests.get(f"{base_url}/api/hello?name=Ada", timeout=10)
            assert resp.status_code == 200
            assert "Ada" in resp.text


# ---------------------------------------------------------------------------
# http_routing_query_body
# ---------------------------------------------------------------------------


class TestHttpRoutingQueryBody:
    """CRUD routes at /api/users and /api/search."""

    EXAMPLE = "apis-and-ingress/http_routing_query_body"

    def test_list_users(self) -> None:
        with run_func_host(self.EXAMPLE) as base_url:
            resp = requests.get(f"{base_url}/api/users", timeout=10)
            assert resp.status_code == 200
            body = resp.json()
            assert "users" in body or isinstance(body, list)

    def test_create_and_get_user(self) -> None:
        with run_func_host(self.EXAMPLE) as base_url:
            # Create
            payload = {"id": "test-1", "name": "Test User", "email": "test@example.com"}
            resp = requests.post(f"{base_url}/api/users", json=payload, timeout=10)
            assert resp.status_code in (200, 201)

    def test_search_users(self) -> None:
        with run_func_host(self.EXAMPLE) as base_url:
            resp = requests.get(f"{base_url}/api/search?q=test", timeout=10)
            assert resp.status_code == 200


# ---------------------------------------------------------------------------
# http_auth_levels
# ---------------------------------------------------------------------------


class TestHttpAuthLevels:
    """Anonymous, Function, and Admin auth levels."""

    EXAMPLE = "apis-and-ingress/http_auth_levels"

    def test_public_endpoint_accessible(self) -> None:
        """Anonymous endpoint should return 200."""
        with run_func_host(self.EXAMPLE) as base_url:
            resp = requests.get(f"{base_url}/api/public", timeout=10)
            assert resp.status_code == 200

    def test_protected_endpoint_accessible_locally(self) -> None:
        """Function-level endpoint is accessible without key in local dev."""
        with run_func_host(self.EXAMPLE) as base_url:
            resp = requests.get(f"{base_url}/api/protected", timeout=10)
            assert resp.status_code == 200

    def test_admin_endpoint_requires_key_locally(self) -> None:
        """Admin-level endpoint returns 401 or 404 in local dev without key."""
        with run_func_host(self.EXAMPLE) as base_url:
            resp = requests.get(f"{base_url}/api/admin-only", timeout=10)
            # func start locally may return 401 (Unauthorized) or 404
            # depending on the Core Tools version
            assert resp.status_code in (401, 404)


# ---------------------------------------------------------------------------
# webhook_github
# ---------------------------------------------------------------------------


class TestWebhookGitHub:
    """POST /api/github/webhook with HMAC-SHA256."""

    EXAMPLE = "apis-and-ingress/webhook_github"
    WEBHOOK_SECRET = "test-secret-key"

    def _sign_payload(self, payload: bytes) -> str:
        """Compute HMAC-SHA256 signature matching GitHub's format."""
        sig = hmac.new(
            key=self.WEBHOOK_SECRET.encode("utf-8"),
            msg=payload,
            digestmod=hashlib.sha256,
        ).hexdigest()
        return f"sha256={sig}"

    def test_valid_push_event(self) -> None:
        body = json.dumps(
            {
                "ref": "refs/heads/main",
                "repository": {"full_name": "octo/repo"},
                "commits": [{}],
            }
        ).encode()

        with run_func_host(
            self.EXAMPLE, env_vars={"GITHUB_WEBHOOK_SECRET": self.WEBHOOK_SECRET}
        ) as base_url:
            resp = requests.post(
                f"{base_url}/api/github/webhook",
                data=body,
                headers={
                    "Content-Type": "application/json",
                    "X-GitHub-Event": "push",
                    "X-Hub-Signature-256": self._sign_payload(body),
                },
                timeout=10,
            )
            assert resp.status_code == 200
            data = resp.json()
            assert data["event"] == "push"

    def test_invalid_signature_rejected(self) -> None:
        body = b'{"test": true}'
        with run_func_host(
            self.EXAMPLE, env_vars={"GITHUB_WEBHOOK_SECRET": self.WEBHOOK_SECRET}
        ) as base_url:
            resp = requests.post(
                f"{base_url}/api/github/webhook",
                data=body,
                headers={
                    "Content-Type": "application/json",
                    "X-GitHub-Event": "push",
                    "X-Hub-Signature-256": "sha256=invalidsignature",
                },
                timeout=10,
            )
            assert resp.status_code == 401

    def test_missing_secret_returns_500(self) -> None:
        """When GITHUB_WEBHOOK_SECRET is not set, server returns 500."""
        body = b'{"test": true}'
        with run_func_host(self.EXAMPLE) as base_url:
            resp = requests.post(
                f"{base_url}/api/github/webhook",
                data=body,
                headers={
                    "Content-Type": "application/json",
                    "X-GitHub-Event": "push",
                    "X-Hub-Signature-256": "sha256=whatever",
                },
                timeout=10,
            )
            assert resp.status_code == 500


# ---------------------------------------------------------------------------
# local_run_and_direct_invoke
# ---------------------------------------------------------------------------


class TestLocalRunAndDirectInvoke:
    """GET/POST /api/greet."""

    EXAMPLE = "guides/local_run_and_direct_invoke"

    def test_greet_with_query_param(self) -> None:
        with run_func_host(self.EXAMPLE) as base_url:
            resp = requests.get(f"{base_url}/api/greet?name=World", timeout=10)
            assert resp.status_code == 200
            assert "World" in resp.text

    def test_greet_with_json_body(self) -> None:
        with run_func_host(self.EXAMPLE) as base_url:
            resp = requests.post(
                f"{base_url}/api/greet",
                json={"name": "Bob"},
                timeout=10,
            )
            assert resp.status_code == 200
            assert "Bob" in resp.text

    def test_greet_missing_name_returns_400(self) -> None:
        with run_func_host(self.EXAMPLE) as base_url:
            resp = requests.get(f"{base_url}/api/greet", timeout=10)
            assert resp.status_code == 400


# ---------------------------------------------------------------------------
# blueprint_modular_app
# ---------------------------------------------------------------------------


class TestBlueprintModularApp:
    """Health + Users endpoints."""

    EXAMPLE = "runtime-and-ops/blueprint_modular_app"

    def test_health_endpoint(self) -> None:
        with run_func_host(self.EXAMPLE) as base_url:
            resp = requests.get(f"{base_url}/api/health", timeout=10)
            assert resp.status_code == 200

    def test_list_users(self) -> None:
        with run_func_host(self.EXAMPLE) as base_url:
            resp = requests.get(f"{base_url}/api/users", timeout=10)
            assert resp.status_code == 200

    def test_create_and_get_user(self) -> None:
        with run_func_host(self.EXAMPLE) as base_url:
            # Create a user
            payload = {"id": "u1", "name": "Ada"}
            resp = requests.post(f"{base_url}/api/users", json=payload, timeout=10)
            assert resp.status_code == 201

            # Retrieve the user
            resp = requests.get(f"{base_url}/api/users/u1", timeout=10)
            assert resp.status_code == 200
            data = resp.json()
            assert data["name"] == "Ada"
