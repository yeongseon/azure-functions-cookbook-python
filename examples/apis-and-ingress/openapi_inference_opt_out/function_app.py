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
    message: str = Field(description="Human-readable greeting.")
    source: str = Field(description="Whether return-type inference was enabled.")


def serialize(
    handler: Callable[[func.HttpRequest], BaseModel],
) -> Callable[[func.HttpRequest], func.HttpResponse]:
    @wraps(handler)
    def wrapper(req: func.HttpRequest) -> func.HttpResponse:
        return func.HttpResponse(
            handler(req).model_dump_json(),
            status_code=200,
            mimetype="application/json",
        )

    return wrapper


@app.route(route="openapi/inference/default", methods=["GET"])
@serialize
@openapi(
    summary="Default return-type inference",
    description="The return annotation produces the OpenAPI 200 response schema.",
    route="/api/openapi/inference/default",
    method="get",
    tags=["openapi-inference-opt-out"],
)
def inferred_greeting(req: func.HttpRequest) -> GreetingResponse:
    name = req.params.get("name", "Azure Functions")
    logger.info("Handled inferred greeting.", extra={"name": name})
    return GreetingResponse(message=f"Hello, {name}!", source="return_annotation")


@app.route(route="openapi/inference/opt-out", methods=["GET"])
@serialize
@openapi(
    summary="Return-type inference disabled",
    description="The internal return annotation is omitted from the OpenAPI response contract.",
    route="/api/openapi/inference/opt-out",
    method="get",
    tags=["openapi-inference-opt-out"],
    infer_return_types=False,
)
def opted_out_greeting(req: func.HttpRequest) -> GreetingResponse:
    name = req.params.get("name", "Azure Functions")
    logger.info("Handled opted-out greeting.", extra={"name": name})
    return GreetingResponse(message=f"Hello, {name}!", source="inference_disabled")
