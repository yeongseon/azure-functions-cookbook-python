"""Cosmos DB change feed trigger that handles inserts and updates."""

from __future__ import annotations

import logging
from typing import Any

import azure.functions as func

app = func.FunctionApp()
logger = logging.getLogger(__name__)


@app.cosmos_db_trigger(
    arg_name="docs",
    database_name="maindb",
    container_name="items",
    connection="CosmosDBConnection",
    lease_container_name="leases",
    create_lease_container_if_not_exists=True,
)
def process_cosmos_changes(docs: list[dict[str, Any]]) -> None:
    """Handle changed Cosmos DB documents from the change feed."""
    if not docs:
        logger.info("No documents found in this change feed batch.")
        return

    logger.info("Received %d changed document(s) from Cosmos DB.", len(docs))
    for change in docs:
        outcome = _process_change(change)
        logger.info("Processed change: %s", outcome)


def _process_change(change: dict[str, Any]) -> str:
    """Simulate downstream handling for one changed document."""
    document_id = str(change.get("id", "unknown-id"))
    category = str(change.get("category", "uncategorized"))
    return f"id={document_id} category={category} status=synced"
