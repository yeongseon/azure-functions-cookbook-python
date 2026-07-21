from __future__ import annotations

import json
import os
from typing import Any

import azure.functions as func

try:
    from pydantic import BaseModel, Field
except ImportError:

    class BaseModel:
        def __init__(self, **kwargs: object) -> None:
            for key, value in kwargs.items():
                setattr(self, key, value)

        def model_dump(self) -> dict[str, object]:
            return self.__dict__.copy()

    def Field(default: object = None, **_: object) -> object:
        return default


from azure_functions_logging import get_logger, setup_logging, with_context
from azure_functions_openapi import openapi
from azure_functions_validation import validate_http

setup_logging(format="json")
logger = get_logger(__name__)
app = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)


class PublishRequest(BaseModel):
    user_id: str = Field(..., description="Connected user identifier")
    room: str = Field(..., description="Target group or room")
    message: str = Field(..., description="Payload to fan out")


def _build_webpubsub_client() -> Any:
    from azure.messaging.webpubsubservice import WebPubSubServiceClient

    connection_string = os.environ["WebPubSubConnectionString"]
    hub_name = os.getenv("WEBPUBSUB_HUB_NAME", "realtime-proxy")
    return WebPubSubServiceClient.from_connection_string(connection_string, hub=hub_name)


@app.route(route="websocket/negotiate", methods=["POST"])
@with_context
def negotiate(req: func.HttpRequest) -> func.HttpResponse:
    user_id = req.headers.get("x-user-id", "local-user")
    client = _build_webpubsub_client()
    token = client.get_client_access_token(
        user_id=user_id, roles=["webpubsub.joinLeaveGroup", "webpubsub.sendToGroup"]
    )
    logger.info("Issued Web PubSub access token", extra={"user_id": user_id})
    return func.HttpResponse(body=json.dumps(token), mimetype="application/json")


@app.route(route="websocket/publish", methods=["POST"])
@with_context
@openapi(
    summary="Publish Web PubSub message",
    tags=["Realtime"],
    route="/api/websocket/publish",
    method="post",
)
@validate_http(body=PublishRequest)
def publish(req: func.HttpRequest, body: PublishRequest) -> func.HttpResponse:
    client = _build_webpubsub_client()
    client.send_to_group(group=body.room, message=body.message, content_type="text/plain")
    logger.info("Forwarded WebSocket message through Web PubSub", extra=body.model_dump())
    return func.HttpResponse(
        body=json.dumps({"status": "published", **body.model_dump()}), mimetype="application/json"
    )


@app.route(route="websocket/events", methods=["POST", "OPTIONS"])
@with_context
def handle_event(req: func.HttpRequest) -> func.HttpResponse:
    event_type = req.headers.get("ce-type", req.headers.get("WebHook-Request-Origin", "unknown"))
    logger.info("Received Web PubSub upstream callback", extra={"event_type": event_type})
    if req.method == "OPTIONS":
        return func.HttpResponse(status_code=204, headers={"WebHook-Allowed-Origin": "*"})
    return func.HttpResponse(
        body=json.dumps({"handled": True, "event_type": event_type}), mimetype="application/json"
    )
