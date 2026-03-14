"""Queue-triggered worker that parses and processes outbound task messages."""

from __future__ import annotations

import json
import logging
from typing import Any

import azure.functions as func

app = func.FunctionApp()
logger = logging.getLogger(__name__)


@app.queue_trigger(
    arg_name="msg",
    queue_name="outbound-tasks",
    connection="AzureWebJobsStorage",
)
def process_queue_message(msg: func.QueueMessage) -> None:
    """Parse queue payload, log retry context, and dispatch task processing."""
    message_text = msg.get_body().decode("utf-8", errors="replace")
    dequeue_count = int(getattr(msg, "dequeue_count", 1))
    message_id = getattr(msg, "id", "unknown")

    try:
        payload: dict[str, Any] = json.loads(message_text)
    except json.JSONDecodeError:
        logger.error(
            "Invalid JSON in message %s (dequeue_count=%d): %s",
            message_id,
            dequeue_count,
            message_text,
        )
        return

    logger.info(
        "Processing queue message id=%s dequeue_count=%d task_type=%s",
        message_id,
        dequeue_count,
        payload.get("task_type", "unknown"),
    )

    outcome = _process_task(payload)
    logger.info("Queue message %s processed: %s", message_id, outcome)


def _process_task(task: dict[str, Any]) -> str:
    """Simulate task processing and return an execution summary."""
    task_type = str(task.get("task_type", "unknown"))
    details = task.get("payload", {})
    return f"Task '{task_type}' completed with payload keys: {sorted(details.keys())}"
