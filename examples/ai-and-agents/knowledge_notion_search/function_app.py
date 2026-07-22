"""Notion-backed knowledge retrieval with ``azure-functions-knowledge``.

The ``KnowledgeBindings`` decorator API gives two Azure Functions-native ways
to reach a knowledge provider (here, Notion):

* ``@kb.input(...)``    -- inject ranked search results into a handler param.
* ``@kb.inject_client`` -- inject a live provider client for imperative reads.

The optional ``azure-functions-knowledge`` dependency is import-guarded so this
module always imports cleanly (the cookbook smoke suite only imports
``function_app`` and asserts it exposes ``app``). When the package is absent the
same routes are registered as ``501`` stubs. The Notion token is read from the
``NOTION_TOKEN`` app setting via the ``%NOTION_TOKEN%`` binding expression.
"""

from __future__ import annotations

import json
import logging
from typing import Any

import azure.functions as func

try:
    from azure_functions_logging import get_logger, setup_logging

    setup_logging(format="json")
    logger = get_logger(__name__)
except ImportError:  # pragma: no cover - only without the toolkit
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)  # type: ignore[assignment]

app = func.FunctionApp(http_auth_level=func.AuthLevel.FUNCTION)

try:
    from azure_functions_knowledge import Document, KnowledgeBindings

    _KB_AVAILABLE = True
except ImportError:  # pragma: no cover - exercised in smoke CI (pkg absent)
    _KB_AVAILABLE = False


def _register_stub_routes() -> None:
    """Register 501 placeholders when azure-functions-knowledge is absent."""
    logger.warning("azure-functions-knowledge not installed; registering stub routes")

    @app.route(route="search", methods=["GET"])
    def search_stub(req: func.HttpRequest) -> func.HttpResponse:
        return func.HttpResponse(
            json.dumps({"status": "azure-functions-knowledge not installed"}),
            mimetype="application/json",
            status_code=501,
        )

    @app.route(route="page/{page_id}", methods=["GET"])
    def page_stub(req: func.HttpRequest) -> func.HttpResponse:
        return func.HttpResponse(
            json.dumps({"status": "azure-functions-knowledge not installed"}),
            mimetype="application/json",
            status_code=501,
        )


def _register_knowledge_routes() -> None:
    """Register the real Notion-backed routes via KnowledgeBindings."""
    kb = KnowledgeBindings()

    @app.route(route="search", methods=["GET"])
    @kb.input(
        "docs",
        provider="notion",
        query=lambda req: req.params.get("q", ""),
        top=5,
        connection="%NOTION_TOKEN%",
    )
    def search_knowledge(req: func.HttpRequest, docs: list[Document]) -> func.HttpResponse:
        logger.info("Knowledge search", extra={"q": req.params.get("q", ""), "hits": len(docs)})
        results = [{"title": d.title, "url": d.url, "id": d.document_id} for d in docs]
        return func.HttpResponse(json.dumps(results), mimetype="application/json")

    @app.route(route="page/{page_id}", methods=["GET"])
    @kb.inject_client("client", provider="notion", connection="%NOTION_TOKEN%")
    def get_page(req: func.HttpRequest, client: Any) -> func.HttpResponse:
        page_id = req.route_params.get("page_id", "")
        logger.info("Knowledge page fetch", extra={"page_id": page_id})
        doc = client.get_document(page_id)
        return func.HttpResponse(
            json.dumps({"title": doc.title, "content": doc.content, "url": doc.url}),
            mimetype="application/json",
        )


if _KB_AVAILABLE:
    _register_knowledge_routes()
else:
    _register_stub_routes()
