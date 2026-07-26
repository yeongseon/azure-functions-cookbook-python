"""Convergent scoring workflow with ``azure-functions-durable-graph``.

Topology (a fan-in DAG expressed with the ManifestBuilder graph API)::

    split -> score_length -> score_keywords -> score_sentiment -> aggregate

``split`` seeds the shared state, each ``score_*`` node contributes one
independent partial signal, and ``aggregate`` (terminal) fans the signals back
in to a single decision. The durable-graph runtime persists state between node
transitions, so each node is a durable step rather than an in-process call.

The optional ``azure-functions-durable-graph`` dependency is import-guarded so
this module always imports cleanly -- the cookbook smoke suite only imports
``function_app`` and asserts it exposes ``app``. When the package is absent a
plain HTTP ``FunctionApp`` stub is exposed instead.
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


def _build_app() -> func.FunctionApp:
    """Build the durable-graph app, or a plain HTTP stub if unavailable."""
    try:
        from azure_functions_durable_graph import DurableGraphApp, ManifestBuilder
        from pydantic import BaseModel
    except ImportError:  # pragma: no cover - exercised in smoke CI (pkg absent)
        logger.warning("azure-functions-durable-graph not installed; using HTTP stub")
        stub = func.FunctionApp(http_auth_level=func.AuthLevel.FUNCTION)

        @stub.route(route="fan-in/status", methods=["GET"])
        def status(req: func.HttpRequest) -> func.HttpResponse:
            return func.HttpResponse(
                json.dumps({"status": "azure-functions-durable-graph not installed"}),
                mimetype="application/json",
                status_code=501,
            )

        return stub

    class ReviewState(BaseModel):
        """State threaded through the convergent scoring graph."""

        text: str
        length_score: int | None = None
        keyword_score: int | None = None
        sentiment_score: int | None = None
        decision: str | None = None

    def split(state: ReviewState) -> dict[str, Any]:
        """Entry node -- seed point before the scoring chain."""
        logger.info("Starting review scoring", extra={"chars": len(state.text)})
        return {}

    def score_length(state: ReviewState) -> dict[str, Any]:
        return {"length_score": min(len(state.text) // 20, 5)}

    def score_keywords(state: ReviewState) -> dict[str, Any]:
        hits = sum(state.text.lower().count(w) for w in ("bug", "crash", "error", "fail"))
        return {"keyword_score": min(hits, 5)}

    def score_sentiment(state: ReviewState) -> dict[str, Any]:
        negative = {"bad", "broken", "terrible", "worst", "angry", "hate"}
        words = set(state.text.lower().split())
        return {"sentiment_score": 5 if words & negative else 0}

    def aggregate(state: ReviewState) -> dict[str, Any]:
        """Terminal fan-in node -- combine the partial scores into a decision."""
        total = (
            (state.length_score or 0) + (state.keyword_score or 0) + (state.sentiment_score or 0)
        )
        decision = "escalate" if total >= 6 else "auto-resolve"
        logger.info("Aggregated review score", extra={"total": total, "decision": decision})
        return {"decision": decision}

    builder = ManifestBuilder(
        graph_name="review_fan_in",
        state_model=ReviewState,
        version="0.1.0",
        metadata={"example": True, "profile": "fan-in"},
    )
    builder.set_entrypoint("split")
    builder.add_node("split", split, next_node="score_length")
    builder.add_node("score_length", score_length, next_node="score_keywords")
    builder.add_node("score_keywords", score_keywords, next_node="score_sentiment")
    builder.add_node("score_sentiment", score_sentiment, next_node="aggregate")
    builder.add_node("aggregate", aggregate, terminal=True)

    runtime = DurableGraphApp()
    runtime.register_registration(builder.build())
    return runtime.function_app


app = _build_app()
