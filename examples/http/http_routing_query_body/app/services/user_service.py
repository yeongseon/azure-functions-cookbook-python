from __future__ import annotations

import json
from typing import Any

import azure.functions as func

USERS: dict[str, dict[str, str]] = {
    "1": {"id": "1", "name": "Ada Lovelace", "email": "ada@example.com"},
    "2": {"id": "2", "name": "Grace Hopper", "email": "grace@example.com"},
}


def _json_response(body: object, status_code: int = 200) -> func.HttpResponse:
    return func.HttpResponse(
        json.dumps(body),
        status_code=status_code,
        mimetype="application/json",
    )


def _parse_json_body(req: func.HttpRequest) -> dict[str, Any] | None:
    try:
        payload = req.get_json()
    except ValueError:
        return None
    return payload if isinstance(payload, dict) else None


def list_all_users() -> dict[str, list[dict[str, str]]]:
    return {"users": list(USERS.values())}


def get_user_by_id(user_id: str) -> dict[str, str] | None:
    return USERS.get(user_id)


def create_user(payload: dict[str, Any]) -> tuple[dict[str, str], int]:
    name = str(payload.get("name", "")).strip()
    email = str(payload.get("email", "")).strip()
    if not name or not email:
        return {"error": "Fields 'name' and 'email' are required."}, 400

    requested_id = str(payload.get("id", "")).strip()
    user_id = requested_id or str(len(USERS) + 1)
    if user_id in USERS:
        return {"error": f"User '{user_id}' already exists."}, 409

    user = {"id": user_id, "name": name, "email": email}
    USERS[user_id] = user
    return user, 201


def update_user(user_id: str, payload: dict[str, Any]) -> tuple[dict[str, str], int]:
    existing = USERS.get(user_id)
    if existing is None:
        return {"error": f"User '{user_id}' not found."}, 404

    name = str(payload.get("name", existing["name"]))
    email = str(payload.get("email", existing["email"]))
    USERS[user_id] = {"id": user_id, "name": name, "email": email}
    return USERS[user_id], 200


def delete_user(user_id: str) -> tuple[dict[str, str], int]:
    if user_id not in USERS:
        return {"error": f"User '{user_id}' not found."}, 404

    del USERS[user_id]
    return {}, 204


def search_users(query: str, limit: int) -> dict[str, object]:
    matched = [
        user
        for user in USERS.values()
        if query in user["name"].lower() or query in user["email"].lower()
    ]
    return {"q": query, "limit": limit, "results": matched[:limit]}
