from __future__ import annotations

import json

import azure.functions as func

from app.services.health_service import get_health_payload

health_blueprint = func.Blueprint()


@health_blueprint.route(route="health", methods=["GET"])
def get_health(req: func.HttpRequest) -> func.HttpResponse:
    del req
    return func.HttpResponse(
        body=json.dumps(get_health_payload()),
        mimetype="application/json",
        status_code=200,
    )
