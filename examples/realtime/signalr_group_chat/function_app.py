from __future__ import annotations

import json
import os
from typing import TypeVar

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


try:
    from azure_functions_logging import get_logger, setup_logging, with_context
except ImportError:
    import logging

    def setup_logging(*_: object, **__: object) -> None:
        logging.basicConfig(level=logging.INFO)

    def get_logger(name: str) -> logging.Logger:
        return logging.getLogger(name)

    def with_context(function):
        return function


try:
    from azure_functions_openapi.decorator import openapi
except ImportError:

    def openapi(*_: object, **__: object):
        def decorator(function):
            return function

        return decorator


try:
    from azure_functions_validation import validate_http
except ImportError:

    def validate_http(*_: object, **__: object):
        def decorator(function):
            return function

        return decorator


setup_logging(format="json")
logger = get_logger(__name__)
app = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)
F = TypeVar("F")
HUB_NAME = os.getenv("SIGNALR_HUB_NAME", "groupchat")


class JoinRoomRequest(BaseModel):
    room: str = Field(..., description="Chat room name")
    user_id: str = Field(..., description="User identifier")


class SendMessageRequest(BaseModel):
    room: str
    user_id: str
    message: str


@app.route(route="chat/negotiate", methods=["POST"])
@app.signalr_connection_info_input(
    arg_name="connection_info",
    hub_name=HUB_NAME,
    connection_string_setting="AzureSignalRConnectionString",
    user_id="chat-user",
)
@with_context
def negotiate(req: func.HttpRequest, connection_info: str) -> func.HttpResponse:
    logger.info("Negotiated SignalR chat connection", extra={"hub": HUB_NAME})
    return func.HttpResponse(connection_info, mimetype="application/json")


@app.route(route="chat/join", methods=["POST"])
@with_context
@openapi(summary="Join SignalR group", tags=["Realtime"], route="/api/chat/join", method="post")
@app.signalr_output(
    arg_name="signalr",
    hub_name=HUB_NAME,
    connection_string_setting="AzureSignalRConnectionString",
)
@validate_http(body=JoinRoomRequest)
def join_room(
    req: func.HttpRequest, body: JoinRoomRequest, signalr: func.Out[str]
) -> func.HttpResponse:
    signalr.set(
        json.dumps(
            {
                "action": "add",
                "userId": body.user_id,
                "groupName": body.room,
            }
        )
    )
    logger.info("Added user to SignalR room", extra=body.model_dump())
    return func.HttpResponse(
        json.dumps({"status": "joined", **body.model_dump()}), mimetype="application/json"
    )


@app.route(route="chat/message", methods=["POST"])
@with_context
@openapi(
    summary="Broadcast SignalR group message",
    tags=["Realtime"],
    route="/api/chat/message",
    method="post",
)
@app.signalr_output(
    arg_name="signalr",
    hub_name=HUB_NAME,
    connection_string_setting="AzureSignalRConnectionString",
)
@validate_http(body=SendMessageRequest)
def send_message(
    req: func.HttpRequest, body: SendMessageRequest, signalr: func.Out[str]
) -> func.HttpResponse:
    signalr.set(
        json.dumps(
            {
                "target": "newMessage",
                "groupName": body.room,
                "arguments": [body.model_dump()],
            }
        )
    )
    logger.info("Published SignalR room message", extra=body.model_dump())
    return func.HttpResponse(
        json.dumps({"status": "sent", **body.model_dump()}), mimetype="application/json"
    )
