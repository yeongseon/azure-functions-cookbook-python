from __future__ import annotations

# pyright: reportMissingImports=false, reportAttributeAccessIssue=false, reportUnknownVariableType=false, reportUnknownMemberType=false, reportUnknownParameterType=false, reportUntypedFunctionDecorator=false, reportUntypedBaseClass=false, reportExplicitAny=false, reportAny=false, reportUnknownArgumentType=false, reportUnusedParameter=false

import json
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any

import azure.functions as func
from azure_functions_db import DbBindings, DbOut, DbReader
from azure_functions_logging import get_logger, setup_logging, with_context
from azure_functions_openapi import openapi
from azure_functions_validation import validate_http
from pydantic import BaseModel, Field

setup_logging(format="json")
logger = get_logger(__name__)

app = func.FunctionApp(http_auth_level=func.AuthLevel.FUNCTION)
db = DbBindings()


class OrderLine(BaseModel):
    sku: str
    quantity: int = Field(ge=1)
    unit_price: float = Field(ge=0)


class OrderWriteRequest(BaseModel):
    id: str
    customer_id: str
    status: str = "pending"
    items: list[OrderLine]


class OrderAccepted(BaseModel):
    id: str
    status: str


class OrderProjection(BaseModel):
    id: str
    customer_id: str
    status: str
    item_count: int
    total_amount: float
    updated_at: str


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _build_order_document(body: OrderWriteRequest) -> dict[str, Any]:
    return {
        "id": body.id,
        "customer_id": body.customer_id,
        "status": body.status,
        "items": [item.model_dump() for item in body.items],
        "updated_at": _utc_now_iso(),
        "entity_type": "order",
    }


def _build_projection(document: dict[str, Any]) -> dict[str, Any]:
    items = document.get("items", [])
    total_amount = sum(
        Decimal(str(item.get("quantity", 0))) * Decimal(str(item.get("unit_price", 0)))
        for item in items
    )
    item_count = sum(int(item.get("quantity", 0)) for item in items)
    return {
        "id": str(document.get("id", "unknown-order")),
        "customer_id": str(document.get("customer_id", "unknown-customer")),
        "status": str(document.get("status", "pending")),
        "item_count": item_count,
        "total_amount": float(total_amount),
        "updated_at": str(document.get("updated_at", _utc_now_iso())),
    }


@app.route(route="orders", methods=["POST"])
@with_context
@openapi(
    summary="Create order",
    request_body=OrderWriteRequest,
    response={202: OrderAccepted},
    tags=["orders"],
)
@validate_http(body=OrderWriteRequest, response_model=OrderAccepted)
@app.cosmos_db_output(
    arg_name="order_doc",
    database_name="ordersdb",
    container_name="orders",
    connection="CosmosDBConnection",
)
def create_order(
    req: func.HttpRequest,
    body: OrderWriteRequest,
    order_doc: func.Out[str],
) -> func.HttpResponse:
    document = _build_order_document(body)
    order_doc.set(json.dumps(document))

    logger.info(
        "Accepted order write.",
        extra={"order_id": document["id"], "customer_id": document["customer_id"]},
    )
    return func.HttpResponse(
        body=OrderAccepted(id=document["id"], status="accepted").model_dump_json(),
        status_code=202,
        mimetype="application/json",
    )


@app.cosmos_db_trigger(
    arg_name="documents",
    database_name="ordersdb",
    container_name="orders",
    connection="CosmosDBConnection",
    lease_container_name="leases",
    create_lease_container_if_not_exists=True,
)
@db.output("projection_out", url="%READ_DB_URL%", table="order_read_models")
def project_order_read_models(
    documents: list[dict[str, Any]],
    projection_out: DbOut,
) -> None:
    if not documents:
        logger.info("No changed documents found in this batch.")
        return

    logger.info("Projecting changed documents.", extra={"count": len(documents)})
    projections = [_build_projection(document) for document in documents]
    projection_out.set(projections)

    for projection in projections:
        logger.info(
            "Upserted order read model.",
            extra={
                "order_id": projection["id"],
                "customer_id": projection["customer_id"],
                "total_amount": projection["total_amount"],
            },
        )


@app.route(route="orders/{id}/projection", methods=["GET"])
@with_context
@openapi(summary="Get order projection", response={200: OrderProjection}, tags=["orders"])
@db.input("reader", url="%READ_DB_URL%", table="order_read_models")
def get_order_projection(req: func.HttpRequest, reader: DbReader) -> func.HttpResponse:
    order_id = req.route_params["id"]
    rows = [dict(row) for row in reader.fetch_all()]
    match = next((row for row in rows if str(row.get("id")) == order_id), None)

    if match is None:
        return func.HttpResponse("Not found", status_code=404)

    logger.info("Read projected order.", extra={"order_id": order_id})
    return func.HttpResponse(
        body=OrderProjection(**match).model_dump_json(),
        mimetype="application/json",
    )
