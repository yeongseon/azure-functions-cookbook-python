"""HTTP routing example with route params, query strings, and JSON request bodies."""

from __future__ import annotations

import json
from typing import Any

import azure.functions as func

app = func.FunctionApp()

USERS: dict[str, dict[str, str]] = {
    "1": {"id": "1", "name": "Ada Lovelace", "email": "ada@example.com"},
    "2": {"id": "2", "name": "Grace Hopper", "email": "grace@example.com"},
}


def _json_response(body: object, status_code: int = 200) -> func.HttpResponse:
    """Return a JSON HTTP response with the provided body and status code."""
    return func.HttpResponse(
        json.dumps(body),
        status_code=status_code,
        mimetype="application/json",
    )


def _parse_json_body(req: func.HttpRequest) -> dict[str, Any] | None:
    """Parse a JSON request body and return `None` when parsing fails."""
    try:
        payload = req.get_json()
    except ValueError:
        return None
    return payload if isinstance(payload, dict) else None


@app.route(route="users", methods=["GET"], auth_level=func.AuthLevel.ANONYMOUS)
def list_users(req: func.HttpRequest) -> func.HttpResponse:
    """List all users from the in-memory user store."""
    del req
    return _json_response({"users": list(USERS.values())})


@app.route(route="users/{user_id}", methods=["GET"], auth_level=func.AuthLevel.ANONYMOUS)
def get_user(req: func.HttpRequest) -> func.HttpResponse:
    """Return one user by the `user_id` route parameter."""
    user_id = req.route_params.get("user_id", "")
    user = USERS.get(user_id)
    if user is None:
        return _json_response({"error": f"User '{user_id}' not found."}, status_code=404)
    return _json_response(user)


@app.route(route="users", methods=["POST"], auth_level=func.AuthLevel.ANONYMOUS)
def create_user(req: func.HttpRequest) -> func.HttpResponse:
    """Create a user from JSON request body and return HTTP 201."""
    payload = _parse_json_body(req)
    if payload is None:
        return _json_response({"error": "Request body must be a JSON object."}, status_code=400)

    name = str(payload.get("name", "")).strip()
    email = str(payload.get("email", "")).strip()
    if not name or not email:
        return _json_response(
            {"error": "Fields 'name' and 'email' are required."},
            status_code=400,
        )

    requested_id = str(payload.get("id", "")).strip()
    user_id = requested_id or str(len(USERS) + 1)
    if user_id in USERS:
        return _json_response({"error": f"User '{user_id}' already exists."}, status_code=409)

    user = {"id": user_id, "name": name, "email": email}
    USERS[user_id] = user
    return _json_response(user, status_code=201)


@app.route(route="users/{user_id}", methods=["PUT"], auth_level=func.AuthLevel.ANONYMOUS)
def update_user(req: func.HttpRequest) -> func.HttpResponse:
    """Update an existing user by `user_id` and return HTTP 200 or 404."""
    user_id = req.route_params.get("user_id", "")
    existing = USERS.get(user_id)
    if existing is None:
        return _json_response({"error": f"User '{user_id}' not found."}, status_code=404)

    payload = _parse_json_body(req)
    if payload is None:
        return _json_response({"error": "Request body must be a JSON object."}, status_code=400)

    name = str(payload.get("name", existing["name"]))
    email = str(payload.get("email", existing["email"]))
    USERS[user_id] = {"id": user_id, "name": name, "email": email}
    return _json_response(USERS[user_id], status_code=200)


@app.route(route="users/{user_id}", methods=["DELETE"], auth_level=func.AuthLevel.ANONYMOUS)
def delete_user(req: func.HttpRequest) -> func.HttpResponse:
    """Delete a user by `user_id` and return HTTP 204."""
    user_id = req.route_params.get("user_id", "")
    if user_id not in USERS:
        return _json_response({"error": f"User '{user_id}' not found."}, status_code=404)

    del USERS[user_id]
    return func.HttpResponse(status_code=204)


@app.route(route="search", methods=["GET"], auth_level=func.AuthLevel.ANONYMOUS)
def search_users(req: func.HttpRequest) -> func.HttpResponse:
    """Search users by `q` query parameter and optional `limit`."""
    query = req.params.get("q", "").strip().lower()

    limit_raw = req.params.get("limit", "10")
    try:
        limit = max(1, int(limit_raw))
    except ValueError:
        return _json_response(
            {"error": "Query parameter 'limit' must be an integer."}, status_code=400
        )

    matched = [
        user
        for user in USERS.values()
        if query in user["name"].lower() or query in user["email"].lower()
    ]
    return _json_response({"q": query, "limit": limit, "results": matched[:limit]})
