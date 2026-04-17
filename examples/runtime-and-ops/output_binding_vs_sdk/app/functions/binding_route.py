from __future__ import annotations

import json

import azure.functions as func

from app.services.payload_service import build_payload

binding_blueprint = func.Blueprint()


@binding_blueprint.function_name(name="enqueue_via_binding")
@binding_blueprint.route(route="enqueue/binding", methods=["POST"])
@binding_blueprint.queue_output(
    arg_name="output_message",
    queue_name="work-items",
    connection="StorageConnection",
)
def enqueue_via_binding(
    req: func.HttpRequest,
    output_message: func.Out[str],
) -> func.HttpResponse:
    payload = build_payload(req)
    payload["method"] = "binding"
    output_message.set(json.dumps(payload))
    return func.HttpResponse(
        body=json.dumps(payload),
        mimetype="application/json",
        status_code=200,
    )
