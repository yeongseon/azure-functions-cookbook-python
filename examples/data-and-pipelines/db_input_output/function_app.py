from __future__ import annotations

import logging
import uuid
from typing import Any

import azure.functions as func
from pydantic import BaseModel

try:
    from azure_functions_db import DbBindings, DbOut, DbReader

    db = DbBindings()
except ImportError:
    db = None  # type: ignore[assignment]
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


@app.route(route="items", methods=["GET"])
@with_context
@openapi(summary="List items", response={200: list[ItemResponse]}, tags=["items"])
def list_items(req: func.HttpRequest) -> func.HttpResponse:
    if db is not None:
        try:
            reader = db.inject_reader(url="%DB_URL%", table="items")
            rows = reader.fetch_all()
        except Exception:
            rows = []
    else:
        rows = []
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
def create_item(req: func.HttpRequest, body: ItemCreate) -> func.HttpResponse:
    item_id = str(uuid.uuid4())
    if db is not None:
        try:
            out: Any = db.inject_writer(url="%DB_URL%", table="items")
            out.set({"id": item_id, **body.model_dump()})
        except Exception:
            pass
    logger.info("Created item", extra={"item_id": item_id})
    return func.HttpResponse(
        body=ItemResponse(id=item_id, **body.model_dump()).model_dump_json(),
        status_code=201,
        mimetype="application/json",
    )
