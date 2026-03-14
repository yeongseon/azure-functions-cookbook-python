from __future__ import annotations

from typing import Any

_users: dict[str, dict[str, Any]] = {}


def list_users() -> list[dict[str, Any]]:
    return list(_users.values())


def get_user(user_id: str) -> dict[str, Any] | None:
    return _users.get(user_id)


def create_user(user_id: str, name: str) -> dict[str, str]:
    user = {"id": user_id, "name": name}
    _users[user_id] = user
    return user
