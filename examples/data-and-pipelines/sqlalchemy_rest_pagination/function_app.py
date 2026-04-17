from __future__ import annotations

# pyright: reportMissingImports=false, reportAttributeAccessIssue=false, reportUnknownVariableType=false, reportUnknownMemberType=false, reportUnknownParameterType=false, reportUntypedFunctionDecorator=false, reportUntypedBaseClass=false, reportExplicitAny=false, reportAny=false, reportUnknownArgumentType=false, reportUnusedParameter=false, reportImplicitRelativeImport=false

import os
from decimal import Decimal
from urllib.parse import urlencode, urlparse, urlunparse

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

app = func.FunctionApp(http_auth_level=func.AuthLevel.FUNCTION)

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
    price: float = Field(ge=0)


class ItemResponse(BaseModel):
    id: int
    name: str
    price: float
    created_at: str


class PaginatedItemsResponse(BaseModel):
    page: int
    page_size: int
    total: int
    items: list[ItemResponse]
    next_link: str | None


def _serialize_item(item: Item) -> ItemResponse:
    return ItemResponse(
        id=item.id,
        name=item.name,
        price=float(item.price),
        created_at=item.created_at.isoformat(),
    )


def _build_next_link(req: func.HttpRequest, *, page: int, page_size: int, total: int) -> str | None:
    if page * page_size >= total:
        return None

    parsed = urlparse(req.url)
    query_string = urlencode({"page": page + 1, "page_size": page_size})
    return urlunparse(parsed._replace(query=query_string))


@app.route(route="items", methods=["GET"])
@openapi(
    summary="List items with pagination", response={200: PaginatedItemsResponse}, tags=["items"]
)
@validate_http(query=PaginationQuery, response_model=PaginatedItemsResponse)
def list_items(req: func.HttpRequest, query: PaginationQuery) -> func.HttpResponse:
    offset = (query.page - 1) * query.page_size

    with SessionLocal() as session:
        total = session.scalar(select(sql_func.count()).select_from(Item)) or 0
        rows = session.scalars(
            select(Item).order_by(Item.id.asc()).offset(offset).limit(query.page_size)
        ).all()

    payload = PaginatedItemsResponse(
        page=query.page,
        page_size=query.page_size,
        total=total,
        items=[_serialize_item(item) for item in rows],
        next_link=_build_next_link(req, page=query.page, page_size=query.page_size, total=total),
    )
    logger.info(
        "Listed paginated items.",
        extra={
            "page": query.page,
            "page_size": query.page_size,
            "returned": len(rows),
            "total": total,
        },
    )
    return func.HttpResponse(payload.model_dump_json(), mimetype="application/json")


@app.route(route="items", methods=["POST"])
@openapi(
    summary="Create item", request_body=ItemCreate, response={201: ItemResponse}, tags=["items"]
)
@validate_http(body=ItemCreate, response_model=ItemResponse)
def create_item(req: func.HttpRequest, body: ItemCreate) -> func.HttpResponse:
    record = Item(name=body.name, price=Decimal(str(body.price)))

    with SessionLocal() as session:
        session.add(record)
        session.commit()
        session.refresh(record)

    payload = _serialize_item(record)
    logger.info(
        "Created item.",
        extra={"item_id": record.id, "name": record.name, "request_url": req.url},
    )
    return func.HttpResponse(
        payload.model_dump_json(), status_code=201, mimetype="application/json"
    )
