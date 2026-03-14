from __future__ import annotations

import json

import azure.functions as func

from app.services.user_service import create_user, get_user, list_users

users_blueprint = func.Blueprint()


@users_blueprint.route(route="users", methods=["GET"])
def list_users_route(req: func.HttpRequest) -> func.HttpResponse:
    del req
    payload = json.dumps({"users": list_users()})
    return func.HttpResponse(body=payload, mimetype="application/json", status_code=200)


@users_blueprint.route(route="users/{id}", methods=["GET"])
def get_user_route(req: func.HttpRequest) -> func.HttpResponse:
    user_id = req.route_params.get("id", "")
    user = get_user(user_id)
    if user is None:
        return func.HttpResponse(
            body='{"error": "user not found"}',
            mimetype="application/json",
            status_code=404,
        )

    return func.HttpResponse(body=json.dumps(user), mimetype="application/json", status_code=200)


@users_blueprint.route(route="users", methods=["POST"])
def create_user_route(req: func.HttpRequest) -> func.HttpResponse:
    try:
        payload = req.get_json()
    except ValueError:
        return func.HttpResponse(
            body='{"error": "invalid json"}',
            mimetype="application/json",
            status_code=400,
        )

    user_id = str(payload.get("id", "")).strip()
    name = str(payload.get("name", "")).strip()
    if not user_id or not name:
        return func.HttpResponse(
            body='{"error": "fields id and name are required"}',
            mimetype="application/json",
            status_code=400,
        )

    user = create_user(user_id=user_id, name=name)
    return func.HttpResponse(body=json.dumps(user), mimetype="application/json", status_code=201)
