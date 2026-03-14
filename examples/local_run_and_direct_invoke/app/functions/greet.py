from __future__ import annotations

import json

import azure.functions as func

from app.services.greet_service import build_greeting, extract_name

greet_blueprint = func.Blueprint()


@greet_blueprint.route(route="greet", methods=["GET", "POST"], auth_level=func.AuthLevel.ANONYMOUS)
def greet(req: func.HttpRequest) -> func.HttpResponse:
    name = extract_name(
        params=req.params,
        body=req.get_body(),
        content_type=req.headers.get("Content-Type", ""),
    )
    if not name:
        return func.HttpResponse(
            json.dumps({"error": "Please provide a 'name' query param or JSON body."}),
            mimetype="application/json",
            status_code=400,
        )

    return func.HttpResponse(
        json.dumps(build_greeting(name)),
        mimetype="application/json",
        status_code=200,
    )
