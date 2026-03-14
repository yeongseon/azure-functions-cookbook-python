from __future__ import annotations

import json
import logging
from typing import Any

import azure.functions as func

from app.services.task_service import process_task

worker_blueprint = func.Blueprint()
logger = logging.getLogger(__name__)


@worker_blueprint.queue_trigger(
    arg_name="msg",
    queue_name="outbound-tasks",
    connection="AzureWebJobsStorage",
)
def process_queue_message(msg: func.QueueMessage) -> None:
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

    outcome = process_task(payload)
    logger.info("Queue message %s processed: %s", message_id, outcome)
