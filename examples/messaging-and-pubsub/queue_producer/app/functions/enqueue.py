from __future__ import annotations

import json
import logging
from typing import Any
from uuid import uuid4

import azure.functions as func

from app.services.enqueue_service import build_queue_message, validate_payload

enqueue_blueprint = func.Blueprint()
logger = logging.getLogger(__name__)


@enqueue_blueprint.route(route="enqueue", methods=["POST"], auth_level=func.AuthLevel.ANONYMOUS)
@enqueue_blueprint.queue_output(
    arg_name="msg",
    queue_name="outbound-tasks",
    connection="AzureWebJobsStorage",
)
def enqueue_task(req: func.HttpRequest, msg: func.Out[str]) -> func.HttpResponse:
    try:
        payload: dict[str, Any] = req.get_json()
    except ValueError:
        return _json_response(
            {"error": "Request body must be valid JSON."},
            status_code=400,
        )

    is_valid, error_message = validate_payload(payload)
    if not is_valid:
        return _json_response({"error": error_message}, status_code=400)

    message_id = str(uuid4())
    queue_message = build_queue_message(payload, message_id)
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


def _json_response(data: dict[str, Any], status_code: int) -> func.HttpResponse:
    return func.HttpResponse(
        body=json.dumps(data),
        status_code=status_code,
        mimetype="application/json",
    )
