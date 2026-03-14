"""Compare queue output binding with direct Azure Storage Queue SDK usage."""

from __future__ import annotations

import json
import os
from typing import Any

import azure.functions as func

app = func.FunctionApp()


def _build_payload(req: func.HttpRequest) -> dict[str, str]:
    """Build a queue payload from request body."""
    try:
        body = req.get_json()
    except ValueError:
        body = {}

    task = str(body.get("task", "demo-task")).strip() or "demo-task"
    return {"task": task, "source": "recipe"}


@app.function_name(name="enqueue_via_binding")
@app.route(route="enqueue/binding", methods=["POST"])
@app.queue_output(
    arg_name="output_message",
    queue_name="work-items",
    connection="StorageConnection",
)
def enqueue_via_binding(req: func.HttpRequest) -> str:
    """Send a queue message using an Azure Functions output binding."""
    payload = _build_payload(req)
    payload["method"] = "binding"
    return json.dumps(payload)


@app.function_name(name="enqueue_via_sdk")
@app.route(route="enqueue/sdk", methods=["POST"])
def enqueue_via_sdk(req: func.HttpRequest) -> func.HttpResponse:
    """Send a queue message using the Azure Storage Queue SDK."""
    payload = _build_payload(req)
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
