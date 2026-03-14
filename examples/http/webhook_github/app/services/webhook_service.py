from __future__ import annotations

import hashlib
import hmac
import json
from typing import Any

import azure.functions as func


def _json_response(body: object, status_code: int = 200) -> func.HttpResponse:
    return func.HttpResponse(
        body=json.dumps(body),
        status_code=status_code,
        mimetype="application/json",
    )


def _is_signature_valid(signature_header: str | None, payload: bytes, secret: str) -> bool:
    if not signature_header or not signature_header.startswith("sha256="):
        return False

    expected = (
        "sha256="
        + hmac.new(
            key=secret.encode("utf-8"),
            msg=payload,
            digestmod=hashlib.sha256,
        ).hexdigest()
    )
    return hmac.compare_digest(expected, signature_header)


def _handle_push(payload: dict[str, Any]) -> dict[str, object]:
    repository = payload.get("repository", {})
    repo_name = str(repository.get("full_name", "unknown"))
    ref = str(payload.get("ref", "unknown"))
    commit_count = len(payload.get("commits", []))
    return {
        "event": "push",
        "repository": repo_name,
        "ref": ref,
        "commits": commit_count,
        "message": f"Processed push with {commit_count} commit(s).",
    }


def _handle_pull_request(payload: dict[str, Any]) -> dict[str, object]:
    action = str(payload.get("action", "unknown"))
    pull_request = payload.get("pull_request", {})
    number = pull_request.get("number", payload.get("number", "unknown"))
    title = str(pull_request.get("title", ""))
    return {
        "event": "pull_request",
        "action": action,
        "number": number,
        "title": title,
        "message": f"Processed pull request #{number} ({action}).",
    }


def _handle_issues(payload: dict[str, Any]) -> dict[str, object]:
    action = str(payload.get("action", "unknown"))
    issue = payload.get("issue", {})
    number = issue.get("number", payload.get("number", "unknown"))
    title = str(issue.get("title", ""))
    return {
        "event": "issues",
        "action": action,
        "number": number,
        "title": title,
        "message": f"Processed issue #{number} ({action}).",
    }


def dispatch_event(event_type: str, payload: dict[str, Any]) -> tuple[dict[str, object], int]:
    if event_type == "push":
        return _handle_push(payload), 200
    if event_type == "pull_request":
        return _handle_pull_request(payload), 200
    if event_type == "issues":
        return _handle_issues(payload), 200
    return {
        "event": event_type,
        "message": "Event received but no specialized handler is defined.",
    }, 200
