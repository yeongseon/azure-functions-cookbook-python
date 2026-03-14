from __future__ import annotations

import azure.functions as func


def build_payload(req: func.HttpRequest) -> dict[str, str]:
    try:
        body = req.get_json()
    except ValueError:
        body = {}

    task = str(body.get("task", "demo-task")).strip() or "demo-task"
    return {"task": task, "source": "recipe"}
