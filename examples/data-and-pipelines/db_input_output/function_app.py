import azure.functions as func
from azure_functions_db import DbBindings, DbOut, DbReader
from azure_functions_logging import setup_logging, with_context, get_logger
from azure_functions_validation import validate_http
from azure_functions_openapi import openapi
from pydantic import BaseModel

setup_logging(format="json")
logger = get_logger(__name__)

db = DbBindings()
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
@db.input("reader", url="%DB_URL%", table="items")
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
    import uuid

    item_id = str(uuid.uuid4())
    record = {"id": item_id, **body.model_dump()}
    out.set(record)
    logger.info("Created item", extra={"item_id": item_id})
    return func.HttpResponse(
        body=ItemResponse(id=item_id, **body.model_dump()).model_dump_json(),
        status_code=201,
        mimetype="application/json",
    )
