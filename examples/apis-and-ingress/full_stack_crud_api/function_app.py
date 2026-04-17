from __future__ import annotations

# pyright: reportMissingImports=false, reportAttributeAccessIssue=false, reportUnknownVariableType=false, reportUnknownMemberType=false, reportUnknownParameterType=false, reportUntypedFunctionDecorator=false, reportUntypedBaseClass=false, reportExplicitAny=false, reportAny=false, reportUnknownArgumentType=false, reportUnusedParameter=false, reportImplicitRelativeImport=false

import os
from decimal import Decimal
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

import azure.functions as func
from azure_functions_db import EngineProvider
from azure_functions_db.core.config import DbConfig
from azure_functions_logging import get_logger, setup_logging
from azure_functions_openapi import openapi
from azure_functions_validation import validate_http
from pydantic import BaseModel, Field
from sqlalchemy import func as sql_func
from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from models import Base, Item

setup_logging(format="json")
logger = get_logger(__name__)

app = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)

DB_URL = os.getenv("DB_URL", "sqlite:///./items.db")
ENGINE_PROVIDER = EngineProvider()
ENGINE = ENGINE_PROVIDER.get_engine(
    DbConfig(
        connection_url=DB_URL,
        connect_args={"check_same_thread": False} if DB_URL.startswith("sqlite") else None,
    )
)
SessionLocal = sessionmaker(bind=ENGINE, autoflush=False, expire_on_commit=False, class_=Session)
Base.metadata.create_all(bind=ENGINE)


class PaginationQuery(BaseModel):
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)


class ItemCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    description: str = Field(min_length=1, max_length=2000)
    price: float = Field(ge=0)


class ItemUpdate(ItemCreate):
    pass


class ItemResponse(BaseModel):
    id: int
    name: str
    description: str
    price: float
    created_at: str
    updated_at: str


class ItemListResponse(BaseModel):
    page: int
    page_size: int
    total: int
    items: list[ItemResponse]
    next_link: str | None


def _json_response(
    payload: BaseModel | None = None, *, status_code: int = 200
) -> func.HttpResponse:
    return func.HttpResponse(
        body=None if payload is None else payload.model_dump_json(),
        status_code=status_code,
        mimetype="application/json" if payload is not None else None,
    )


def _serialize_item(item: Item) -> ItemResponse:
    return ItemResponse(
        id=item.id,
        name=item.name,
        description=item.description,
        price=float(item.price),
        created_at=item.created_at.isoformat(),
        updated_at=item.updated_at.isoformat(),
    )


def _get_item_or_none(session: Session, item_id: int) -> Item | None:
    return session.scalar(select(Item).where(Item.id == item_id))


def _build_next_link(req: func.HttpRequest, *, page: int, page_size: int, total: int) -> str | None:
    if page * page_size >= total:
        return None

    parsed = urlparse(req.url)
    query_params = dict(parse_qsl(parsed.query, keep_blank_values=True))
    query_params.update({"page": str(page + 1), "page_size": str(page_size)})
    return urlunparse(parsed._replace(query=urlencode(query_params)))


@app.route(route="items", methods=["GET"], auth_level=func.AuthLevel.ANONYMOUS)
@openapi(
    summary="List items with pagination",
    description="Returns a paginated item collection using toolkit validation, logging, and database helpers.",
    response={200: ItemListResponse},
    tags=["items"],
)
@validate_http(query=PaginationQuery, response_model=ItemListResponse)
def list_items(req: func.HttpRequest, query: PaginationQuery) -> func.HttpResponse:
    offset = (query.page - 1) * query.page_size

    with SessionLocal() as session:
        total = session.scalar(select(sql_func.count()).select_from(Item)) or 0
        rows = session.scalars(
            select(Item).order_by(Item.id.asc()).offset(offset).limit(query.page_size)
        ).all()

    payload = ItemListResponse(
        page=query.page,
        page_size=query.page_size,
        total=total,
        items=[_serialize_item(item) for item in rows],
        next_link=_build_next_link(req, page=query.page, page_size=query.page_size, total=total),
    )
    logger.info(
        "Listed items.",
        extra={
            "operation": "list_items",
            "page": query.page,
            "page_size": query.page_size,
            "returned": len(rows),
            "total": total,
        },
    )
    return _json_response(payload)


@app.route(route="items/{id:int}", methods=["GET"], auth_level=func.AuthLevel.ANONYMOUS)
@openapi(
    summary="Get item by id",
    description="Loads a single item from the shared SQLAlchemy session.",
    response={200: ItemResponse},
    tags=["items"],
)
def get_item(req: func.HttpRequest) -> func.HttpResponse:
    item_id = int(req.route_params["id"])

    with SessionLocal() as session:
        item = _get_item_or_none(session, item_id)

    if item is None:
        logger.info("Item not found.", extra={"operation": "get_item", "item_id": item_id})
        return func.HttpResponse(status_code=404)

    logger.info("Fetched item.", extra={"operation": "get_item", "item_id": item_id})
    return _json_response(_serialize_item(item))


@app.route(route="items", methods=["POST"], auth_level=func.AuthLevel.ANONYMOUS)
@openapi(
    summary="Create item",
    description="Creates an item after body validation succeeds.",
    request_body=ItemCreate,
    response={201: ItemResponse},
    tags=["items"],
)
@validate_http(body=ItemCreate, response_model=ItemResponse)
def create_item(req: func.HttpRequest, body: ItemCreate) -> func.HttpResponse:
    record = Item(
        name=body.name,
        description=body.description,
        price=Decimal(str(body.price)),
    )

    with SessionLocal() as session:
        session.add(record)
        session.commit()
        session.refresh(record)

    payload = _serialize_item(record)
    logger.info(
        "Created item.",
        extra={"operation": "create_item", "item_id": record.id, "request_url": req.url},
    )
    return _json_response(payload, status_code=201)


@app.route(route="items/{id:int}", methods=["PUT"], auth_level=func.AuthLevel.ANONYMOUS)
@openapi(
    summary="Update item",
    description="Replaces an existing item with the validated request body.",
    request_body=ItemUpdate,
    response={200: ItemResponse},
    tags=["items"],
)
@validate_http(body=ItemUpdate, response_model=ItemResponse)
def update_item(req: func.HttpRequest, body: ItemUpdate) -> func.HttpResponse:
    item_id = int(req.route_params["id"])

    with SessionLocal() as session:
        item = _get_item_or_none(session, item_id)
        if item is None:
            logger.info("Item not found.", extra={"operation": "update_item", "item_id": item_id})
            return func.HttpResponse(status_code=404)

        item.name = body.name
        item.description = body.description
        item.price = Decimal(str(body.price))
        session.add(item)
        session.commit()
        session.refresh(item)

    logger.info("Updated item.", extra={"operation": "update_item", "item_id": item_id})
    return _json_response(_serialize_item(item))


@app.route(route="items/{id:int}", methods=["DELETE"], auth_level=func.AuthLevel.ANONYMOUS)
@openapi(
    summary="Delete item",
    description="Deletes an existing item and returns no content.",
    response={204: None},
    tags=["items"],
)
def delete_item(req: func.HttpRequest) -> func.HttpResponse:
    item_id = int(req.route_params["id"])

    with SessionLocal() as session:
        item = _get_item_or_none(session, item_id)
        if item is None:
            logger.info("Item not found.", extra={"operation": "delete_item", "item_id": item_id})
            return func.HttpResponse(status_code=404)

        session.delete(item)
        session.commit()

    logger.info("Deleted item.", extra={"operation": "delete_item", "item_id": item_id})
    return func.HttpResponse(status_code=204)
