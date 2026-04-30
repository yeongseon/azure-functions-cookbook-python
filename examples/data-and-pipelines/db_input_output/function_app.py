from __future__ import annotations

import logging
import uuid
from typing import Any

import azure.functions as func
from pydantic import BaseModel

try:
    from azure_functions_db import DbBindings, DbOut, DbReader

    db: Any = DbBindings()
    _db_available = True
except ImportError:
    db = None
    _db_available = False
    DbReader = Any  # type: ignore[assignment,misc]
    DbOut = Any  # type: ignore[assignment,misc]

try:
    from azure_functions_logging import get_logger, setup_logging, with_context

    setup_logging(format="json")
    logger = get_logger(__name__)
except ImportError:
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)  # type: ignore[assignment]

    def with_context(fn: Any) -> Any:  # type: ignore[misc]
        return fn


try:
    from azure_functions_validation import validate_http
except ImportError:

    def validate_http(**kwargs: Any) -> Any:  # type: ignore[misc]
        def decorator(fn: Any) -> Any:
            return fn

        return decorator


try:
    from azure_functions_openapi import openapi
except ImportError:

    def openapi(**kwargs: Any) -> Any:  # type: ignore[misc]
        def decorator(fn: Any) -> Any:
            return fn

        return decorator


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
    @openapi(summary="List items", response={200: list[ItemResponse]}, tags=["items"])
    @db.inject_reader("reader", url="%DB_URL%", table="items")
    def list_items(req: func.HttpRequest, reader: DbReader) -> func.HttpResponse:
        rows = reader.fetch_all()
        logger.info("Listed items", extra={"count": len(rows)})
        return func.HttpResponse(
            body=str([dict(r) for r in rows]),
            mimetype="application/json",
        )

    @app.route(route="items", methods=["POST"])
    @with_context
    @openapi(
        summary="Create item",
        request_body=ItemCreate,
        response={201: ItemResponse},
        tags=["items"],
    )
    @validate_http(body=ItemCreate, response_model=ItemResponse)
    @db.output("out", url="%DB_URL%", table="items")
    def create_item(req: func.HttpRequest, body: ItemCreate, out: DbOut) -> func.HttpResponse:
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
    def list_items(req: func.HttpRequest) -> func.HttpResponse:  # type: ignore[misc]
        logger.warning("azure-functions-db not installed; returning empty list")
        return func.HttpResponse(body="[]", mimetype="application/json")

    @app.route(route="items", methods=["POST"])
    @with_context
    def create_item(req: func.HttpRequest) -> func.HttpResponse:  # type: ignore[misc]
        logger.warning("azure-functions-db not installed; item not persisted")
        return func.HttpResponse(
            body='{"error": "db not available"}',
            status_code=503,
            mimetype="application/json",
        )
