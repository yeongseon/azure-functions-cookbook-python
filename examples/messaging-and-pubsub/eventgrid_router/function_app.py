from __future__ import annotations

import importlib
import logging
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from typing import Protocol, TypeVar, cast

F = TypeVar("F", bound=Callable[..., object])


class EventGridEventProtocol(Protocol):
    id: str
    event_type: str
    subject: str

    def get_json(self) -> object: ...


class FunctionAppProtocol(Protocol):
    def event_grid_trigger(self, *, arg_name: str) -> Callable[[F], F]: ...


class LoggerProtocol(Protocol):
    def info(self, msg: object, *, extra: Mapping[str, object] | None = None) -> None: ...

    def warning(self, msg: object, *, extra: Mapping[str, object] | None = None) -> None: ...


Decorator = Callable[[Callable[..., object]], Callable[..., object]]


def _passthrough(function: F) -> F:
    return function


def _fallback_setup_logging(*, format: str = "json") -> None:
    _ = format
    logging.basicConfig(level=logging.INFO)


def _fallback_get_logger(name: str) -> LoggerProtocol:
    return logging.getLogger(name)


try:
    func = cast(object, importlib.import_module("azure.functions"))
except ImportError:

    @dataclass
    class _FallbackEventGridEvent:
        id: str = ""
        event_type: str = ""
        subject: str = ""

        def get_json(self) -> object:
            return {}

    class _FallbackFunctionApp:
        def event_grid_trigger(self, *, arg_name: str) -> Callable[[F], F]:
            _ = arg_name
            return _passthrough

    class _FallbackFuncModule:
        EventGridEvent: type[EventGridEventProtocol] = _FallbackEventGridEvent

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


def _payload_dict(value: object) -> dict[str, object]:
    if isinstance(value, dict):
        mapping = cast(dict[object, object], value)
        return {str(key): item for key, item in mapping.items()}
    return {"value": value}


def handle_blob_created(event: EventGridEventProtocol, payload: dict[str, object]) -> None:
    logger.info(
        "Handled blob created event",
        extra={
            "event_id": event.id,
            "subject": event.subject,
            "blob_url": payload.get("url"),
            "api": payload.get("api"),
        },
    )


def handle_premium_item_archived(event: EventGridEventProtocol, payload: dict[str, object]) -> None:
    logger.info(
        "Handled premium item archived event",
        extra={
            "event_id": event.id,
            "subject": event.subject,
            "item_id": payload.get("itemId"),
            "reason": payload.get("reason"),
        },
    )


def handle_unknown_event(event: EventGridEventProtocol, payload: dict[str, object]) -> None:
    logger.warning(
        "No explicit route matched Event Grid event",
        extra={
            "event_id": event.id,
            "event_type": event.event_type,
            "subject": event.subject,
            "payload_keys": sorted(payload.keys()),
        },
    )


Handler = Callable[[EventGridEventProtocol, dict[str, object]], None]

ROUTES: dict[str, Handler] = {
    "blob_created": handle_blob_created,
    "premium_item_archived": handle_premium_item_archived,
    "fallback": handle_unknown_event,
}


def _resolve_route(event_type: str, subject: str) -> str:
    if event_type == "Microsoft.Storage.BlobCreated" and "/containers/inbound-blobs/" in subject:
        return "blob_created"
    if event_type == "Contoso.Items.ItemArchived" and subject.startswith("/tenants/premium/"):
        return "premium_item_archived"
    return "fallback"


@app.event_grid_trigger(arg_name="event")
@with_context
def route_events(event: EventGridEventProtocol) -> None:
    payload = _payload_dict(event.get_json())
    route_key = _resolve_route(event.event_type, event.subject)
    logger.info(
        "Routing Event Grid event",
        extra={
            "event_id": event.id,
            "event_type": event.event_type,
            "subject": event.subject,
            "route_key": route_key,
        },
    )
    handler = ROUTES.get(route_key, handle_unknown_event)
    handler(event, payload)
