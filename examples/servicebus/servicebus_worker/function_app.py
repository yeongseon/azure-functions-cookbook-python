"""Service Bus queue trigger for resilient background task processing."""

from __future__ import annotations

import json
import logging
from typing import Any

import azure.functions as func

app = func.FunctionApp()
logger = logging.getLogger(__name__)


@app.service_bus_queue_trigger(
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
    outcome = _process_service_bus_message(payload)
    logger.info("Service Bus processing complete: %s", outcome)


def _process_service_bus_message(payload: dict[str, Any]) -> str:
    """Simulate Service Bus business processing for a task payload."""
    task_name = str(payload.get("task", "unknown"))
    priority = str(payload.get("priority", "normal"))
    return f"task={task_name} priority={priority} status=processed"
