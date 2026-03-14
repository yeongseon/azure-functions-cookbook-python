from __future__ import annotations

from typing import Any


def process_message(payload: dict[str, Any]) -> str:
    """Simulate Service Bus business processing for a task payload."""
    task_name = str(payload.get("task", "unknown"))
    priority = str(payload.get("priority", "normal"))
    return f"task={task_name} priority={priority} status=processed"
