from __future__ import annotations

import datetime as dt
import importlib
import json
import logging
import uuid
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from typing import Protocol, TypeVar, cast

F = TypeVar("F", bound=Callable[..., object])
T_contra = TypeVar("T_contra", contravariant=True)


class HttpRequestProtocol(Protocol):
    def get_json(self) -> object: ...


class HttpResponseProtocol(Protocol):
    status_code: int


class OutProtocol(Protocol[T_contra]):
    def set(self, value: T_contra) -> None: ...


class EventGridEventProtocol(Protocol):
    id: str
    event_type: str
    subject: str

    def get_json(self) -> object: ...


class EventGridOutputEventProtocol(Protocol): ...


class EventGridOutputEventFactory(Protocol):
    def __call__(
        self,
        *,
        id: str,
        subject: str,
        event_type: str,
        event_time: dt.datetime,
        data: dict[str, object],
        data_version: str,
    ) -> EventGridOutputEventProtocol: ...


class HttpResponseFactory(Protocol):
    def __call__(
        self,
        *,
        body: str,
        status_code: int,
        mimetype: str,
    ) -> HttpResponseProtocol: ...


class FunctionAppProtocol(Protocol):
    def function_name(self, *, name: str) -> Callable[[F], F]: ...

    def route(
        self,
        *,
        route: str,
        methods: list[str],
        auth_level: object | None = None,
    ) -> Callable[[F], F]: ...

    def event_grid_output(
        self,
        *,
        arg_name: str,
        topic_endpoint_uri: str,
        topic_key_setting: str,
    ) -> Callable[[F], F]: ...

    def event_grid_trigger(self, *, arg_name: str) -> Callable[[F], F]: ...


class LoggerProtocol(Protocol):
    def info(self, msg: object, *, extra: Mapping[str, object] | None = None) -> None: ...


class AuthLevelProtocol(Protocol):
    ANONYMOUS: object


class FuncModuleProtocol(Protocol):
    AuthLevel: AuthLevelProtocol
    EventGridEvent: type[EventGridEventProtocol]
    EventGridOutputEvent: EventGridOutputEventFactory
    HttpRequest: type[HttpRequestProtocol]
    HttpResponse: HttpResponseFactory
    Out: type[OutProtocol[EventGridOutputEventProtocol]]

    def FunctionApp(self, *, http_auth_level: object | None = None) -> FunctionAppProtocol: ...


def _passthrough(function: F) -> F:
    return function


def _fallback_get_logger(name: str) -> LoggerProtocol:
    return logging.getLogger(name)


@dataclass
class _FallbackHttpResponse:
    status_code: int = 200


@dataclass
class _FallbackHttpRequest:
    payload: object = None

    def get_json(self) -> object:
        return self.payload


@dataclass
class _FallbackEventGridEvent:
    id: str = ""
    event_type: str = ""
    subject: str = ""

    def get_json(self) -> object:
        return {}


@dataclass
class _FallbackEventGridOutputEvent:
    id: str
    subject: str
    event_type: str
    event_time: dt.datetime
    data: dict[str, object]
    data_version: str


class _FallbackOut:
    def set(self, value: _FallbackEventGridOutputEvent) -> None:
        _ = value


def _fallback_http_response(*, body: str, status_code: int, mimetype: str) -> HttpResponseProtocol:
    _ = (body, mimetype)
    return _FallbackHttpResponse(status_code=status_code)


class _FallbackAuthLevel:
    ANONYMOUS: object = object()


class _FallbackFunctionApp:
    def function_name(self, *, name: str) -> Callable[[F], F]:
        _ = name
        return _passthrough

    def route(
        self,
        *,
        route: str,
        methods: list[str],
        auth_level: object | None = None,
    ) -> Callable[[F], F]:
        _ = (route, methods, auth_level)
        return _passthrough

    def event_grid_output(
        self,
        *,
        arg_name: str,
        topic_endpoint_uri: str,
        topic_key_setting: str,
    ) -> Callable[[F], F]:
        _ = (arg_name, topic_endpoint_uri, topic_key_setting)
        return _passthrough

    def event_grid_trigger(self, *, arg_name: str) -> Callable[[F], F]:
        _ = arg_name
        return _passthrough


class _FallbackFuncModule:
    AuthLevel: type[_FallbackAuthLevel] = _FallbackAuthLevel
    EventGridEvent: type[_FallbackEventGridEvent] = _FallbackEventGridEvent
    EventGridOutputEvent: EventGridOutputEventFactory = _FallbackEventGridOutputEvent
    HttpRequest: type[_FallbackHttpRequest] = _FallbackHttpRequest
    HttpResponse: HttpResponseFactory = _fallback_http_response
    Out: type[_FallbackOut] = _FallbackOut

    def FunctionApp(self, *, http_auth_level: object | None = None) -> FunctionAppProtocol:
        _ = http_auth_level
        return _FallbackFunctionApp()


try:
    func = cast(FuncModuleProtocol, cast(object, importlib.import_module("azure.functions")))
except ImportError:
    func = _FallbackFuncModule()


app = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)
logger = _fallback_get_logger(__name__)

ALLOWED_EVENT_TYPES: dict[str, str] = {
    "OrderPlaced": "Contoso.Orders.OrderPlaced",
    "OrderShipped": "Contoso.Orders.OrderShipped",
}


@app.function_name(name="publish_order_event")
@app.route(route="orders/events", methods=["POST"], auth_level=func.AuthLevel.ANONYMOUS)
@app.event_grid_output(
    arg_name="output_event",
    topic_endpoint_uri="MyEventGridTopicUriSetting",
    topic_key_setting="MyEventGridTopicKeySetting",
)
def publish_order_event(
    req: HttpRequestProtocol,
    output_event: OutProtocol[EventGridOutputEventProtocol],
) -> HttpResponseProtocol:
    try:
        payload = _payload_dict(req.get_json())
    except ValueError:
        return _json_response({"error": "Request body must be valid JSON."}, status_code=400)

    is_valid, error_message = _validate_payload(payload)
    if not is_valid:
        return _json_response({"error": error_message or "Invalid payload."}, status_code=400)

    event_name = _require_text(payload, "event_type")
    order_id = _require_text(payload, "order_id")
    custom_event_type = ALLOWED_EVENT_TYPES[event_name]
    subject = f"/orders/{order_id}"

    output_event.set(
        func.EventGridOutputEvent(
            id=str(uuid.uuid4()),
            subject=subject,
            event_type=custom_event_type,
            event_time=dt.datetime.now(dt.timezone.utc),
            data=_build_event_payload(payload),
            data_version="1.0",
        )
    )

    logger.info(
        "Accepted order domain event publication",
        extra={
            "event_type": custom_event_type,
            "order_id": order_id,
            "subject": subject,
        },
    )

    return _json_response(
        {
            "status": "accepted",
            "published_event_type": custom_event_type,
            "subject": subject,
        },
        status_code=202,
    )


@app.function_name(name="handle_order_domain_event")
@app.event_grid_trigger(arg_name="event")
def handle_order_domain_event(event: EventGridEventProtocol) -> None:
    payload = _payload_dict(event.get_json())
    logger.info(
        "Handled order domain event",
        extra={
            "event_id": event.id,
            "event_type": event.event_type,
            "subject": event.subject,
            "order_id": _optional_text(payload, "orderId"),
            "customer_id": _optional_text(payload, "customerId"),
            "status": _optional_text(payload, "status"),
        },
    )


def _payload_dict(value: object) -> dict[str, object]:
    if isinstance(value, dict):
        mapping = cast(dict[object, object], value)
        return {str(key): item for key, item in mapping.items()}
    return {"value": value}


def _optional_text(payload: Mapping[str, object], key: str) -> str | None:
    value = payload.get(key)
    if value is None:
        return None
    return str(value)


def _require_text(payload: Mapping[str, object], key: str) -> str:
    value = payload.get(key)
    if value is None:
        raise ValueError(f"{key} is required")
    return str(value)


def _validate_payload(payload: Mapping[str, object]) -> tuple[bool, str | None]:
    event_type = _optional_text(payload, "event_type")
    if event_type not in ALLOWED_EVENT_TYPES:
        allowed = ", ".join(sorted(ALLOWED_EVENT_TYPES))
        return False, f"event_type must be one of: {allowed}."

    if _optional_text(payload, "order_id") is None:
        return False, "order_id is required."

    if event_type == "OrderPlaced":
        if payload.get("amount") is None:
            return False, "amount is required for OrderPlaced."
        if _optional_text(payload, "currency") is None:
            return False, "currency is required for OrderPlaced."

    if event_type == "OrderShipped" and _optional_text(payload, "tracking_number") is None:
        return False, "tracking_number is required for OrderShipped."

    return True, None


def _build_event_payload(payload: Mapping[str, object]) -> dict[str, object]:
    event_type = _require_text(payload, "event_type")

    event_payload: dict[str, object] = {
        "orderId": _require_text(payload, "order_id"),
        "status": event_type,
    }

    customer_id = _optional_text(payload, "customer_id")
    if customer_id is not None:
        event_payload["customerId"] = customer_id

    if event_type == "OrderPlaced":
        event_payload["amount"] = payload.get("amount")
        currency = _optional_text(payload, "currency")
        if currency is not None:
            event_payload["currency"] = currency

    if event_type == "OrderShipped":
        tracking_number = _optional_text(payload, "tracking_number")
        carrier = _optional_text(payload, "carrier")
        if tracking_number is not None:
            event_payload["trackingNumber"] = tracking_number
        if carrier is not None:
            event_payload["carrier"] = carrier

    return event_payload


def _json_response(data: Mapping[str, object], *, status_code: int) -> HttpResponseProtocol:
    return func.HttpResponse(
        body=json.dumps(dict(data)),
        status_code=status_code,
        mimetype="application/json",
    )
