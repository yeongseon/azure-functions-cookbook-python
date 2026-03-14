from __future__ import annotations

from typing import Any


def process_task(task: dict[str, Any]) -> str:
    task_type = str(task.get("task_type", "unknown"))
    details = task.get("payload", {})
    return f"Task '{task_type}' completed with payload keys: {sorted(details.keys())}"
