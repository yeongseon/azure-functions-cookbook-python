"""Cosmos DB change feed trigger that handles inserts and updates."""

from __future__ import annotations

import azure.functions as func

from app.core.logging import configure_logging
from app.functions.cosmosdb import cosmosdb_blueprint

configure_logging()

app = func.FunctionApp()
app.register_functions(cosmosdb_blueprint)
