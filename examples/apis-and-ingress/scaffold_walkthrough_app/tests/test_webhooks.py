from __future__ import annotations

import hashlib
import hmac
import json
import os
from unittest.mock import patch

import azure.functions as func

from app.functions.webhooks import receive_webhook
from app.services.webhook_service import webhook_store


def _make_request(
    method: str,
    url: str,
    *,
    body: bytes = b"",
    headers: dict[str, str] | None = None,
) -> func.HttpRequest:
    return func.HttpRequest(
        method=method,
        url=url,
        params={},
        body=body,
        route_params={},
        headers=headers or {},
    )


def _sign(payload: bytes, secret: str) -> str:
    """Compute HMAC-SHA256 signature for *payload*."""
    digest = hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()
    return f"sha256={digest}"


VALID_PAYLOAD = json.dumps({
    "event_type": "order.completed",
    "source": "shopify",
    "occurred_at": "2026-04-12T12:00:00Z",
    "data": {"order_id": "12345"},
}).encode()


class TestReceiveWebhook:
    def test_accepts_valid_webhook(self) -> None:
        webhook_store.clear()
        secret = "test-secret-key"
        signature = _sign(VALID_PAYLOAD, secret)

        with patch.dict(os.environ, {"WEBHOOK_SECRET": secret}):
            request = _make_request(
                "POST",
                "http://localhost/api/webhooks/inbound",
                body=VALID_PAYLOAD,
                headers={
                    "Content-Type": "application/json",
                    "X-Signature": signature,
                },
            )
            response = receive_webhook(request)

        assert response.status_code == 202
        body = json.loads(response.get_body())
        assert body["status"] == "accepted"
        assert body["delivery_id"].startswith("dlv_")
        assert "received_at" in body

    def test_returns_400_for_invalid_json(self) -> None:
        webhook_store.clear()
        secret = "test-secret-key"
        signature = _sign(b"not-json", secret)

        with patch.dict(os.environ, {"WEBHOOK_SECRET": secret}):
            request = _make_request(
                "POST",
                "http://localhost/api/webhooks/inbound",
                body=b"not-json",
                headers={
                    "Content-Type": "application/json",
                    "X-Signature": signature,
                },
            )
            response = receive_webhook(request)

        assert response.status_code == 400


    def test_returns_422_for_invalid_schema(self) -> None:
        webhook_store.clear()
        payload = json.dumps({"data": {}}).encode()
        secret = "test-secret-key"
        signature = _sign(payload, secret)

        with patch.dict(os.environ, {"WEBHOOK_SECRET": secret}):
            request = _make_request(
                "POST",
                "http://localhost/api/webhooks/inbound",
                body=payload,
                headers={
                    "Content-Type": "application/json",
                    "X-Signature": signature,
                },
            )
            response = receive_webhook(request)

        assert response.status_code == 422
        body = json.loads(response.get_body())
        assert "Validation error" in body["error"]

    def test_returns_422_for_non_object_json(self) -> None:
        webhook_store.clear()
        payload = json.dumps(["not", "an", "object"]).encode()
        secret = "test-secret-key"
        signature = _sign(payload, secret)

        with patch.dict(os.environ, {"WEBHOOK_SECRET": secret}):
            request = _make_request(
                "POST",
                "http://localhost/api/webhooks/inbound",
                body=payload,
                headers={
                    "Content-Type": "application/json",
                    "X-Signature": signature,
                },
            )
            response = receive_webhook(request)

        assert response.status_code == 422


class TestWebhookSignatureVerification:
    def test_rejects_invalid_signature_when_secret_set(self) -> None:
        webhook_store.clear()

        with patch.dict(os.environ, {"WEBHOOK_SECRET": "test-secret-key"}):
            request = _make_request(
                "POST",
                "http://localhost/api/webhooks/inbound",
                body=VALID_PAYLOAD,
                headers={
                    "Content-Type": "application/json",
                    "X-Signature": "sha256=invalid",
                },
            )
            response = receive_webhook(request)

        assert response.status_code == 401

    def test_accepts_valid_signature_when_secret_set(self) -> None:
        webhook_store.clear()
        secret = "test-secret-key"
        signature = _sign(VALID_PAYLOAD, secret)

        with patch.dict(os.environ, {"WEBHOOK_SECRET": secret}):
            request = _make_request(
                "POST",
                "http://localhost/api/webhooks/inbound",
                body=VALID_PAYLOAD,
                headers={
                    "Content-Type": "application/json",
                    "X-Signature": signature,
                },
            )
            response = receive_webhook(request)

        assert response.status_code == 202

    def test_returns_503_when_secret_is_not_configured(self) -> None:
        webhook_store.clear()

        with patch.dict(os.environ, {}, clear=True):
            request = _make_request(
                "POST",
                "http://localhost/api/webhooks/inbound",
                body=VALID_PAYLOAD,
                headers={"Content-Type": "application/json"},
            )
            response = receive_webhook(request)

        assert response.status_code == 503
        body = json.loads(response.get_body())
        assert body["error"] == "Webhook signing secret not configured"


    def test_returns_401_before_422_when_secret_set(self) -> None:
        """Signature check must reject before Pydantic validation runs."""
        webhook_store.clear()
        invalid_payload = json.dumps({"data": {}}).encode()  # missing required fields

        with patch.dict(os.environ, {"WEBHOOK_SECRET": "test-secret-key"}):
            request = _make_request(
                "POST",
                "http://localhost/api/webhooks/inbound",
                body=invalid_payload,
                headers={
                    "Content-Type": "application/json",
                    "X-Signature": "sha256=invalid",
                },
            )
            response = receive_webhook(request)

        assert response.status_code == 401  # auth failure, not 422

    def test_accepts_valid_payload_with_pydantic_model(self) -> None:
        """Valid signed payload returns 202 with Pydantic-serialized response."""
        webhook_store.clear()
        secret = "test-secret-key"
        signature = _sign(VALID_PAYLOAD, secret)

        with patch.dict(os.environ, {"WEBHOOK_SECRET": secret}):
            request = _make_request(
                "POST",
                "http://localhost/api/webhooks/inbound",
                body=VALID_PAYLOAD,
                headers={
                    "Content-Type": "application/json",
                    "X-Signature": signature,
                },
            )
            response = receive_webhook(request)

        assert response.status_code == 202
        body = json.loads(response.get_body())
        assert body["status"] == "accepted"
        assert body["delivery_id"].startswith("dlv_")

