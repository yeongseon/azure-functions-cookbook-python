from __future__ import annotations

import importlib
import json
import logging
import os
import uuid
from collections.abc import Callable, Iterable, Mapping
from dataclasses import dataclass
from http import HTTPStatus
from typing import Protocol, TypeVar, cast

F = TypeVar("F", bound=Callable[..., object])
Decorator = Callable[[Callable[..., object]], Callable[..., object]]


class LoggerProtocol(Protocol):
    def info(self, msg: object, *, extra: Mapping[str, object] | None = None) -> None: ...

    def warning(self, msg: object, *, extra: Mapping[str, object] | None = None) -> None: ...

    def error(self, msg: object, *, extra: Mapping[str, object] | None = None) -> None: ...

    def exception(self, msg: object, *, extra: Mapping[str, object] | None = None) -> None: ...


class HttpRequestProtocol(Protocol):
    params: Mapping[str, str]

    def get_json(self) -> object: ...


class HttpResponseProtocol(Protocol):
    body: object
    status_code: int
    mimetype: str | None


class AuthLevelProtocol(Protocol):
    FUNCTION: object


class ServiceBusTriggerMessageProtocol(Protocol):
    message_id: str | None
    correlation_id: str | None
    delivery_count: int | None
    dead_letter_reason: str | None
    dead_letter_error_description: str | None

    def get_body(self) -> bytes: ...


class ServiceBusReceivedMessageProtocol(Protocol):
    body: bytes | str | Iterable[object]
    application_properties: Mapping[object, object] | None
    content_type: str | None
    correlation_id: str | None
    dead_letter_reason: str | None
    message_id: str | None
    partition_key: str | None
    reply_to: str | None
    reply_to_session_id: str | None
    session_id: str | None
    subject: str | None
    time_to_live: object
    to: str | None


class ServiceBusSenderProtocol(Protocol):
    def __enter__(self) -> ServiceBusSenderProtocol: ...

    def __exit__(self, exc_type: object, exc: object, tb: object) -> None: ...

    def send_messages(self, message: object) -> None: ...


class ServiceBusReceiverProtocol(Protocol):
    def __enter__(self) -> ServiceBusReceiverProtocol: ...

    def __exit__(self, exc_type: object, exc: object, tb: object) -> None: ...

    def receive_messages(
        self, *, max_message_count: int, max_wait_time: int
    ) -> list[ServiceBusReceivedMessageProtocol]: ...

    def complete_message(self, message: ServiceBusReceivedMessageProtocol) -> None: ...


class ServiceBusClientProtocol(Protocol):
    @classmethod
    def from_connection_string(cls, *, conn_str: str) -> ServiceBusClientProtocol: ...

    def __enter__(self) -> ServiceBusClientProtocol: ...

    def __exit__(self, exc_type: object, exc: object, tb: object) -> None: ...

    def get_queue_receiver(
        self,
        *,
        queue_name: str,
        sub_queue: object,
        max_wait_time: int,
    ) -> ServiceBusReceiverProtocol: ...

    def get_queue_sender(self, *, queue_name: str) -> ServiceBusSenderProtocol: ...


class FunctionAppProtocol(Protocol):
    def service_bus_queue_trigger(
        self, *, arg_name: str, queue_name: str, connection: str
    ) -> Callable[[F], F]: ...

    def route(self, *, route: str, methods: list[str]) -> Callable[[F], F]: ...


class ServiceBusMessageFactoryProtocol(Protocol):
    def __call__(self, **kwargs: object) -> object: ...


class ServiceBusSubQueueProtocol(Protocol):
    DEAD_LETTER: object


def _passthrough(function: F) -> F:
    return function


def _fallback_setup_logging(*, format: str = "json") -> None:
    _ = format
    logging.basicConfig(level=logging.INFO)


def _fallback_get_logger(name: str) -> LoggerProtocol:
    return logging.getLogger(name)


@dataclass
class _FallbackHttpResponse:
    body: object
    status_code: int = HTTPStatus.OK
    mimetype: str | None = None


@dataclass
class _FallbackTriggerMessage:
    payload: bytes = b""
    message_id: str | None = None
    correlation_id: str | None = None
    delivery_count: int | None = 1
    dead_letter_reason: str | None = None
    dead_letter_error_description: str | None = None

    def get_body(self) -> bytes:
        return self.payload


class _FallbackSender:
    def __enter__(self) -> _FallbackSender:
        return self

    def __exit__(self, exc_type: object, exc: object, tb: object) -> None:
        _ = (exc_type, exc, tb)

    def send_messages(self, message: object) -> None:
        _ = message


class _FallbackReceiver:
    def __enter__(self) -> _FallbackReceiver:
        return self

    def __exit__(self, exc_type: object, exc: object, tb: object) -> None:
        _ = (exc_type, exc, tb)

    def receive_messages(
        self, *, max_message_count: int, max_wait_time: int
    ) -> list[ServiceBusReceivedMessageProtocol]:
        _ = (max_message_count, max_wait_time)
        return []

    def complete_message(self, message: ServiceBusReceivedMessageProtocol) -> None:
        _ = message


class _FallbackServiceBusClient:
    @classmethod
    def from_connection_string(cls, *, conn_str: str) -> _FallbackServiceBusClient:
        _ = conn_str
        return cls()

    def __enter__(self) -> _FallbackServiceBusClient:
        return self

    def __exit__(self, exc_type: object, exc: object, tb: object) -> None:
        _ = (exc_type, exc, tb)

    def get_queue_receiver(
        self,
        *,
        queue_name: str,
        sub_queue: object,
        max_wait_time: int,
    ) -> ServiceBusReceiverProtocol:
        _ = (queue_name, sub_queue, max_wait_time)
        return _FallbackReceiver()

    def get_queue_sender(self, *, queue_name: str) -> ServiceBusSenderProtocol:
        _ = queue_name
        return _FallbackSender()


class _FallbackFunctionApp:
    def __init__(self, *, http_auth_level: object) -> None:
        _ = http_auth_level

    def service_bus_queue_trigger(
        self, *, arg_name: str, queue_name: str, connection: str
    ) -> Callable[[F], F]:
        _ = (arg_name, queue_name, connection)
        return _passthrough

    def route(self, *, route: str, methods: list[str]) -> Callable[[F], F]:
        _ = (route, methods)
        return _passthrough


class _FallbackAuthLevel:
    FUNCTION: str = "function"


class _FallbackFuncModule:
    AuthLevel: type[_FallbackAuthLevel] = _FallbackAuthLevel
    HttpRequest: type[object] = object
    HttpResponse: type[_FallbackHttpResponse] = _FallbackHttpResponse
    ServiceBusMessage: type[_FallbackTriggerMessage] = _FallbackTriggerMessage

    @staticmethod
    def FunctionApp(*, http_auth_level: object) -> FunctionAppProtocol:
        return _FallbackFunctionApp(http_auth_level=http_auth_level)


class _FallbackServiceBusSubQueue:
    DEAD_LETTER: str = "dead_letter"


def _fallback_servicebus_message(**kwargs: object) -> dict[str, object]:
    return kwargs


try:
    func = cast(object, importlib.import_module("azure.functions"))
except ImportError:
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

try:
    servicebus_module = importlib.import_module("azure.servicebus")
    ServiceBusClient = cast(
        ServiceBusClientProtocol, getattr(servicebus_module, "ServiceBusClient")
    )
    ServiceBusMessage = cast(
        ServiceBusMessageFactoryProtocol, getattr(servicebus_module, "ServiceBusMessage")
    )
    ServiceBusSubQueue = cast(
        ServiceBusSubQueueProtocol, getattr(servicebus_module, "ServiceBusSubQueue")
    )
except ImportError:
    ServiceBusClient = cast(ServiceBusClientProtocol, _FallbackServiceBusClient)
    ServiceBusMessage = cast(ServiceBusMessageFactoryProtocol, _fallback_servicebus_message)
    ServiceBusSubQueue = cast(
        ServiceBusSubQueueProtocol, cast(object, _FallbackServiceBusSubQueue())
    )

try:
    servicebus_exceptions = importlib.import_module("azure.servicebus.exceptions")
    ServiceBusError = cast(type[Exception], getattr(servicebus_exceptions, "ServiceBusError"))
except ImportError:
    ServiceBusError = Exception

setup_logging(format="json")
logger = get_logger(__name__)

QUEUE_NAME = os.getenv("SERVICEBUS_QUEUE_NAME", "orders")
DLQ_BATCH_SIZE = int(os.getenv("DLQ_REPLAY_BATCH_SIZE", "10"))
SERVICE_BUS_CONNECTION_SETTING = "ServiceBusConnection"

auth_level = cast(AuthLevelProtocol, getattr(func, "AuthLevel"))
app_factory = cast(Callable[..., FunctionAppProtocol], getattr(func, "FunctionApp"))
http_response = cast(Callable[..., HttpResponseProtocol], getattr(func, "HttpResponse"))
app = app_factory(http_auth_level=auth_level.FUNCTION)


def _application_properties_dict(properties: Mapping[object, object] | None) -> dict[str, object]:
    normalized: dict[str, object] = {}
    for key, value in (properties or {}).items():
        normalized[str(key)] = value
    return normalized


def _message_body_bytes(message: ServiceBusReceivedMessageProtocol) -> bytes:
    body = message.body

    if isinstance(body, bytes):
        return body
    if isinstance(body, str):
        return body.encode("utf-8")

    chunks: list[bytes] = []
    for item in body:
        if isinstance(item, bytes):
            chunks.append(item)
        elif isinstance(item, str):
            chunks.append(item.encode("utf-8"))
        elif isinstance(item, bytearray):
            chunks.append(bytes(item))
        elif isinstance(item, memoryview):
            chunks.append(item.tobytes())
        else:
            chunks.append(str(item).encode("utf-8"))
    return b"".join(chunks)


def _log_dead_letter_message(msg: ServiceBusTriggerMessageProtocol) -> None:
    raw_body = msg.get_body().decode("utf-8", errors="replace")
    logger.warning(
        "Dead-lettered Service Bus message detected",
        extra={
            "queue_name": QUEUE_NAME,
            "message_id": getattr(msg, "message_id", None),
            "correlation_id": getattr(msg, "correlation_id", None),
            "delivery_count": int(getattr(msg, "delivery_count", 1)),
            "dead_letter_reason": getattr(msg, "dead_letter_reason", None),
            "dead_letter_error_description": getattr(msg, "dead_letter_error_description", None),
            "body_preview": raw_body[:512],
        },
    )


def _resolve_batch_size(req: HttpRequestProtocol) -> int:
    limit_value = req.params.get("limit")
    if not limit_value:
        try:
            payload = req.get_json()
        except ValueError:
            payload = {}

        if isinstance(payload, Mapping):
            payload_mapping = cast(Mapping[str, object], payload)
            raw_limit_obj = payload_mapping.get("limit", DLQ_BATCH_SIZE)
        else:
            raw_limit_obj = DLQ_BATCH_SIZE
        limit_value = str(raw_limit_obj)

    try:
        requested = int(limit_value)
    except (TypeError, ValueError):
        requested = DLQ_BATCH_SIZE

    return max(1, min(requested, 100))


def _build_replay_message(message: ServiceBusReceivedMessageProtocol) -> tuple[object, str]:
    application_properties = _application_properties_dict(message.application_properties)
    application_properties["replayed_from_dlq"] = True
    if getattr(message, "dead_letter_reason", None):
        application_properties["dead_letter_reason"] = message.dead_letter_reason

    message_id = getattr(message, "message_id", None)
    replay_message_id = (
        f"{message_id}-replay-{uuid.uuid4().hex[:8]}"
        if message_id
        else f"replay-{uuid.uuid4().hex}"
    )

    replay_message = ServiceBusMessage(
        body=_message_body_bytes(message),
        application_properties=application_properties,
        content_type=message.content_type,
        correlation_id=message.correlation_id,
        message_id=replay_message_id,
        partition_key=message.partition_key,
        reply_to=message.reply_to,
        reply_to_session_id=message.reply_to_session_id,
        session_id=message.session_id,
        subject=message.subject,
        time_to_live=message.time_to_live,
        to=message.to,
    )
    return replay_message, replay_message_id


@app.service_bus_queue_trigger(
    arg_name="msg",
    queue_name=f"{QUEUE_NAME}/$DeadLetterQueue",
    connection=SERVICE_BUS_CONNECTION_SETTING,
)
def log_dead_lettered_message(msg: ServiceBusTriggerMessageProtocol) -> None:
    _log_dead_letter_message(msg)


@app.route(route="servicebus/dlq/replay", methods=["POST"])
@with_context
def replay_dead_letter_queue(req: HttpRequestProtocol) -> HttpResponseProtocol:
    batch_size = _resolve_batch_size(req)
    replayed: list[dict[str, object]] = []

    try:
        client = ServiceBusClient.from_connection_string(
            conn_str=os.environ[SERVICE_BUS_CONNECTION_SETTING]
        )
    except KeyError:
        logger.error(
            "Missing Service Bus connection setting",
            extra={"setting": SERVICE_BUS_CONNECTION_SETTING},
        )
        return http_response(
            body=json.dumps({"error": f"Missing app setting: {SERVICE_BUS_CONNECTION_SETTING}"}),
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
            mimetype="application/json",
        )

    try:
        with client:
            receiver = client.get_queue_receiver(
                queue_name=QUEUE_NAME,
                sub_queue=ServiceBusSubQueue.DEAD_LETTER,
                max_wait_time=5,
            )
            sender = client.get_queue_sender(queue_name=QUEUE_NAME)

            with receiver, sender:
                messages = receiver.receive_messages(
                    max_message_count=batch_size,
                    max_wait_time=5,
                )

                for message in messages:
                    replay_message, replay_message_id = _build_replay_message(message)
                    _ = sender.send_messages(replay_message)
                    _ = receiver.complete_message(message)

                    replay_record: dict[str, object] = {
                        "original_message_id": message.message_id,
                        "replayed_message_id": replay_message_id,
                        "correlation_id": message.correlation_id,
                        "dead_letter_reason": message.dead_letter_reason,
                    }
                    replayed.append(replay_record)
                    logger.info("Replayed dead-lettered Service Bus message", extra=replay_record)
    except ServiceBusError as exc:
        logger.exception(
            "Failed to replay Service Bus DLQ messages",
            extra={"queue_name": QUEUE_NAME, "requested_batch_size": batch_size},
        )
        return http_response(
            body=json.dumps(
                {
                    "error": "Failed to replay DLQ messages",
                    "details": str(exc),
                }
            ),
            status_code=HTTPStatus.BAD_GATEWAY,
            mimetype="application/json",
        )

    return http_response(
        body=json.dumps(
            {
                "queue_name": QUEUE_NAME,
                "requested_batch_size": batch_size,
                "replayed_count": len(replayed),
                "messages": replayed,
            }
        ),
        status_code=HTTPStatus.OK,
        mimetype="application/json",
    )
