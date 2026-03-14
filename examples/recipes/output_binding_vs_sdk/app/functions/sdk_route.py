from __future__ import annotations

import json
import os
from typing import Any

import azure.functions as func

from app.services.payload_service import build_payload

sdk_blueprint = func.Blueprint()


@sdk_blueprint.function_name(name="enqueue_via_sdk")
@sdk_blueprint.route(route="enqueue/sdk", methods=["POST"])
def enqueue_via_sdk(req: func.HttpRequest) -> func.HttpResponse:
    payload = build_payload(req)
    payload["method"] = "sdk"

    connection_string = os.getenv("StorageConnection", "")
    if not connection_string:
        return func.HttpResponse(
            body='{"error": "StorageConnection app setting is required"}',
            mimetype="application/json",
            status_code=500,
        )

    queue_client_module = __import__("azure.storage.queue", fromlist=["QueueClient"])
    queue_client_class: Any = getattr(queue_client_module, "QueueClient")
    client = queue_client_class.from_connection_string(
        conn_str=connection_string,
        queue_name="work-items",
    )
    client.send_message(json.dumps(payload))

    return func.HttpResponse(
        body=json.dumps(payload),
        mimetype="application/json",
        status_code=202,
    )
