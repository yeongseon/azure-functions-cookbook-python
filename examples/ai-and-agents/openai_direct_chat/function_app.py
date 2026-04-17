# pyright: reportMissingImports=false, reportUnknownVariableType=false, reportUnknownMemberType=false, reportUntypedFunctionDecorator=false, reportUnknownParameterType=false, reportAny=false, reportExplicitAny=false, reportUnknownArgumentType=false, reportUntypedBaseClass=false, reportUnusedCallResult=false, reportUnannotatedClassAttribute=false, reportUnusedParameter=false

from __future__ import annotations

import logging
import os
from typing import Any

import azure.functions as func
from pydantic import BaseModel, Field

try:
    from azure_functions_logging import get_logger, setup_logging, with_context
except ImportError:

    def setup_logging(*args: Any, **kwargs: Any) -> None:
        logging.basicConfig(level=logging.INFO)

    def get_logger(name: str) -> logging.Logger:
        return logging.getLogger(name)

    def with_context(function: Any) -> Any:
        return function


try:
    from azure_functions_openapi import openapi
except ImportError:

    def openapi(*args: Any, **kwargs: Any):
        def decorator(function: Any) -> Any:
            return function

        return decorator


try:
    from azure_functions_validation import validate_http
except ImportError:

    def validate_http(*args: Any, **kwargs: Any):
        def decorator(function: Any) -> Any:
            return function

        return decorator


try:
    from openai import AzureOpenAI
except ImportError:
    AzureOpenAI = None

setup_logging(format="json")
logger = get_logger(__name__)
app = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, description="User prompt to send to Azure OpenAI.")
    system_prompt: str = Field(
        default="You are a concise Azure Functions assistant.",
        min_length=1,
        description="Optional system instruction.",
    )


class ChatResponse(BaseModel):
    answer: str
    deployment: str


def _json_response(model: BaseModel, *, status_code: int = 200) -> func.HttpResponse:
    return func.HttpResponse(
        body=model.model_dump_json(),
        status_code=status_code,
        mimetype="application/json",
    )


def _complete_chat(message: str, system_prompt: str) -> str:
    deployment = os.getenv("AZURE_OPENAI_CHAT_DEPLOYMENT", "gpt-4o-mini")
    endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
    api_key = os.getenv("AZURE_OPENAI_KEY")

    if AzureOpenAI is None or not endpoint or not api_key:
        return (
            "Fallback response: Azure Functions can call Azure OpenAI from an HTTP "
            "trigger and return the generated answer as JSON."
        )

    client = AzureOpenAI(
        api_key=api_key,
        api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-01"),
        azure_endpoint=endpoint,
    )
    completion = client.chat.completions.create(
        model=deployment,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": message},
        ],
    )
    content = completion.choices[0].message.content or ""
    return content.strip() or "The model returned an empty response."


@app.route(route="chat", methods=["POST"])
@with_context
@openapi(
    summary="Chat with Azure OpenAI",
    description="Sends a single user message to Azure OpenAI and returns the answer.",
    request_body=ChatRequest,
    response={200: ChatResponse},
    tags=["ai"],
)
@validate_http(body=ChatRequest, response_model=ChatResponse)
def chat(req: func.HttpRequest, body: ChatRequest) -> func.HttpResponse:
    del req
    answer = _complete_chat(body.message, body.system_prompt)
    deployment = os.getenv("AZURE_OPENAI_CHAT_DEPLOYMENT", "gpt-4o-mini")
    logger.info("Completed direct chat request", extra={"deployment": deployment})
    return _json_response(ChatResponse(answer=answer, deployment=deployment))
