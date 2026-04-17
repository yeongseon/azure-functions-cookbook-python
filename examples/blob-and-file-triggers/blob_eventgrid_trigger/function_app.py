"""Blob trigger using Event Grid notifications instead of storage polling."""

from __future__ import annotations

import azure.functions as func

from app.core.logging import configure_logging
from app.functions.blob_eventgrid import blob_eventgrid_blueprint

configure_logging()

app = func.FunctionApp()
app.register_functions(blob_eventgrid_blueprint)
