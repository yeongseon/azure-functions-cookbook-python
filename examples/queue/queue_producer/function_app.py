"""HTTP trigger that validates and enqueues tasks to Azure Storage Queue."""

from __future__ import annotations

import json
import logging
from typing import Any
from uuid import uuid4

import azure.functions as func

app = func.FunctionApp()
logger = logging.getLogger(__name__)


@app.route(route="enqueue", methods=["POST"], auth_level=func.AuthLevel.ANONYMOUS)
@app.queue_output(
    arg_name="msg",
    queue_name="outbound-tasks",
    connection="AzureWebJobsStorage",
)
def enqueue_task(req: func.HttpRequest, msg: func.Out[str]) -> func.HttpResponse:
    """Accept task payloads and send validated messages to the queue."""
    try:
        payload: dict[str, Any] = req.get_json()
    except ValueError:
        return _json_response(
            {"error": "Request body must be valid JSON."},
            status_code=400,
        )

    is_valid, error_message = _validate_payload(payload)
    if not is_valid:
        return _json_response({"error": error_message}, status_code=400)

    message_id = str(uuid4())
    queue_message = {
        "message_id": message_id,
        "task_type": payload["task_type"],
        "payload": payload.get("payload", {}),
    }
    msg.set(json.dumps(queue_message))

    logger.info("Queued task %s of type %s", message_id, payload["task_type"])
    return _json_response(
        {
            "status": "accepted",
            "message_id": message_id,
            "queue": "outbound-tasks",
        },
        status_code=202,
    )


def _validate_payload(payload: dict[str, Any]) -> tuple[bool, str]:
    """Validate incoming enqueue payload shape and value types."""
    task_type = payload.get("task_type")
    if not isinstance(task_type, str) or not task_type.strip():
        return False, "Field 'task_type' is required and must be a non-empty string."

    task_payload = payload.get("payload", {})
    if not isinstance(task_payload, dict):
        return False, "Field 'payload' must be an object if provided."

    return True, ""


def _json_response(data: dict[str, Any], status_code: int) -> func.HttpResponse:
    """Create a JSON HTTP response with consistent content type."""
    return func.HttpResponse(
        body=json.dumps(data),
        status_code=status_code,
        mimetype="application/json",
    )
