# pyright: reportMissingImports=false, reportUnknownVariableType=false, reportUnknownMemberType=false, reportUntypedFunctionDecorator=false, reportUnknownParameterType=false, reportAny=false, reportExplicitAny=false, reportUnknownArgumentType=false, reportUntypedBaseClass=false, reportUnusedCallResult=false, reportUnannotatedClassAttribute=false, reportUnusedParameter=false

from __future__ import annotations

import inspect
import json
import logging
import os
import uuid
from types import SimpleNamespace
from typing import Any

import azure.functions as func
from pydantic import BaseModel, Field

try:
    from azure_functions_logging import get_logger, setup_logging
except ImportError:

    def setup_logging(*args: Any, **kwargs: Any) -> None:
        logging.basicConfig(level=logging.INFO)

    def get_logger(name: str) -> logging.Logger:
        return logging.getLogger(name)


try:
    from azure_functions_openapi import openapi
except ImportError:

    def openapi(*args: Any, **kwargs: Any):
        def decorator(function: Any) -> Any:
            return function

        return decorator


try:
    from azure_functions_validation import validate_http as _validate_http
except ImportError:
    _validate_http = None


def validate_http(*args: Any, **kwargs: Any):
    if _validate_http is None:

        def decorator(function: Any) -> Any:
            return function

        return decorator

    def decorator(function: Any) -> Any:
        validator = _validate_http
        try:
            if validator is None:
                return function
            return validator(*args, **kwargs)(function)
        except Exception:
            return function

    return decorator


try:
    import azure.durable_functions as df
except ImportError:

    class _FallbackDFApp(func.FunctionApp):
        def durable_client_input(self, client_name: str):
            del client_name

            def decorator(function: Any) -> Any:
                return function

            return decorator

        def orchestration_trigger(self, context_name: str):
            del context_name

            def decorator(function: Any) -> Any:
                return function

            return decorator

        def activity_trigger(self, input_name: str):
            del input_name

            def decorator(function: Any) -> Any:
                return function

            return decorator

    df = SimpleNamespace(
        DFApp=_FallbackDFApp,
        DurableOrchestrationClient=object,
        DurableOrchestrationContext=object,
    )


try:
    from azure.core.credentials import AzureKeyCredential
    from azure.search.documents import SearchClient
    from azure.search.documents.models import VectorizedQuery
except ImportError:
    AzureKeyCredential = None
    SearchClient = None
    VectorizedQuery = None


try:
    from openai import AzureOpenAI
except ImportError:
    AzureOpenAI = None

setup_logging(format="json")
logger = get_logger(__name__)
app = df.DFApp(http_auth_level=func.AuthLevel.ANONYMOUS)


class PipelineRequest(BaseModel):
    question: str = Field(..., min_length=1)
    top_k: int = Field(default=3, ge=1, le=5)


class PipelineStartResponse(BaseModel):
    instance_id: str
    status_query_get_uri: str


def _openai_client() -> Any | None:
    endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
    api_key = os.getenv("AZURE_OPENAI_KEY")
    if AzureOpenAI is None or not endpoint or not api_key:
        return None
    return AzureOpenAI(
        api_key=api_key,
        api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-01"),
        azure_endpoint=endpoint,
    )


def _search_client() -> Any | None:
    endpoint = os.getenv("AI_SEARCH_ENDPOINT")
    api_key = os.getenv("AI_SEARCH_KEY")
    index_name = os.getenv("AI_SEARCH_INDEX", "knowledge-index")
    if (
        SearchClient is None
        or AzureKeyCredential is None
        or not endpoint
        or not api_key
        or not index_name
    ):
        return None
    return SearchClient(
        endpoint=endpoint, index_name=index_name, credential=AzureKeyCredential(api_key)
    )


def _json_response(model: BaseModel, *, status_code: int = 200) -> func.HttpResponse:
    return func.HttpResponse(
        body=model.model_dump_json(),
        status_code=status_code,
        mimetype="application/json",
    )


@app.route(route="pipeline/start", methods=["POST"])
@openapi(
    summary="Start durable AI pipeline",
    description="Starts a durable workflow that embeds, searches, and generates an answer.",
    request_body=PipelineRequest,
    response={202: PipelineStartResponse},
    tags=["ai"],
)
@validate_http(body=PipelineRequest, response_model=PipelineStartResponse)
@app.durable_client_input(client_name="client")
async def start_pipeline(
    req: func.HttpRequest, body: PipelineRequest, client: Any
) -> func.HttpResponse:
    del req
    instance_id = f"pipeline-{uuid.uuid4()}"
    if hasattr(client, "start_new"):
        maybe_instance_id = client.start_new(
            orchestration_function_name="pipeline_orchestrator",
            client_input=body.model_dump(),
        )
        if inspect.isawaitable(maybe_instance_id):
            instance_id = await maybe_instance_id
        else:
            instance_id = maybe_instance_id
        status_uri = f"http://localhost:7071/runtime/webhooks/durabletask/instances/{instance_id}"
    else:
        status_uri = f"http://localhost:7071/runtime/webhooks/durabletask/instances/{instance_id}"

    logger.info("Started durable AI pipeline", extra={"instance_id": instance_id})
    return _json_response(
        PipelineStartResponse(instance_id=str(instance_id), status_query_get_uri=status_uri),
        status_code=202,
    )


@app.orchestration_trigger(context_name="context")
def pipeline_orchestrator(context: Any) -> Any:
    if not hasattr(context, "call_activity"):
        return {
            "answer": "Fallback durable pipeline response.",
            "matches": [{"id": "doc-1", "title": "Azure Functions overview"}],
        }

    payload = context.get_input()
    vector = yield context.call_activity("embed_query", payload)
    matches = yield context.call_activity(
        "search_documents", {"vector": vector, "top_k": payload.get("top_k", 3)}
    )
    answer = yield context.call_activity(
        "generate_answer",
        {"question": payload.get("question", ""), "documents": matches},
    )
    return {"answer": answer, "matches": matches}


@app.activity_trigger(input_name="payload")
def embed_query(payload: dict[str, Any]) -> list[float]:
    client = _openai_client()
    if client is None:
        return [0.12, 0.34, 0.56]

    response = client.embeddings.create(
        model=os.getenv("AZURE_OPENAI_EMBEDDING_DEPLOYMENT", "text-embedding-3-small"),
        input=payload.get("question", ""),
    )
    logger.info("Embedded durable query")
    return list(response.data[0].embedding)


@app.activity_trigger(input_name="payload")
def search_documents(payload: dict[str, Any]) -> list[dict[str, Any]]:
    client = _search_client()
    if client is None or VectorizedQuery is None:
        return [
            {
                "id": "doc-1",
                "title": "Azure Functions overview",
                "content": "Azure Functions automatically scales based on demand.",
                "score": 0.91,
            }
        ]

    vector_query = VectorizedQuery(
        vector=payload["vector"],
        k_nearest_neighbors=int(payload.get("top_k", 3)),
        fields="content_vector",
    )
    results = client.search(
        search_text=None, vector_queries=[vector_query], top=payload.get("top_k", 3)
    )
    matches: list[dict[str, Any]] = []
    for item in results:
        matches.append(
            {
                "id": item.get("id", "unknown"),
                "title": item.get("title", "Untitled"),
                "content": item.get("content", ""),
                "score": float(item.get("@search.score", 0.0)),
            }
        )
    logger.info("Completed durable vector search", extra={"matches": len(matches)})
    return matches


@app.activity_trigger(input_name="payload")
def generate_answer(payload: dict[str, Any]) -> str:
    documents = payload.get("documents", [])
    context_text = "\n".join(document.get("content", "") for document in documents)
    client = _openai_client()
    if client is None:
        return (
            "Fallback durable answer: Azure Functions scales automatically based on demand, "
            "which is the key point retrieved from the search results."
        )

    completion = client.chat.completions.create(
        model=os.getenv("AZURE_OPENAI_CHAT_DEPLOYMENT", "gpt-4o-mini"),
        messages=[
            {
                "role": "system",
                "content": "Answer the user using only the retrieved context.",
            },
            {
                "role": "user",
                "content": (
                    f"Question: {payload.get('question', '')}\n\nRetrieved context:\n{context_text}"
                ),
            },
        ],
    )
    message = completion.choices[0].message.content or ""
    logger.info("Generated durable answer", extra={"documents": len(documents)})
    return message.strip() or "The model returned an empty response."


@app.route(route="pipeline/sample-result", methods=["GET"])
def sample_result(req: func.HttpRequest) -> func.HttpResponse:
    del req
    return func.HttpResponse(
        body=json.dumps({"status": "ok", "pattern": "durable-ai-pipeline"}),
        mimetype="application/json",
    )
