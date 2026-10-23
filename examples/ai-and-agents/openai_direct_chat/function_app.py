# pyright: reportMissingImports=false, reportUnknownVariableType=false, reportUnknownMemberType=false, reportUntypedFunctionDecorator=false, reportUnknownParameterType=false, reportAny=false, reportExplicitAny=false, reportUnknownArgumentType=false, reportUntypedBaseClass=false, reportUnusedCallResult=false, reportUnannotatedClassAttribute=false, reportUnusedParameter=false

from __future__ import annotations

import os
from typing import Final

import azure.functions as func
from azure_functions_logging import get_logger, setup_logging, with_context
from azure_functions_openapi import openapi
from azure_functions_validation import validate_http
from pydantic import BaseModel, Field

try:
    from openai import AzureOpenAI, OpenAIError
except ImportError:
    AzureOpenAI = None

    class OpenAIError(Exception):
        pass


setup_logging(format="json")
logger = get_logger(__name__)
MAX_REQUEST_BYTES: Final = 32_768
MAX_PROMPT_CHARS: Final = 4_000
MAX_OUTPUT_TOKENS: Final = 256
PUBLIC_DEMO: Final = os.getenv("COOKBOOK_PUBLIC_DEMO", "") == "true"
app = func.FunctionApp(
    http_auth_level=func.AuthLevel.ANONYMOUS if PUBLIC_DEMO else func.AuthLevel.FUNCTION
)
if PUBLIC_DEMO:
    logger.warning(
        "Public paid-AI demo enabled; authentication and cost protection required at edge"
    )


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=MAX_PROMPT_CHARS)
    system_prompt: str = Field(
        default="You are a concise Azure Functions assistant.",
        min_length=1,
        max_length=MAX_PROMPT_CHARS,
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
        timeout=30.0,
        max_retries=0,
    )
    completion = client.chat.completions.create(
        model=deployment,
        max_tokens=MAX_OUTPUT_TOKENS,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": message},
        ],
    )
    content = completion.choices[0].message.content or ""
    return content.strip() or "The model returned an empty response."


@app.route(route="chat", methods=["POST"])
@openapi(
    summary="Chat with Azure OpenAI",
    description="Sends a single user message to Azure OpenAI and returns the answer.",
    tags=["ai"],
)
@with_context
@validate_http(body=ChatRequest, response_model=ChatResponse, max_body_bytes=MAX_REQUEST_BYTES)
def chat(req: func.HttpRequest, body: ChatRequest, context: func.Context) -> func.HttpResponse:
    del req
    try:
        answer = _complete_chat(body.message, body.system_prompt)
    except OpenAIError:
        logger.error("Azure OpenAI request failed")
        return func.HttpResponse("Model service unavailable", status_code=502)
    deployment = os.getenv("AZURE_OPENAI_CHAT_DEPLOYMENT", "gpt-4o-mini")
    logger.info("Completed direct chat request", extra={"deployment": deployment})
    return _json_response(ChatResponse(answer=answer, deployment=deployment))
