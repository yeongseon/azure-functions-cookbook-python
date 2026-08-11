from __future__ import annotations

import json
import logging

import azure.functions as func
from azure_functions_openapi.decorator import openapi
from pydantic import ValidationError

from app.schemas.webhooks import WebhookAcceptedResponse, WebhookEvent
from app.services.webhook_service import get_webhook_secret, verify_signature, webhook_store

webhooks_blueprint = func.Blueprint()  # type: ignore[no-untyped-call]


# ---------------------------------------------------------------------------
# POST /api/webhooks/inbound — receive inbound webhook events
# ---------------------------------------------------------------------------

@webhooks_blueprint.route(
    route="webhooks/inbound",
    methods=["POST"],
    auth_level=func.AuthLevel.FUNCTION,
)
@openapi(
    summary="Receive inbound webhook",
    description=(
        "Accepts a webhook event for asynchronous processing. "
        "Returns 202 when the delivery is accepted."
    ),
    tags=["webhooks"],
    requests=WebhookEvent,
    responses={
        202: WebhookAcceptedResponse,
        400: {"description": "Invalid request payload"},
        401: {"description": "Invalid webhook signature"},
        422: {"description": "Request validation error"},
    },
)
def receive_webhook(req: func.HttpRequest) -> func.HttpResponse:
    # --- Signature verification (must run before body parsing) ---
    try:
        secret = get_webhook_secret()
    except RuntimeError:
        return func.HttpResponse(
            body=json.dumps({"error": "Webhook signing secret not configured"}),
            mimetype="application/json",
            status_code=503,
        )

    signature = req.headers.get("X-Signature", "")
    if not verify_signature(req.get_body(), signature, secret):
        logging.warning("Webhook signature verification failed")
        return func.HttpResponse(
            body=json.dumps({"error": "Invalid signature"}),
            mimetype="application/json",
            status_code=401,
        )
    # --- Body validation (after auth) ---
    try:
        raw = req.get_json()
    except ValueError:
        return func.HttpResponse(
            body=json.dumps({"error": "Invalid JSON body"}),
            mimetype="application/json",
            status_code=400,
        )

    try:
        event = WebhookEvent(**raw) if isinstance(raw, dict) else WebhookEvent.model_validate(raw)
    except (ValidationError, TypeError) as exc:
        return func.HttpResponse(
            body=json.dumps({"error": "Validation error", "detail": str(exc)}),
            mimetype="application/json",
            status_code=422,
        )

    event_type = event.event_type
    source = event.source
    logging.info("Received webhook: event_type=%s source=%s", event_type, source)

    entry = webhook_store.record(event_type, source)
    return func.HttpResponse(
        body=WebhookAcceptedResponse(**entry).model_dump_json(),
        mimetype="application/json",
        status_code=202,
    )
