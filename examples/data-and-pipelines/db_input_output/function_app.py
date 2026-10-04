from __future__ import annotations

import uuid
from typing import Any

import azure.functions as func
from azure_functions_db import DbBindings, DbOut, DbReader
from azure_functions_logging import get_logger, setup_logging, with_context
from azure_functions_openapi import openapi
from azure_functions_validation import validate_http
from pydantic import BaseModel

db: Any = DbBindings()
_db_available = True
setup_logging(format="json")
logger = get_logger(__name__)


app = func.FunctionApp(http_auth_level=func.AuthLevel.FUNCTION)


class ItemCreate(BaseModel):
    name: str
    category: str
    price: float


class ItemResponse(BaseModel):
    id: str
    name: str
    category: str
    price: float


if _db_available:

    @app.route(route="items", methods=["GET"])
    @with_context
    @openapi(
        summary="List items",
        responses={
            200: {
                "description": "Successful Response",
                "content": {
                    "application/json": {
                        "schema": {
                            "type": "array",
                            "items": ItemResponse.model_json_schema(
                                ref_template="#/components/schemas/{model}"
                            ),
                        }
                    }
                },
            }
        },
        tags=["items"],
    )
    @db.inject_reader("reader", url="%DB_URL%", table="items")
    def list_items(
        req: func.HttpRequest, reader: DbReader, context: func.Context
    ) -> func.HttpResponse:
        rows = reader.fetch_all()
        logger.info("Listed items", extra={"count": len(rows)})
        return func.HttpResponse(
            body=str([dict(r) for r in rows]),
            mimetype="application/json",
        )

    @app.route(route="items", methods=["POST"])
    @openapi(
        summary="Create item",
        requests=ItemCreate,
        responses={201: ItemResponse},
        tags=["items"],
    )
    @db.output("out", url="%DB_URL%", table="items")
    @with_context(param="invocation_context")
    @validate_http(body=ItemCreate, response_model=ItemResponse)
    def create_item(
        req: func.HttpRequest, body: ItemCreate, out: DbOut, invocation_context: func.Context
    ) -> func.HttpResponse:
        item_id = str(uuid.uuid4())
        out.set({"id": item_id, **body.model_dump()})
        logger.info("Created item", extra={"item_id": item_id})
        return func.HttpResponse(
            body=ItemResponse(id=item_id, **body.model_dump()).model_dump_json(),
            status_code=201,
            mimetype="application/json",
        )

else:

    @app.route(route="items", methods=["GET"])
    @with_context
    def list_items(req: func.HttpRequest, context: func.Context) -> func.HttpResponse:  # type: ignore[misc]
        logger.warning("azure-functions-db not installed; returning empty list")
        return func.HttpResponse(body="[]", mimetype="application/json")

    @app.route(route="items", methods=["POST"])
    @with_context
    def create_item(req: func.HttpRequest, context: func.Context) -> func.HttpResponse:  # type: ignore[misc]
        logger.warning("azure-functions-db not installed; item not persisted")
        return func.HttpResponse(
            body='{"error": "db not available"}',
            status_code=503,
            mimetype="application/json",
        )
