from __future__ import annotations

from typing import Any


def validate_payload(payload: dict[str, Any]) -> tuple[bool, str]:
    task_type = payload.get("task_type")
    if not isinstance(task_type, str) or not task_type.strip():
        return False, "Field 'task_type' is required and must be a non-empty string."

    task_payload = payload.get("payload", {})
    if not isinstance(task_payload, dict):
        return False, "Field 'payload' must be an object if provided."

    return True, ""


def build_queue_message(payload: dict[str, Any], message_id: str) -> dict[str, Any]:
    return {
        "message_id": message_id,
        "task_type": payload["task_type"],
        "payload": payload.get("payload", {}),
    }
