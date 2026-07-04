from __future__ import annotations

import json
import logging

import azure.functions as func
from azure_functions_openapi.decorator import openapi

from app.services.health_service import check_health

health_blueprint = func.Blueprint()  # type: ignore[no-untyped-call]


@health_blueprint.route(
    route="health",
    methods=["GET"],
    auth_level=func.AuthLevel.ANONYMOUS,
    )
@openapi(
    summary="Health check",
    description="Returns the current health status of the application.",
    tags=["health"],
    )
def health(req: func.HttpRequest) -> func.HttpResponse:
    logging.info("Health check requested")
    result = check_health()
    return func.HttpResponse(
        body=json.dumps(result),
        mimetype="application/json",
        status_code=200,
    )
