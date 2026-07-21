from __future__ import annotations

import json

import azure.functions as func

try:
    from pydantic import BaseModel, Field
except ImportError:

    class BaseModel:
        def __init__(self, **kwargs: object) -> None:
            for key, value in kwargs.items():
                setattr(self, key, value)

        def model_dump(self) -> dict[str, object]:
            return self.__dict__.copy()

    def Field(default: object = None, **_: object) -> object:
        return default


from azure_functions_logging import get_logger, setup_logging, with_context
from azure_functions_openapi import openapi
from azure_functions_validation import validate_http

setup_logging(format="json")
logger = get_logger(__name__)
app = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)


class CatalogPath(BaseModel):
    item_id: str = Field(..., description="Catalog item identifier")


class CatalogResponse(BaseModel):
    item_id: str
    routed_by: str
    correlation_id: str
    cache_status: str


@app.route(route="catalog/{item_id}", methods=["GET"])
@with_context
@openapi(
    summary="APIM-backed function backend",
    tags=["Ingress"],
    route="/api/catalog/{item_id}",
    method="get",
)
@validate_http(path=CatalogPath, response_model=CatalogResponse)
def get_catalog_item(req: func.HttpRequest, path: CatalogPath) -> CatalogResponse:
    response = CatalogResponse(
        item_id=path.item_id,
        routed_by=req.headers.get("x-apim-gateway", "azure-api-management"),
        correlation_id=req.headers.get("x-correlation-id", "local-correlation"),
        cache_status=req.headers.get("x-apim-cache", "bypass"),
    )
    logger.info("Handled APIM backend request", extra=response.model_dump())
    return response


@app.route(route="catalog/health", methods=["GET"])
@with_context
def health(req: func.HttpRequest) -> func.HttpResponse:
    return func.HttpResponse(
        body=json.dumps({"status": "ok", "backend": "functions"}), mimetype="application/json"
    )
