from __future__ import annotations

import logging
import os

import azure.functions as func

from app.services.webhook_service import _is_signature_valid, _json_response, dispatch_event

webhook_blueprint = func.Blueprint()


@webhook_blueprint.route(
    route="github/webhook", methods=["POST"], auth_level=func.AuthLevel.ANONYMOUS
)
def github_webhook(req: func.HttpRequest) -> func.HttpResponse:
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
    body, status_code = dispatch_event(event_type, payload)
    return _json_response(body, status_code=status_code)
