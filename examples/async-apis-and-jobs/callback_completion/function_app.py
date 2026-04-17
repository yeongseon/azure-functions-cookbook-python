# pyright: reportMissingImports=false, reportUnknownVariableType=false, reportUnknownMemberType=false, reportUnknownArgumentType=false, reportUnknownParameterType=false, reportUntypedFunctionDecorator=false, reportUntypedBaseClass=false, reportAny=false, reportExplicitAny=false

from __future__ import annotations

import importlib
import json
import logging
import os
import time
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Protocol, TypeVar, cast
from urllib import error, parse, request
from uuid import uuid4

from pydantic import BaseModel, Field, field_validator

F = TypeVar("F", bound=Callable[..., object])


class HttpRequestProtocol(Protocol): ...


class HttpResponseProtocol(Protocol): ...


class QueueMessageProtocol(Protocol):
    def get_body(self) -> bytes: ...


class OutProtocol(Protocol):
    def set(self, value: str) -> None: ...


class AuthLevelProtocol:
    ANONYMOUS: str = "anonymous"


class FunctionAppProtocol(Protocol):
    def route(
        self, *, route: str, methods: list[str], auth_level: object | None = None
    ) -> Callable[[F], F]: ...

    def queue_output(
        self, *, arg_name: str, queue_name: str, connection: str
    ) -> Callable[[F], F]: ...

    def queue_trigger(
        self, *, arg_name: str, queue_name: str, connection: str
    ) -> Callable[[F], F]: ...


class LoggerProtocol(Protocol):
    def info(self, msg: object, *, extra: Mapping[str, object] | None = None) -> None: ...

    def warning(self, msg: object, *, extra: Mapping[str, object] | None = None) -> None: ...

    def error(self, msg: object, *, extra: Mapping[str, object] | None = None) -> None: ...


Decorator = Callable[[Callable[..., object]], Callable[..., object]]


def _passthrough(function: F) -> F:
    return function


def _fallback_setup_logging(*, format: str = "json") -> None:
    _ = format
    logging.basicConfig(level=logging.INFO)


def _fallback_get_logger(name: str) -> LoggerProtocol:
    return logging.getLogger(name)


def _fallback_validate_http(**_: object) -> Decorator:
    return cast(Decorator, _passthrough)


try:
    func = cast(Any, importlib.import_module("azure.functions"))
except ImportError:

    @dataclass
    class _FallbackHttpRequest:
        body: bytes = b""

    class _FallbackHttpResponse:
        def __init__(
            self,
            body: str,
            *,
            status_code: int = 200,
            mimetype: str = "text/plain",
            headers: Mapping[str, str] | None = None,
        ) -> None:
            self.body: str = body
            self.status_code: int = status_code
            self.mimetype: str = mimetype
            self.headers: dict[str, str] = dict(headers or {})

    class _FallbackOut:
        def set(self, value: str) -> None:
            _ = value

    @dataclass
    class _FallbackQueueMessage:
        body: bytes = b"{}"

        def get_body(self) -> bytes:
            return self.body

    class _FallbackFunctionApp:
        def route(
            self, *, route: str, methods: list[str], auth_level: object | None = None
        ) -> Callable[[F], F]:
            _ = (route, methods, auth_level)
            return _passthrough

        def queue_output(
            self, *, arg_name: str, queue_name: str, connection: str
        ) -> Callable[[F], F]:
            _ = (arg_name, queue_name, connection)
            return _passthrough

        def queue_trigger(
            self, *, arg_name: str, queue_name: str, connection: str
        ) -> Callable[[F], F]:
            _ = (arg_name, queue_name, connection)
            return _passthrough

    class _FallbackFuncModule:
        AuthLevel: type[AuthLevelProtocol] = AuthLevelProtocol
        HttpRequest: type[_FallbackHttpRequest] = _FallbackHttpRequest
        HttpResponse: type[_FallbackHttpResponse] = _FallbackHttpResponse
        Out: type[_FallbackOut] = _FallbackOut
        QueueMessage: type[_FallbackQueueMessage] = _FallbackQueueMessage

        def FunctionApp(self, **_: object) -> FunctionAppProtocol:
            return _FallbackFunctionApp()

    func = _FallbackFuncModule()


try:
    logging_toolkit = importlib.import_module("azure_functions_logging")
    get_logger = cast(Callable[[str], LoggerProtocol], getattr(logging_toolkit, "get_logger"))
    setup_logging = cast(Callable[..., None], getattr(logging_toolkit, "setup_logging"))
except ImportError:
    get_logger = _fallback_get_logger
    setup_logging = _fallback_setup_logging


try:
    validation_toolkit = importlib.import_module("azure_functions_validation")
    validate_http = cast(Callable[..., Decorator], getattr(validation_toolkit, "validate_http"))
except ImportError:
    validate_http = _fallback_validate_http


setup_logging(format="json")
logger = get_logger(__name__)
AUTH_LEVEL_ANONYMOUS = getattr(
    getattr(func, "AuthLevel", AuthLevelProtocol), "ANONYMOUS", "anonymous"
)
TASK_QUEUE_NAME = os.getenv("TASK_QUEUE_NAME", "callback-tasks")
TASK_PROCESSING_DELAY_SECONDS = int(os.getenv("TASK_PROCESSING_DELAY_SECONDS", "3"))

app_factory = cast(Callable[..., FunctionAppProtocol], getattr(func, "FunctionApp"))
app = app_factory(http_auth_level=AUTH_LEVEL_ANONYMOUS)


class TaskCreateRequest(BaseModel):
    task_name: str = Field(..., min_length=1, description="Logical task name")
    callback_url: str = Field(..., min_length=1, description="HTTP callback endpoint")

    @field_validator("callback_url")
    @classmethod
    def validate_callback_url(cls, value: str) -> str:
        parsed = parse.urlparse(value)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            raise ValueError("callback_url must be a valid http or https URL.")
        return value


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _json_response(payload: dict[str, Any], *, status_code: int) -> HttpResponseProtocol:
    response_factory = cast(Callable[..., HttpResponseProtocol], getattr(func, "HttpResponse"))
    return response_factory(
        body=json.dumps(payload),
        status_code=status_code,
        mimetype="application/json",
    )


def _queue_message_to_dict(message: QueueMessageProtocol | str | bytes) -> dict[str, Any]:
    if isinstance(message, str):
        raw = message
    elif isinstance(message, bytes):
        raw = message.decode("utf-8")
    else:
        raw = message.get_body().decode("utf-8")
    payload = json.loads(raw)
    if not isinstance(payload, dict):
        raise ValueError("Queue message payload must be a JSON object.")
    return cast(dict[str, Any], payload)


def _build_result(payload: Mapping[str, Any]) -> dict[str, Any]:
    task_id = str(payload.get("task_id", "unknown-task"))
    task_name = str(payload.get("task_name", "unknown-task"))
    return {
        "taskName": task_name,
        "artifactUrl": f"https://example.invalid/results/{task_id}.json",
        "processedAt": _utc_now_iso(),
    }


def _send_callback(callback_url: str, payload: dict[str, Any]) -> int:
    callback_request = request.Request(
        callback_url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with request.urlopen(callback_request, timeout=10) as response:
            return int(getattr(response, "status", 200))
    except error.HTTPError as exc:
        logger.error(
            "Callback endpoint returned HTTP error",
            extra={"callback_url": callback_url, "status_code": exc.code},
        )
        raise
    except error.URLError as exc:
        logger.error(
            "Callback delivery failed",
            extra={"callback_url": callback_url, "reason": str(exc.reason)},
        )
        raise


@app.route(route="tasks", methods=["POST"], auth_level=AUTH_LEVEL_ANONYMOUS)
@validate_http(body=TaskCreateRequest)
@app.queue_output(
    arg_name="task_queue",
    queue_name=TASK_QUEUE_NAME,
    connection="AzureWebJobsStorage",
)
def submit_task(
    req: HttpRequestProtocol,
    body: TaskCreateRequest,
    task_queue: OutProtocol,
) -> HttpResponseProtocol:
    _ = req
    task_id = str(uuid4())
    queue_payload = {
        "task_id": task_id,
        "task_name": body.task_name,
        "callback_url": body.callback_url,
        "submitted_at": _utc_now_iso(),
    }
    task_queue.set(json.dumps(queue_payload))

    logger.info(
        "Accepted callback completion task",
        extra={"task_id": task_id, "task_name": body.task_name, "callback_url": body.callback_url},
    )
    return _json_response(
        {"status": "accepted", "task_id": task_id, "callback_pending": True},
        status_code=202,
    )


@app.queue_trigger(
    arg_name="msg",
    queue_name=TASK_QUEUE_NAME,
    connection="AzureWebJobsStorage",
)
def process_task(msg: QueueMessageProtocol | str | bytes) -> None:
    payload = _queue_message_to_dict(msg)
    task_id = str(payload.get("task_id", "unknown-task"))
    callback_url = str(payload.get("callback_url", ""))

    if not callback_url:
        raise ValueError("callback_url is required in the queued task payload.")

    logger.info(
        "Processing callback completion task",
        extra={"task_id": task_id, "task_name": payload.get("task_name")},
    )
    time.sleep(TASK_PROCESSING_DELAY_SECONDS)

    callback_payload = {
        "status": "completed",
        "task_id": task_id,
        "result": _build_result(payload),
        "completed_at": _utc_now_iso(),
    }
    status_code = _send_callback(callback_url, callback_payload)

    logger.info(
        "Delivered callback completion payload",
        extra={"task_id": task_id, "callback_url": callback_url, "status_code": status_code},
    )
