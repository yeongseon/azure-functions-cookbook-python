from __future__ import annotations

import json
import logging
from typing import Any

import azure.functions as func

from app.services.servicebus_service import process_message

servicebus_blueprint = func.Blueprint()
logger = logging.getLogger(__name__)


@servicebus_blueprint.service_bus_queue_trigger(
    arg_name="msg",
    queue_name="tasks",
    connection="ServiceBusConnection",
)
def process_service_bus_message(msg: func.ServiceBusMessage) -> None:
    """Process a Service Bus message and track delivery metadata.

    In production, handle poison messages by moving them to the dead-letter queue
    after max delivery attempts, then inspect and replay after remediation.
    """
    raw_body = msg.get_body().decode("utf-8", errors="replace")
    correlation_id = getattr(msg, "correlation_id", None)
    delivery_count = int(getattr(msg, "delivery_count", 1))

    try:
        payload: dict[str, Any] = json.loads(raw_body)
    except json.JSONDecodeError:
        logger.error(
            "Invalid Service Bus JSON (correlation_id=%s delivery_count=%d): %s",
            correlation_id,
            delivery_count,
            raw_body,
        )
        return

    logger.info(
        "Service Bus message received correlation_id=%s delivery_count=%d",
        correlation_id,
        delivery_count,
    )
    outcome = process_message(payload)
    logger.info("Service Bus processing complete: %s", outcome)
