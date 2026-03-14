"""Blob trigger (polling mode) that validates and processes uploaded blobs."""

from __future__ import annotations

import azure.functions as func

from app.core.logging import configure_logging
from app.functions.blob_processor import blob_blueprint

configure_logging()

app = func.FunctionApp()
app.register_functions(blob_blueprint)
