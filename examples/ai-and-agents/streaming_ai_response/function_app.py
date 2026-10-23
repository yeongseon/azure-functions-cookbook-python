# pyright: reportMissingImports=false, reportUnknownVariableType=false, reportUnknownMemberType=false, reportUntypedFunctionDecorator=false, reportUnknownParameterType=false, reportAny=false, reportExplicitAny=false, reportUnknownArgumentType=false, reportUntypedBaseClass=false, reportUnusedCallResult=false, reportUnannotatedClassAttribute=false, reportUnusedParameter=false

from __future__ import annotations

import json
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


class StreamRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=MAX_PROMPT_CHARS)
    system_prompt: str = Field(
        default="You are a concise Azure Functions assistant.",
        min_length=1,
        max_length=MAX_PROMPT_CHARS,
    )


def _stream_frames(message: str, system_prompt: str) -> str:
    endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
    api_key = os.getenv("AZURE_OPENAI_KEY")
    deployment = os.getenv("AZURE_OPENAI_CHAT_DEPLOYMENT", "gpt-4o-mini")

    if AzureOpenAI is None or not endpoint or not api_key:
        del system_prompt
        chunks = [
            "Azure Functions ",
            "can stream Azure OpenAI output ",
            f"for prompts like: {message}",
        ]
    else:
        client = AzureOpenAI(
            api_key=api_key,
            api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-01"),
            azure_endpoint=endpoint,
            timeout=30.0,
            max_retries=0,
        )
        stream = client.chat.completions.create(
            model=deployment,
            max_tokens=MAX_OUTPUT_TOKENS,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": message},
            ],
            stream=True,
        )
        chunks = []
        for event in stream:
            if not event.choices:
                continue
            delta = event.choices[0].delta.content
            if delta:
                chunks.append(delta)

    frames = [f"data: {json.dumps({'delta': chunk})}\n\n" for chunk in chunks]
    frames.append("event: done\n")
    frames.append(f"data: {json.dumps({'status': 'completed'})}\n\n")
    return "".join(frames)


@app.route(route="stream", methods=["POST"])
@openapi(
    summary="Stream Azure OpenAI response",
    description="Returns SSE frames generated from Azure OpenAI streaming chat completions.",
    tags=["ai"],
)
@with_context
@validate_http(body=StreamRequest, max_body_bytes=MAX_REQUEST_BYTES)
def stream_chat(
    req: func.HttpRequest, body: StreamRequest, context: func.Context
) -> func.HttpResponse:
    del req
    try:
        payload = _stream_frames(body.message, body.system_prompt)
    except OpenAIError:
        logger.error("Azure OpenAI request failed")
        return func.HttpResponse("Model service unavailable", status_code=502)
    logger.info(
        "Completed streaming response",
        extra={"deployment": os.getenv("AZURE_OPENAI_CHAT_DEPLOYMENT", "gpt-4o-mini")},
    )
    return func.HttpResponse(body=payload, mimetype="text/event-stream")
