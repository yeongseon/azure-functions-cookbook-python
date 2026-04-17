# pyright: reportMissingImports=false, reportUnknownVariableType=false, reportUnknownMemberType=false, reportUnknownParameterType=false, reportUnknownArgumentType=false, reportUntypedBaseClass=false, reportUntypedFunctionDecorator=false, reportAny=false, reportMissingTypeArgument=false

from __future__ import annotations

import base64
import json
import os

import azure.functions as func
from azure_functions_db import DbBindings, DbReader
from azure_functions_logging import get_logger, setup_logging, with_context
from azure_functions_openapi import openapi
from azure_functions_validation import validate_http
from pydantic import BaseModel, Field

setup_logging(format="json")
logger = get_logger(__name__)

app = func.FunctionApp(http_auth_level=func.AuthLevel.FUNCTION)
db = DbBindings()


class TenantInvoiceQuery(BaseModel):
    customer_id: str | None = None
    status: str | None = None
    limit: int = Field(default=20, ge=1, le=100)


class TenantInvoice(BaseModel):
    invoice_id: str
    customer_id: str
    status: str
    amount: float


class TenantInvoiceListResponse(BaseModel):
    tenant_id: str
    count: int
    items: list[TenantInvoice]


def _decode_jwt_without_validation(token: str) -> dict:
    parts = token.split(".")
    if len(parts) != 3:
        return {}

    payload = parts[1]
    padding = "=" * (-len(payload) % 4)
    try:
        decoded = base64.urlsafe_b64decode(payload + padding)
        return json.loads(decoded.decode("utf-8"))
    except (ValueError, json.JSONDecodeError):
        return {}


def _normalize_tenant_key(tenant_id: str) -> str:
    return tenant_id.strip().upper().replace("-", "_")


def resolve_tenant_id(req: func.HttpRequest) -> str:
    tenant_id = req.headers.get("X-Tenant-ID", "").strip()
    if tenant_id:
        return tenant_id

    authorization = req.headers.get("Authorization", "")
    if authorization.lower().startswith("bearer "):
        claims = _decode_jwt_without_validation(authorization.split(" ", 1)[1].strip())
        tenant_id = str(claims.get("tid") or claims.get("tenant_id") or "").strip()
        if tenant_id:
            return tenant_id

    raise ValueError("Tenant context is missing. Provide X-Tenant-ID or a bearer token with tid.")


def resolve_tenant_db_url(req: func.HttpRequest) -> str:
    tenant_id = resolve_tenant_id(req)
    setting_name = f"TENANT_{_normalize_tenant_key(tenant_id)}_DB_URL"
    db_url = os.getenv(setting_name, "").strip()
    if not db_url:
        raise ValueError(
            f"No DB mapping configured for tenant '{tenant_id}'. Expected setting '{setting_name}'."
        )
    return db_url


@app.route(route="tenant/invoices/query", methods=["POST"])
@with_context
@openapi(
    summary="Query invoices from a tenant-isolated database",
    request_body=TenantInvoiceQuery,
    response={200: TenantInvoiceListResponse},
    tags=["security", "tenancy", "db"],
)
@validate_http(body=TenantInvoiceQuery, response_model=TenantInvoiceListResponse)
@db.input("reader", url=resolve_tenant_db_url, table="invoices")
def query_tenant_invoices(
    req: func.HttpRequest,
    body: TenantInvoiceQuery,
    reader: DbReader,
) -> func.HttpResponse:
    try:
        tenant_id = resolve_tenant_id(req)
    except ValueError as exc:
        logger.warning("Rejected request without tenant context", extra={"reason": str(exc)})
        return func.HttpResponse(
            body=json.dumps({"error": str(exc)}),
            status_code=400,
            mimetype="application/json",
        )

    try:
        rows = [dict(row) for row in reader.fetch_all()]
    except ValueError as exc:
        logger.warning(
            "Rejected request for unmapped tenant",
            extra={"tenant_id": tenant_id, "reason": str(exc)},
        )
        return func.HttpResponse(
            body=json.dumps({"error": str(exc), "tenant_id": tenant_id}),
            status_code=404,
            mimetype="application/json",
        )

    filtered_rows = [
        row
        for row in rows
        if (body.customer_id is None or row.get("customer_id") == body.customer_id)
        and (body.status is None or row.get("status") == body.status)
    ][: body.limit]

    response = TenantInvoiceListResponse(
        tenant_id=tenant_id,
        count=len(filtered_rows),
        items=[TenantInvoice(**row) for row in filtered_rows],
    )
    logger.info(
        "Queried tenant invoices",
        extra={"tenant_id": tenant_id, "count": response.count, "limit": body.limit},
    )
    return func.HttpResponse(
        body=response.model_dump_json(),
        mimetype="application/json",
        status_code=200,
    )
