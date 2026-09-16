from __future__ import annotations

from collections.abc import Callable

# pyright: reportMissingImports=false, reportUntypedFunctionDecorator=false, reportUnknownVariableType=false, reportUnknownMemberType=false, reportUnknownParameterType=false
from functools import wraps

import azure.functions as func
from azure_functions_logging import get_logger, setup_logging
from azure_functions_openapi import openapi
from pydantic import BaseModel, Field

setup_logging(format="json")
logger = get_logger(__name__)

app = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)


class GreetingResponse(BaseModel):
    """Response body whose schema is inferred from the return annotation."""

    message: str = Field(description="Human-readable greeting.")
    source: str = Field(description="Where the OpenAPI 200 schema came from.")


def serialize(
    handler: Callable[[func.HttpRequest], BaseModel],
) -> Callable[[func.HttpRequest], func.HttpResponse]:
    """Adapt a model-returning handler into a real ``HttpResponse``.

    Return-type inference lets ``@openapi`` read the 200 schema straight from
    the handler's ``-> GreetingResponse`` annotation, but the Azure Functions
    worker only serializes ``str``/``bytes``. This tiny adapter bridges the two:
    the handler stays annotated with the Pydantic model (so inference works),
    while the wrapper turns the returned model into JSON at runtime.
    """

    @wraps(handler)
    def wrapper(req: func.HttpRequest) -> func.HttpResponse:
        return func.HttpResponse(
            handler(req).model_dump_json(),
            status_code=200,
            mimetype="application/json",
        )

    return wrapper


@app.route(route="openapi/inference/greeting", methods=["GET"])
@serialize
@openapi(
    summary="Return-type inference demo",
    description="The 200 response schema is inferred from the return annotation.",
    route="/api/openapi/inference/greeting",
    method="get",
    tags=["openapi-inference"],
)
def inferred_greeting(req: func.HttpRequest) -> GreetingResponse:
    name = req.params.get("name", "Azure Functions")
    logger.info("Handled inference greeting.", extra={"name": name})
    return GreetingResponse(message=f"Hello, {name}!", source="return_annotation")
