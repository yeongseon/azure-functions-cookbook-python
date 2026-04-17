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
app = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)


class VectorSearchRequest(BaseModel):
    query: str = Field(..., min_length=1)
    top_k: int = Field(default=3, ge=1, le=10)


class SearchResult(BaseModel):
    id: str
    title: str
    content: str
    score: float


class VectorSearchResponse(BaseModel):
    query: str
    results: list[SearchResult]


def _json_response(model: BaseModel) -> func.HttpResponse:
    return func.HttpResponse(body=model.model_dump_json(), mimetype="application/json")


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


def _vector_search(query: str, top_k: int) -> list[SearchResult]:
    openai_client = _openai_client()
    search_client = _search_client()
    if openai_client is None or search_client is None or VectorizedQuery is None:
        return [
            SearchResult(
                id="doc-1",
                title="Azure Functions overview",
                content="Azure Functions automatically scales based on demand.",
                score=0.92,
            )
        ]

    embedding = openai_client.embeddings.create(
        model=os.getenv("AZURE_OPENAI_EMBEDDING_DEPLOYMENT", "text-embedding-3-small"),
        input=query,
    )
    vector_query = VectorizedQuery(
        vector=embedding.data[0].embedding,
        k_nearest_neighbors=top_k,
        fields="content_vector",
    )
    raw_results = search_client.search(search_text=None, vector_queries=[vector_query], top=top_k)
    results: list[SearchResult] = []
    for item in raw_results:
        results.append(
            SearchResult(
                id=str(item.get("id", "unknown")),
                title=str(item.get("title", "Untitled")),
                content=str(item.get("content", "")),
                score=float(item.get("@search.score", 0.0)),
            )
        )
    return results


@app.route(route="search", methods=["POST"])
@with_context
@openapi(
    summary="Run embedding vector search",
    description="Creates an embedding with Azure OpenAI and runs a vector query in Azure AI Search.",
    request_body=VectorSearchRequest,
    response={200: VectorSearchResponse},
    tags=["ai"],
)
@validate_http(body=VectorSearchRequest, response_model=VectorSearchResponse)
def search(req: func.HttpRequest, body: VectorSearchRequest) -> func.HttpResponse:
    del req
    results = _vector_search(body.query, body.top_k)
    logger.info("Completed vector search", extra={"top_k": body.top_k, "matches": len(results)})
    return _json_response(VectorSearchResponse(query=body.query, results=results))
