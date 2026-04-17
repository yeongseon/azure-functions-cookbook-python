# pyright: reportMissingImports=false, reportUnknownVariableType=false, reportUnknownMemberType=false, reportUntypedFunctionDecorator=false, reportUnknownParameterType=false, reportAny=false, reportExplicitAny=false, reportUnknownArgumentType=false, reportUntypedBaseClass=false, reportUnusedCallResult=false, reportUnannotatedClassAttribute=false, reportUnusedParameter=false

from __future__ import annotations

import json
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


class StreamRequest(BaseModel):
    message: str = Field(..., min_length=1)
    system_prompt: str = Field(default="You are a concise Azure Functions assistant.", min_length=1)


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
        )
        stream = client.chat.completions.create(
            model=deployment,
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
@with_context
@openapi(
    summary="Stream Azure OpenAI response",
    description="Returns SSE frames generated from Azure OpenAI streaming chat completions.",
    request_body=StreamRequest,
    tags=["ai"],
)
@validate_http(body=StreamRequest)
def stream_chat(req: func.HttpRequest, body: StreamRequest) -> func.HttpResponse:
    del req
    payload = _stream_frames(body.message, body.system_prompt)
    logger.info(
        "Completed streaming response",
        extra={"deployment": os.getenv("AZURE_OPENAI_CHAT_DEPLOYMENT", "gpt-4o-mini")},
    )
    return func.HttpResponse(body=payload, mimetype="text/event-stream")
