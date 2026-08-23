# pyright: reportMissingImports=false, reportUnknownVariableType=false, reportUnknownMemberType=false, reportUntypedFunctionDecorator=false, reportUnknownParameterType=false, reportAny=false, reportExplicitAny=false, reportUnknownArgumentType=false, reportUntypedBaseClass=false, reportUnusedCallResult=false, reportUnannotatedClassAttribute=false, reportUnusedParameter=false

from __future__ import annotations

import os
from typing import Literal

import azure.functions as func
from azure_functions_logging import get_logger, setup_logging, with_context
from azure_functions_openapi import openapi
from azure_functions_validation import validate_http
from pydantic import BaseModel, Field

try:
    from openai import AzureOpenAI
except ImportError:
    AzureOpenAI = None

setup_logging(format="json")
logger = get_logger(__name__)
app = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)


class ImageRequest(BaseModel):
    prompt: str = Field(..., min_length=1)
    size: Literal["1024x1024", "1792x1024", "1024x1792"] = "1024x1024"


class ImageResponse(BaseModel):
    image_url: str
    revised_prompt: str
    deployment: str


def _json_response(model: BaseModel) -> func.HttpResponse:
    return func.HttpResponse(body=model.model_dump_json(), mimetype="application/json")


def _generate_image(prompt: str, size: str) -> ImageResponse:
    deployment = os.getenv("AZURE_OPENAI_IMAGE_DEPLOYMENT", "dall-e-3")
    endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
    api_key = os.getenv("AZURE_OPENAI_KEY")

    if AzureOpenAI is None or not endpoint or not api_key:
        return ImageResponse(
            image_url="https://example.blob.core.windows.net/generated/fallback-image.png",
            revised_prompt=prompt,
            deployment=deployment,
        )

    client = AzureOpenAI(
        api_key=api_key,
        api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-01"),
        azure_endpoint=endpoint,
    )
    response = client.images.generate(model=deployment, prompt=prompt, size=size)
    image = response.data[0]
    return ImageResponse(
        image_url=getattr(image, "url", ""),
        revised_prompt=getattr(image, "revised_prompt", prompt),
        deployment=deployment,
    )


@app.route(route="images/generate", methods=["POST"])
@with_context
@openapi(
    summary="Generate an image with Azure OpenAI",
    description="Calls Azure OpenAI image generation and returns the resulting image URL.",
    requests=ImageRequest,
    responses={200: ImageResponse},
    tags=["ai"],
)
@validate_http(body=ImageRequest, response_model=ImageResponse)
def generate_image(req: func.HttpRequest, body: ImageRequest, context: func.Context) -> func.HttpResponse:
    del req
    response = _generate_image(body.prompt, body.size)
    logger.info("Generated image", extra={"deployment": response.deployment, "size": body.size})
    return _json_response(response)
