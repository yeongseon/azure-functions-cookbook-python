# pyright: reportAny=false, reportExplicitAny=false

from __future__ import annotations

import importlib
import json
import logging
import os
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from typing import Any, Protocol, TypeVar, cast

F = TypeVar("F", bound=Callable[..., object])


class EventGridEventProtocol(Protocol):
    id: str
    event_type: str
    subject: str

    def get_json(self) -> object: ...


class HttpRequestProtocol(Protocol):
    headers: Mapping[str, str]


class HttpResponseProtocol(Protocol): ...


class AuthLevelProtocol:
    ANONYMOUS: str = "anonymous"


class FunctionAppProtocol(Protocol):
    def route(
        self, *, route: str, methods: list[str], auth_level: object | None = None
    ) -> Callable[[F], F]: ...

    def signalr_connection_info_input(
        self,
        *,
        arg_name: str,
        hub_name: str,
        connection_string_setting: str,
        user_id: str,
    ) -> Callable[[F], F]: ...

    def event_grid_trigger(self, *, arg_name: str) -> Callable[[F], F]: ...

    def signalr_output(
        self,
        *,
        arg_name: str,
        hub_name: str,
        connection_string_setting: str,
    ) -> Callable[[F], F]: ...


class LoggerProtocol(Protocol):
    def info(self, msg: object, *, extra: Mapping[str, object] | None = None) -> None: ...


class OutProtocol(Protocol):
    def set(self, value: str) -> None: ...


Decorator = Callable[[Callable[..., object]], Callable[..., object]]


def _passthrough(function: F) -> F:
    return function


def _fallback_setup_logging(*, format: str = "json") -> None:
    _ = format
    logging.basicConfig(level=logging.INFO)


def _fallback_get_logger(name: str) -> LoggerProtocol:
    return logging.getLogger(name)


try:
    func = cast(Any, importlib.import_module("azure.functions"))
except ImportError:

    @dataclass
    class _FallbackEventGridEvent:
        id: str = ""
        event_type: str = ""
        subject: str = ""

        def get_json(self) -> object:
            return {}

    @dataclass
    class _FallbackHttpRequest:
        headers: dict[str, str]

        def __init__(self, headers: dict[str, str] | None = None) -> None:
            self.headers = headers or {}

    class _FallbackHttpResponse:
        def __init__(
            self, body: str, *, mimetype: str = "text/plain", status_code: int = 200
        ) -> None:
            self.body: str = body
            self.mimetype: str = mimetype
            self.status_code: int = status_code

    class _FallbackOut:
        def set(self, value: str) -> None:
            _ = value

    class _FallbackFunctionApp:
        def route(
            self, *, route: str, methods: list[str], auth_level: object | None = None
        ) -> Callable[[F], F]:
            _ = (route, methods, auth_level)
            return _passthrough

        def signalr_connection_info_input(
            self,
            *,
            arg_name: str,
            hub_name: str,
            connection_string_setting: str,
            user_id: str,
        ) -> Callable[[F], F]:
            _ = (arg_name, hub_name, connection_string_setting, user_id)
            return _passthrough

        def event_grid_trigger(self, *, arg_name: str) -> Callable[[F], F]:
            _ = arg_name
            return _passthrough

        def signalr_output(
            self,
            *,
            arg_name: str,
            hub_name: str,
            connection_string_setting: str,
        ) -> Callable[[F], F]:
            _ = (arg_name, hub_name, connection_string_setting)
            return _passthrough

    class _FallbackFuncModule:
        AuthLevel: type[AuthLevelProtocol] = AuthLevelProtocol
        EventGridEvent: type[_FallbackEventGridEvent] = _FallbackEventGridEvent
        HttpRequest: type[_FallbackHttpRequest] = _FallbackHttpRequest
        HttpResponse: type[_FallbackHttpResponse] = _FallbackHttpResponse
        Out: type[_FallbackOut] = _FallbackOut

        def FunctionApp(self) -> FunctionAppProtocol:
            return _FallbackFunctionApp()

    func = _FallbackFuncModule()


try:
    logging_toolkit = importlib.import_module("azure_functions_logging")
    get_logger = cast(Callable[[str], LoggerProtocol], getattr(logging_toolkit, "get_logger"))
    setup_logging = cast(Callable[..., None], getattr(logging_toolkit, "setup_logging"))
    with_context = cast(Decorator, getattr(logging_toolkit, "with_context"))
except ImportError:
    get_logger = _fallback_get_logger
    setup_logging = _fallback_setup_logging
    with_context = cast(Decorator, _passthrough)


setup_logging(format="json")
app_factory = cast(Callable[[], FunctionAppProtocol], getattr(func, "FunctionApp"))
app = app_factory()
logger = get_logger(__name__)
AUTH_LEVEL_ANONYMOUS = getattr(
    getattr(func, "AuthLevel", AuthLevelProtocol), "ANONYMOUS", "anonymous"
)

HUB_NAME = os.getenv("SIGNALR_HUB_NAME", "notifications")
FALLBACK_NEGOTIATE_USER_ID = os.getenv("SIGNALR_NEGOTIATE_USER_ID", "local-user")
TARGET_METHOD = "notificationReceived"


def _normalize_payload(value: object) -> dict[str, object]:
    if isinstance(value, dict):
        mapping = cast(dict[object, object], value)
        return {str(key): item for key, item in mapping.items()}
    return {"value": value}


def _resolve_user_id(req: HttpRequestProtocol) -> str:
    principal_id = req.headers.get("x-ms-client-principal-id")
    if principal_id:
        return principal_id
    return FALLBACK_NEGOTIATE_USER_ID


def _build_notification(event: EventGridEventProtocol) -> dict[str, object]:
    payload = _normalize_payload(event.get_json())
    return {
        "eventId": event.id,
        "eventType": event.event_type,
        "subject": event.subject,
        "message": str(payload.get("message") or f"New notification for {event.subject}"),
        "data": payload,
    }


@app.route(route="signalr/negotiate", methods=["POST"], auth_level=AUTH_LEVEL_ANONYMOUS)
@app.signalr_connection_info_input(
    arg_name="connection_info",
    hub_name=HUB_NAME,
    connection_string_setting="AzureSignalRConnectionString",
    user_id=FALLBACK_NEGOTIATE_USER_ID,
)
def negotiate_signalr(req: HttpRequestProtocol, connection_info: str) -> HttpResponseProtocol:
    user_id = _resolve_user_id(req)
    logger.info("Negotiated SignalR connection", extra={"hub": HUB_NAME, "user_id": user_id})
    return func.HttpResponse(connection_info, mimetype="application/json")


@app.event_grid_trigger(arg_name="event")
@app.signalr_output(
    arg_name="signalr",
    hub_name=HUB_NAME,
    connection_string_setting="AzureSignalRConnectionString",
)
@with_context
def publish_notification(event: EventGridEventProtocol, signalr: OutProtocol) -> None:
    notification = _build_notification(event)
    logger.info(
        "Publishing SignalR notification",
        extra={
            "hub": HUB_NAME,
            "target": TARGET_METHOD,
            "event_id": notification["eventId"],
            "event_type": notification["eventType"],
            "subject": notification["subject"],
        },
    )
    signalr.set(json.dumps({"target": TARGET_METHOD, "arguments": [notification]}))
