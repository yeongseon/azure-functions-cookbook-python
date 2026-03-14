"""User CRUD endpoints blueprint for modular function apps."""

from __future__ import annotations

import json
from typing import Any

import azure.functions as func

bp = func.Blueprint()
_users: dict[str, dict[str, Any]] = {}


@bp.route(route="users", methods=["GET"])
def list_users(req: func.HttpRequest) -> func.HttpResponse:
    """Return all users from the in-memory store."""
    del req
    payload = json.dumps({"users": list(_users.values())})
    return func.HttpResponse(body=payload, mimetype="application/json", status_code=200)


@bp.route(route="users/{id}", methods=["GET"])
def get_user(req: func.HttpRequest) -> func.HttpResponse:
    """Return a single user by id."""
    user_id = req.route_params.get("id", "")
    user = _users.get(user_id)
    if user is None:
        return func.HttpResponse(
            body='{"error": "user not found"}', mimetype="application/json", status_code=404
        )

    return func.HttpResponse(body=json.dumps(user), mimetype="application/json", status_code=200)


@bp.route(route="users", methods=["POST"])
def create_user(req: func.HttpRequest) -> func.HttpResponse:
    """Create a user in the in-memory store."""
    try:
        payload = req.get_json()
    except ValueError:
        return func.HttpResponse(
            body='{"error": "invalid json"}', mimetype="application/json", status_code=400
        )

    user_id = str(payload.get("id", "")).strip()
    name = str(payload.get("name", "")).strip()
    if not user_id or not name:
        return func.HttpResponse(
            body='{"error": "fields id and name are required"}',
            mimetype="application/json",
            status_code=400,
        )

    user = {"id": user_id, "name": name}
    _users[user_id] = user
    return func.HttpResponse(body=json.dumps(user), mimetype="application/json", status_code=201)
