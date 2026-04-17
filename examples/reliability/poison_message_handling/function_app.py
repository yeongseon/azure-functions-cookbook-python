from __future__ import annotations

import json
import logging
from importlib import import_module
from typing import Callable, Protocol, cast


class QueueMessageLike(Protocol):
    id: str
    dequeue_count: int | None

    def get_body(self) -> bytes: ...


class FunctionAppLike(Protocol):
    def function_name(
        self,
        *,
        name: str,
    ) -> Callable[[Callable[..., object]], Callable[..., object]]: ...

    def queue_trigger(
        self,
        *,
        arg_name: str,
        queue_name: str,
        connection: str,
    ) -> Callable[[Callable[..., object]], Callable[..., object]]: ...


class FuncModuleLike(Protocol):
    def FunctionApp(self) -> FunctionAppLike: ...


class _RuntimeFunctionApp:
    def function_name(
        self,
        *,
        name: str,
    ) -> Callable[[Callable[..., object]], Callable[..., object]]:
        _ = name

        def decorate(func: Callable[..., object]) -> Callable[..., object]:
            return func

        return decorate

    def queue_trigger(
        self,
        *,
        arg_name: str,
        queue_name: str,
        connection: str,
    ) -> Callable[[Callable[..., object]], Callable[..., object]]:
        _ = (arg_name, queue_name, connection)

        def decorate(func: Callable[..., object]) -> Callable[..., object]:
            return func

        return decorate


class _RuntimeFuncModule:
    def FunctionApp(self) -> FunctionAppLike:
        return _RuntimeFunctionApp()


try:
    _func_module = import_module("azure.functions")
except ModuleNotFoundError:
    _func_module = _RuntimeFuncModule()


func = cast(FuncModuleLike, _func_module)
app = func.FunctionApp()


@app.function_name(name="queue_processor")
@app.queue_trigger(arg_name="msg", queue_name="orders", connection="AzureWebJobsStorage")
def queue_processor(msg: QueueMessageLike) -> None:
    raw_body = msg.get_body().decode("utf-8")
    dequeue_count = msg.dequeue_count

    try:
        payload = cast(dict[str, object], json.loads(raw_body))
    except json.JSONDecodeError as exc:
        logging.warning(
            "Invalid JSON encountered. message_id=%s dequeue_count=%s body=%s",
            msg.id,
            dequeue_count,
            raw_body,
        )
        raise ValueError("Queue payload must be valid JSON.") from exc

    order_id = str(payload.get("order_id", "unknown"))
    should_fail = bool(payload.get("should_fail", False))

    if should_fail:
        logging.warning(
            "Simulated failure for order_id=%s dequeue_count=%s message_id=%s",
            order_id,
            dequeue_count,
            msg.id,
        )
        raise RuntimeError(f"Simulated processing failure for order_id={order_id}")

    logging.info(
        "Processing order_id=%s dequeue_count=%s message_id=%s payload=%s",
        order_id,
        dequeue_count,
        msg.id,
        payload,
    )


@app.function_name(name="poison_handler")
@app.queue_trigger(arg_name="msg", queue_name="orders-poison", connection="AzureWebJobsStorage")
def poison_handler(msg: QueueMessageLike) -> None:
    raw_body = msg.get_body().decode("utf-8")
    logging.error(
        "Poison message detected. queue=orders-poison message_id=%s dequeue_count=%s payload=%s",
        msg.id,
        msg.dequeue_count,
        raw_body,
    )
    logging.error("Alert operators to inspect and replay the message after fixing the root cause.")
