"""GitHub webhook receiver with HMAC-SHA256 signature verification."""

from __future__ import annotations

import hashlib
import hmac
import json
import logging
import os
from typing import Any

import azure.functions as func

app = func.FunctionApp()


def _json_response(body: object, status_code: int = 200) -> func.HttpResponse:
    """Return a JSON response payload."""
    return func.HttpResponse(
        body=json.dumps(body),
        status_code=status_code,
        mimetype="application/json",
    )


def _is_signature_valid(signature_header: str | None, payload: bytes, secret: str) -> bool:
    """Validate `X-Hub-Signature-256` header against payload and shared secret."""
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
    """Build response for a GitHub `push` event."""
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
    """Build response for a GitHub `pull_request` event."""
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
    """Build response for a GitHub `issues` event."""
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


@app.route(route="github/webhook", methods=["POST"], auth_level=func.AuthLevel.ANONYMOUS)
def github_webhook(req: func.HttpRequest) -> func.HttpResponse:
    """Handle GitHub webhook events with signature verification and event dispatch."""
    secret = os.environ.get("GITHUB_WEBHOOK_SECRET", "")
    if not secret:
        logging.error("Missing GITHUB_WEBHOOK_SECRET environment variable.")
        return _json_response(
            {"error": "Server is not configured with GITHUB_WEBHOOK_SECRET."},
            status_code=500,
        )

    signature = req.headers.get("X-Hub-Signature-256")
    raw_body = req.get_body()
    if not _is_signature_valid(signature, raw_body, secret):
        logging.warning("Rejected webhook request due to invalid signature.")
        return _json_response({"error": "Invalid or missing webhook signature."}, status_code=401)

    event_type = req.headers.get("X-GitHub-Event", "")
    try:
        payload = req.get_json()
    except ValueError:
        logging.warning("Rejected webhook request due to invalid JSON payload.")
        return _json_response({"error": "Request body must be valid JSON."}, status_code=400)

    if not isinstance(payload, dict):
        return _json_response({"error": "Webhook payload must be a JSON object."}, status_code=400)

    logging.info("Processing GitHub event: %s", event_type)
    if event_type == "push":
        return _json_response(_handle_push(payload), status_code=200)
    if event_type == "pull_request":
        return _json_response(_handle_pull_request(payload), status_code=200)
    if event_type == "issues":
        return _json_response(_handle_issues(payload), status_code=200)

    return _json_response(
        {
            "event": event_type,
            "message": "Event received but no specialized handler is defined.",
        },
        status_code=200,
    )
