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


setup_logging(format="json")
logger = get_logger(__name__)
app = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)

_FALLBACK_DOCUMENTS: list[dict[str, str]] = [
    {
        "id": "doc-1",
        "title": "Azure Functions overview",
        "content": "Azure Functions is a serverless compute service that scales on demand.",
        "source": "https://learn.microsoft.com/en-us/azure/azure-functions/",
    }
]


class Citation(BaseModel):
    id: str
    title: str
    chunk: str


class AskRequest(BaseModel):
    question: str = Field(..., min_length=1, description="User question for the knowledge base")
    top_k: int = Field(default=3, ge=1, le=10, description="Maximum number of chunks to retrieve")
    metadata_filter: str | None = Field(default=None, description="Optional search filter")


class AskResponse(BaseModel):
    answer: str
    citations: list[Citation]
    matches: int


class IngestDocument(BaseModel):
    title: str = Field(..., min_length=1)
    content: str = Field(..., min_length=1)
    id: str | None = Field(default=None, description="Optional caller-supplied document ID")
    source: str | None = Field(default=None, description="Optional URI or logical source name")


class IngestRequest(BaseModel):
    documents: list[IngestDocument] = Field(..., min_length=1, max_length=20)


class IngestResponse(BaseModel):
    status: str
    ingested: int
    index: str


class _FallbackKnowledgeClient:
    def __init__(self) -> None:
        self._index = os.getenv("AI_SEARCH_INDEX", "knowledge-index")

    def ask(self, question: str, top_k: int, metadata_filter: str | None = None) -> dict[str, Any]:
        del metadata_filter
        matches = _FALLBACK_DOCUMENTS[:top_k]
        context = " ".join(document["content"] for document in matches) or "No indexed content yet."
        answer = f"Fallback answer for '{question}'. Retrieved context: {context}"
        return {
            "answer": answer,
            "citations": [
                {
                    "id": document["id"],
                    "title": document["title"],
                    "chunk": document["content"],
                }
                for document in matches
            ],
        }

    def ingest_documents(self, documents: list[dict[str, str]]) -> dict[str, Any]:
        start = len(_FALLBACK_DOCUMENTS) + 1
        for offset, document in enumerate(documents, start=start):
            _FALLBACK_DOCUMENTS.append(
                {
                    "id": document.get("id") or f"doc-{offset}",
                    "title": document["title"],
                    "content": document["content"],
                    "source": document.get("source", "inline"),
                }
            )
        return {"status": "accepted", "ingested": len(documents), "index": self._index}


def _create_knowledge_client() -> Any:
    logger.info("Using local fallback knowledge client")
    return _FallbackKnowledgeClient()


def _json_response(model: BaseModel, *, status_code: int = 200) -> func.HttpResponse:
    return func.HttpResponse(
        body=model.model_dump_json(),
        status_code=status_code,
        mimetype="application/json",
    )


@app.route(route="ask", methods=["POST"])
@with_context
@openapi(
    summary="Ask the knowledge base",
    description="Runs the RAG pipeline: retrieve context and generate a grounded answer.",
    request_body=AskRequest,
    response={200: AskResponse},
    tags=["knowledge"],
)
@validate_http(body=AskRequest, response_model=AskResponse)
def ask(req: func.HttpRequest, body: AskRequest) -> func.HttpResponse:
    del req
    client = _create_knowledge_client()
    result = client.ask(
        question=body.question,
        top_k=body.top_k,
        metadata_filter=body.metadata_filter,
    )

    response = AskResponse(
        answer=result["answer"],
        citations=[Citation(**citation) for citation in result.get("citations", [])],
        matches=len(result.get("citations", [])),
    )

    logger.info(
        "Answered knowledge question",
        extra={"top_k": body.top_k, "matches": response.matches},
    )
    return _json_response(response)


@app.route(route="ingest", methods=["POST"])
@with_context
@openapi(
    summary="Ingest knowledge documents",
    description="Adds new documents to the knowledge base so future RAG queries can retrieve them.",
    request_body=IngestRequest,
    response={202: IngestResponse},
    tags=["knowledge"],
)
@validate_http(body=IngestRequest, response_model=IngestResponse)
def ingest(req: func.HttpRequest, body: IngestRequest) -> func.HttpResponse:
    del req
    client = _create_knowledge_client()
    payload = [document.model_dump(exclude_none=True) for document in body.documents]
    result = client.ingest_documents(payload)

    response = IngestResponse(
        status=result.get("status", "accepted"),
        ingested=int(result.get("ingested", len(payload))),
        index=result.get("index", os.getenv("AI_SEARCH_INDEX", "knowledge-index")),
    )

    logger.info(
        "Accepted knowledge ingestion",
        extra={"documents": response.ingested, "index": response.index},
    )
    return _json_response(response, status_code=202)


@app.route(route="healthz", methods=["GET"])
def healthz(req: func.HttpRequest) -> func.HttpResponse:
    del req
    return func.HttpResponse(
        body=json.dumps({"status": "ok", "mode": "knowledge-api"}),
        mimetype="application/json",
    )
