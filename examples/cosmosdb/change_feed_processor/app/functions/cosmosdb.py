from __future__ import annotations

import logging
from typing import Any

import azure.functions as func

from app.services.change_service import process_change

cosmosdb_blueprint = func.Blueprint()
logger = logging.getLogger(__name__)


@cosmosdb_blueprint.cosmos_db_trigger(
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
        outcome = process_change(change)
        logger.info("Processed change: %s", outcome)
