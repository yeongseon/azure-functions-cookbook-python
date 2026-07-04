from __future__ import annotations

import hashlib
import hmac
import logging
import os
import uuid
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


def _generate_delivery_id() -> str:
    """Generate a unique delivery identifier."""
    return f"dlv_{uuid.uuid4().hex[:12]}"


def verify_signature(payload: bytes, signature: str, secret: str) -> bool:
    """Verify HMAC-SHA256 signature.

    Parameters:
        payload: Raw request body bytes.
        signature: Value of the ``X-Signature`` header (``sha256=<hex>``).
        secret: The shared webhook secret.

    Returns:
        ``True`` when the signature is valid.
    """
    if not signature.startswith("sha256="):
        return False
    expected = hmac.new(
        secret.encode(), payload, hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(signature.removeprefix("sha256="), expected)


class WebhookStore:
    """In-memory recent-delivery store for local development.

    Not intended for production use — replace with a durable queue or
    database in real deployments.
    """

    _MAX_ENTRIES = 100

    def __init__(self) -> None:
        self._deliveries: dict[str, dict[str, str]] = {}

    def record(self, event_type: str, source: str) -> dict[str, str]:
        """Record an accepted webhook delivery and return its metadata."""
        delivery_id = _generate_delivery_id()
        received_at = datetime.now(timezone.utc).isoformat()  # noqa: UP017
        entry = {
            "delivery_id": delivery_id,
            "status": "accepted",
            "received_at": received_at,
        }
        self._deliveries[delivery_id] = entry
        # Evict oldest entries when limit exceeded
        while len(self._deliveries) > self._MAX_ENTRIES:
            oldest_key = next(iter(self._deliveries))
            del self._deliveries[oldest_key]
        logger.info(
            "Webhook accepted: delivery_id=%s event_type=%s source=%s",
            delivery_id,
            event_type,
            source,
        )
        return entry

    def get(self, delivery_id: str) -> dict[str, str] | None:
        return self._deliveries.get(delivery_id)

    def list_recent(self) -> list[dict[str, str]]:
        return list(self._deliveries.values())

    def clear(self) -> None:
        self._deliveries.clear()


def get_webhook_secret() -> str:
    """Return the webhook secret from environment."""
    secret = os.environ.get("WEBHOOK_SECRET", "")
    if not secret:
        raise RuntimeError("WEBHOOK_SECRET is not configured")
    return secret


webhook_store = WebhookStore()
