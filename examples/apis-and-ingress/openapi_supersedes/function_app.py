from __future__ import annotations

# pyright: reportMissingImports=false, reportUntypedFunctionDecorator=false, reportUnknownVariableType=false, reportUnknownMemberType=false, reportUnknownParameterType=false
import azure.functions as func
from azure_functions_logging import get_logger, setup_logging
from azure_functions_openapi import openapi
from azure_functions_validation import validate_http
from pydantic import BaseModel, Field

setup_logging(format="json")
logger = get_logger(__name__)

app = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)


class InferredGreetingResponse(BaseModel):
    """What return-type inference alone would produce for the 200 schema."""

    message: str = Field(description="Human-readable greeting.")


class ExplicitGreetingResponse(InferredGreetingResponse):
    """The validation response_model that supersedes the inferred annotation."""

    source: str = Field(description="Where the winning 200 schema came from.")
    precedence: str = Field(description="Which producer won the 200 schema.")


@app.route(route="openapi/supersedes/greeting", methods=["GET"])
@openapi(
    summary="Validation supersedes inference",
    description="The validation response_model wins the 200 schema over the return annotation.",
    route="/api/openapi/supersedes/greeting",
    method="get",
    tags=["openapi-supersedes"],
)
@validate_http(response_model=ExplicitGreetingResponse)
def supersedes_greeting(req: func.HttpRequest) -> InferredGreetingResponse:
    name = req.params.get("name", "Azure Functions")
    logger.info("Handled supersedes greeting.", extra={"name": name})
    return ExplicitGreetingResponse(
        message=f"Hello, {name}!",
        source="validation_response_model",
        precedence="validation > return annotation",
    )
