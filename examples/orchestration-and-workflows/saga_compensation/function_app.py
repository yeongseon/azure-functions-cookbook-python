from __future__ import annotations

import os
from collections.abc import Generator
from typing import TypedDict, cast

import azure.durable_functions as df
import azure.functions as func
from azure_functions_db import DbBindings
from azure_functions_logging import get_logger, setup_logging, with_context

setup_logging(format="json")
logger = get_logger(__name__)
db = DbBindings()

app = func.FunctionApp()
bp = df.Blueprint()


class SagaInput(TypedDict):
    order_id: str
    sku: str
    quantity: int
    amount: float
    currency: str
    email: str
    fail_payment: bool
    fail_confirmation: bool


class ActivityResult(TypedDict):
    step: str
    status: str
    reservation_id: str
    payment_id: str
    recipient: str
    db_url: str
    db_ready: bool


class AuditPayload(TypedDict):
    order_id: str
    status: str
    completed_steps: list[str]
    compensations: list[str]
    error: str


class SagaResult(TypedDict):
    order_id: str
    status: str
    error: str
    completed_steps: list[ActivityResult]
    compensations: list[ActivityResult]
    confirmation: ActivityResult
    audit: ActivityResult


DEFAULT_SAGA_INPUT: SagaInput = {
    "order_id": "ORD-1001",
    "sku": "demo-widget",
    "quantity": 2,
    "amount": 149.99,
    "currency": "USD",
    "email": "buyer@example.com",
    "fail_payment": False,
    "fail_confirmation": False,
}


def _db_ready() -> bool:
    return isinstance(db, DbBindings)


def _empty_activity(step: str, status: str) -> ActivityResult:
    return {
        "step": step,
        "status": status,
        "reservation_id": "",
        "payment_id": "",
        "recipient": "",
        "db_url": "",
        "db_ready": False,
    }


def _build_saga_input(req: func.HttpRequest) -> SagaInput:
    try:
        payload = req.get_json()
    except ValueError:
        payload = cast(object, {})

    saga_input: SagaInput = {
        "order_id": DEFAULT_SAGA_INPUT["order_id"],
        "sku": DEFAULT_SAGA_INPUT["sku"],
        "quantity": DEFAULT_SAGA_INPUT["quantity"],
        "amount": DEFAULT_SAGA_INPUT["amount"],
        "currency": DEFAULT_SAGA_INPUT["currency"],
        "email": DEFAULT_SAGA_INPUT["email"],
        "fail_payment": DEFAULT_SAGA_INPUT["fail_payment"],
        "fail_confirmation": DEFAULT_SAGA_INPUT["fail_confirmation"],
    }
    if isinstance(payload, dict):
        if isinstance(payload.get("order_id"), str):
            saga_input["order_id"] = payload["order_id"]
        if isinstance(payload.get("sku"), str):
            saga_input["sku"] = payload["sku"]
        if isinstance(payload.get("quantity"), int):
            saga_input["quantity"] = payload["quantity"]
        if isinstance(payload.get("amount"), (int, float)):
            saga_input["amount"] = float(payload["amount"])
        if isinstance(payload.get("currency"), str):
            saga_input["currency"] = payload["currency"]
        if isinstance(payload.get("email"), str):
            saga_input["email"] = payload["email"]
        if isinstance(payload.get("fail_payment"), bool):
            saga_input["fail_payment"] = payload["fail_payment"]
        if isinstance(payload.get("fail_confirmation"), bool):
            saga_input["fail_confirmation"] = payload["fail_confirmation"]
    return saga_input


@bp.route(
    route="start-saga-compensation",
    methods=["POST"],
    auth_level=func.AuthLevel.ANONYMOUS,
)
@bp.durable_client_input(client_name="client")
@with_context
async def start_saga_compensation(
    req: func.HttpRequest,
    client: df.DurableOrchestrationClient,
) -> func.HttpResponse:
    payload = _build_saga_input(req)
    logger.info(
        "Starting saga compensation orchestration",
        extra={
            "order_id": payload["order_id"],
            "db_ready": _db_ready(),
            "db_url_configured": bool(os.getenv("DB_URL")),
        },
    )
    instance_id = await client.start_new("saga_compensation_orchestrator", None, payload)
    return client.create_check_status_response(req, instance_id)


@bp.orchestration_trigger(context_name="context")
def saga_compensation_orchestrator(
    context: df.DurableOrchestrationContext,
) -> Generator[object, object, SagaResult]:
    payload = cast(SagaInput, context.get_input() or dict(DEFAULT_SAGA_INPUT))
    completed_steps: list[ActivityResult] = []
    compensations: list[tuple[str, dict[str, object]]] = []

    try:
        reservation = cast(
            ActivityResult,
            (yield context.call_activity("reserve_inventory", payload)),
        )
        completed_steps.append(reservation)
        compensations.append(
            (
                "release_inventory",
                {
                    "order_id": payload["order_id"],
                    "reservation_id": reservation["reservation_id"],
                    "sku": payload["sku"],
                    "quantity": payload["quantity"],
                },
            )
        )

        payment = cast(
            ActivityResult,
            (yield context.call_activity("charge_payment", payload)),
        )
        completed_steps.append(payment)
        compensations.append(
            (
                "refund_payment",
                {
                    "order_id": payload["order_id"],
                    "payment_id": payment["payment_id"],
                    "amount": payload["amount"],
                    "currency": payload["currency"],
                },
            )
        )

        confirmation = cast(
            ActivityResult,
            (yield context.call_activity("send_confirmation", payload)),
        )
        completed_steps.append(confirmation)

        audit_payload: AuditPayload = {
            "order_id": payload["order_id"],
            "status": "completed",
            "completed_steps": [step["step"] for step in completed_steps],
            "compensations": [],
            "error": "",
        }
        audit = cast(
            ActivityResult,
            (yield context.call_activity("record_saga_audit", audit_payload)),
        )
        return {
            "order_id": payload["order_id"],
            "status": "completed",
            "error": "",
            "completed_steps": completed_steps,
            "compensations": [],
            "confirmation": confirmation,
            "audit": audit,
        }
    except Exception as exc:
        compensation_results: list[ActivityResult] = []
        for activity_name, compensation_payload in reversed(compensations):
            compensation_result = cast(
                ActivityResult,
                (yield context.call_activity(activity_name, compensation_payload)),
            )
            compensation_results.append(compensation_result)

        audit_payload: AuditPayload = {
            "order_id": payload["order_id"],
            "status": "compensated",
            "completed_steps": [step["step"] for step in completed_steps],
            "compensations": [step["step"] for step in compensation_results],
            "error": str(exc),
        }
        audit = cast(
            ActivityResult,
            (yield context.call_activity("record_saga_audit", audit_payload)),
        )
        return {
            "order_id": payload["order_id"],
            "status": "compensated",
            "error": str(exc),
            "completed_steps": completed_steps,
            "compensations": compensation_results,
            "confirmation": _empty_activity("send_confirmation", "not_sent"),
            "audit": audit,
        }


@bp.activity_trigger(input_name="payload")
def reserve_inventory(payload: SagaInput) -> ActivityResult:
    logger.info(
        "Reserved inventory",
        extra={
            "order_id": payload["order_id"],
            "sku": payload["sku"],
            "quantity": payload["quantity"],
        },
    )
    return {
        "step": "reserve_inventory",
        "status": "reserved",
        "reservation_id": f"inv-{payload['order_id']}",
        "payment_id": "",
        "recipient": "",
        "db_url": "",
        "db_ready": False,
    }


@bp.activity_trigger(input_name="payload")
def charge_payment(payload: SagaInput) -> ActivityResult:
    if payload.get("fail_payment"):
        raise RuntimeError(f"Payment authorization failed for order {payload['order_id']}")

    logger.info(
        "Charged payment",
        extra={
            "order_id": payload["order_id"],
            "amount": payload["amount"],
            "currency": payload["currency"],
        },
    )
    return {
        "step": "charge_payment",
        "status": "captured",
        "reservation_id": "",
        "payment_id": f"pay-{payload['order_id']}",
        "recipient": "",
        "db_url": "",
        "db_ready": False,
    }


@bp.activity_trigger(input_name="payload")
def send_confirmation(payload: SagaInput) -> ActivityResult:
    if payload.get("fail_confirmation"):
        raise RuntimeError(f"Confirmation dispatch failed for order {payload['order_id']}")

    logger.info(
        "Sent confirmation",
        extra={
            "order_id": payload["order_id"],
            "email": payload["email"],
        },
    )
    return {
        "step": "send_confirmation",
        "status": "sent",
        "reservation_id": "",
        "payment_id": "",
        "recipient": payload["email"],
        "db_url": "",
        "db_ready": False,
    }


@bp.activity_trigger(input_name="payload")
def refund_payment(payload: dict[str, object]) -> ActivityResult:
    logger.warning(
        "Refunded payment",
        extra={
            "order_id": payload["order_id"],
            "payment_id": payload["payment_id"],
        },
    )
    return {
        "step": "refund_payment",
        "status": "refunded",
        "reservation_id": "",
        "payment_id": cast(str, payload["payment_id"]),
        "recipient": "",
        "db_url": "",
        "db_ready": False,
    }


@bp.activity_trigger(input_name="payload")
def release_inventory(payload: dict[str, object]) -> ActivityResult:
    logger.warning(
        "Released inventory",
        extra={
            "order_id": payload["order_id"],
            "reservation_id": payload["reservation_id"],
        },
    )
    return {
        "step": "release_inventory",
        "status": "released",
        "reservation_id": cast(str, payload["reservation_id"]),
        "payment_id": "",
        "recipient": "",
        "db_url": "",
        "db_ready": False,
    }


@bp.activity_trigger(input_name="payload")
def record_saga_audit(payload: AuditPayload) -> ActivityResult:
    db_url = os.getenv("DB_URL", "sqlite:///local-saga.db")
    logger.info(
        "Recorded saga audit event",
        extra={
            "order_id": payload["order_id"],
            "status": payload["status"],
            "db_url": db_url,
            "db_ready": _db_ready(),
        },
    )
    return {
        "step": "record_saga_audit",
        "status": payload["status"],
        "reservation_id": "",
        "payment_id": "",
        "recipient": "",
        "db_url": db_url,
        "db_ready": _db_ready(),
    }


app.register_functions(bp)
