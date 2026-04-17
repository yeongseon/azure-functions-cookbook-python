# pyright: reportMissingImports=false, reportUnknownMemberType=false, reportUnknownVariableType=false, reportUnknownParameterType=false, reportUnknownArgumentType=false, reportAny=false, reportExplicitAny=false, reportUntypedFunctionDecorator=false, reportUnusedParameter=false

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from functools import lru_cache
from typing import Any

import azure.functions as func
from azure.cosmos import CosmosClient, exceptions
from azure_functions_db import DbBindings, DbOut
from azure_functions_logging import get_logger, setup_logging

setup_logging(format="json")
logger = get_logger(__name__)

app = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)
db = DbBindings()

COSMOS_DB_ENDPOINT = os.getenv("COSMOS_DB_ENDPOINT", "https://localhost:8081")
COSMOS_DB_KEY = os.getenv("COSMOS_DB_KEY", "C2y6yDjf5/R+ob0N8A7Cgv30VRDJIWEHLM+FDw==")
COSMOS_DB_DATABASE_NAME = os.getenv("COSMOS_DB_DATABASE_NAME", "outboxdb")
COSMOS_DB_CONTAINER_NAME = os.getenv("COSMOS_DB_CONTAINER_NAME", "orders")
BROKER_NAME = os.getenv("OUTBOX_BROKER_NAME", "log-broker")
OUTBOX_EVENT_TTL_SECONDS = int(os.getenv("OUTBOX_EVENT_TTL_SECONDS", "86400"))


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _json_response(payload: dict[str, Any], status_code: int) -> func.HttpResponse:
    return func.HttpResponse(
        body=json.dumps(payload, indent=2),
        status_code=status_code,
        mimetype="application/json",
    )


def _parse_order_payload(req: func.HttpRequest) -> dict[str, Any]:
    try:
        payload = req.get_json()
    except ValueError as exc:
        raise ValueError("Request body must be valid JSON.") from exc

    order_id = str(payload.get("id", "")).strip()
    customer_id = str(payload.get("customer_id", "")).strip()
    amount_raw = payload.get("amount")

    if not order_id:
        raise ValueError("Field 'id' is required.")
    if not customer_id:
        raise ValueError("Field 'customer_id' is required.")

    try:
        amount = Decimal(str(amount_raw))
    except (InvalidOperation, TypeError) as exc:
        raise ValueError("Field 'amount' must be numeric.") from exc

    if amount < 0:
        raise ValueError("Field 'amount' must be zero or greater.")

    return {
        "id": order_id,
        "customer_id": customer_id,
        "amount": float(amount),
        "currency": str(payload.get("currency", "USD")).strip() or "USD",
        "status": str(payload.get("status", "accepted")).strip() or "accepted",
    }


def _build_order_document(payload: dict[str, Any]) -> dict[str, Any]:
    partition_key = payload["id"]
    created_at = _utc_now_iso()
    return {
        "id": payload["id"],
        "partitionKey": partition_key,
        "type": "order",
        "customer_id": payload["customer_id"],
        "amount": payload["amount"],
        "currency": payload["currency"],
        "status": payload["status"],
        "created_at": created_at,
    }


def _build_outbox_document(order_document: dict[str, Any]) -> dict[str, Any]:
    event_id = f"evt-{order_document['id']}-created"
    created_at = _utc_now_iso()
    return {
        "id": event_id,
        "partitionKey": order_document["partitionKey"],
        "type": "outbox",
        "aggregate_id": order_document["id"],
        "aggregate_type": "order",
        "event_type": "OrderCreated",
        "status": "pending",
        "created_at": created_at,
        "ttl": OUTBOX_EVENT_TTL_SECONDS,
        "payload": {
            "id": order_document["id"],
            "customer_id": order_document["customer_id"],
            "amount": order_document["amount"],
            "currency": order_document["currency"],
            "status": order_document["status"],
        },
    }


@lru_cache(maxsize=1)
def _get_container() -> Any:
    client = CosmosClient(COSMOS_DB_ENDPOINT, credential=COSMOS_DB_KEY)
    database = client.get_database_client(COSMOS_DB_DATABASE_NAME)
    return database.get_container_client(COSMOS_DB_CONTAINER_NAME)


def _store_order_and_outbox(
    order_document: dict[str, Any], outbox_document: dict[str, Any]
) -> None:
    container = _get_container()
    operations = [
        ("create", (order_document,)),
        ("create", (outbox_document,)),
    ]
    container.execute_item_batch(
        batch_operations=operations,
        partition_key=order_document["partitionKey"],
    )


def _publish_to_broker(outbox_document: dict[str, Any]) -> dict[str, str]:
    logger.info(
        "Relayed outbox event to broker boundary.",
        extra={
            "event_id": outbox_document["id"],
            "aggregate_id": outbox_document["aggregate_id"],
            "event_type": outbox_document["event_type"],
            "broker": BROKER_NAME,
        },
    )
    return {
        "broker_name": BROKER_NAME,
        "status": "published",
        "dispatched_at": _utc_now_iso(),
    }


def _build_dispatch_record(
    outbox_document: dict[str, Any], broker_result: dict[str, str]
) -> dict[str, str]:
    return {
        "event_id": outbox_document["id"],
        "aggregate_id": outbox_document["aggregate_id"],
        "event_type": outbox_document["event_type"],
        "broker_name": broker_result["broker_name"],
        "dispatched_at": broker_result["dispatched_at"],
        "status": broker_result["status"],
    }


@app.route(route="outbox/orders", methods=["POST"])
def create_order(req: func.HttpRequest) -> func.HttpResponse:
    try:
        payload = _parse_order_payload(req)
        order_document = _build_order_document(payload)
        outbox_document = _build_outbox_document(order_document)
        _store_order_and_outbox(order_document, outbox_document)
    except ValueError as exc:
        return _json_response({"message": str(exc)}, status_code=400)
    except exceptions.CosmosBatchOperationError as exc:
        logger.exception("Transactional batch failed.")
        return _json_response(
            {
                "message": "Failed to store order and outbox event atomically.",
                "error_index": exc.error_index,
            },
            status_code=500,
        )
    except exceptions.CosmosHttpResponseError:
        logger.exception("Cosmos DB request failed.")
        return _json_response(
            {"message": "Cosmos DB request failed while storing the order."},
            status_code=500,
        )

    logger.info(
        "Accepted order and stored outbox event in one transactional batch.",
        extra={"order_id": order_document["id"], "event_id": outbox_document["id"]},
    )
    return _json_response(
        {
            "order_id": order_document["id"],
            "event_id": outbox_document["id"],
            "status": "accepted",
        },
        status_code=202,
    )


@app.cosmos_db_trigger(
    arg_name="documents",
    database_name="%COSMOS_DB_DATABASE_NAME%",
    container_name="%COSMOS_DB_CONTAINER_NAME%",
    connection="CosmosDBConnection",
    lease_container_name="leases",
    create_lease_container_if_not_exists=True,
)
@db.output("dispatch_out", url="%DISPATCH_DB_URL%", table="outbox_dispatches")
def relay_outbox_events(documents: list[dict[str, Any]], dispatch_out: DbOut) -> None:
    if not documents:
        logger.info("No changed documents found in this change feed batch.")
        return

    logger.info("Received changed documents from Cosmos DB.", extra={"count": len(documents)})
    dispatches: list[dict[str, str]] = []

    for document in documents:
        if document.get("type") != "outbox":
            continue

        broker_result = _publish_to_broker(document)
        dispatches.append(_build_dispatch_record(document, broker_result))

    if not dispatches:
        logger.info("No outbox documents found in this change feed batch.")
        return

    dispatch_out.set(dispatches)
    logger.info("Recorded dispatch audit rows.", extra={"count": len(dispatches)})
