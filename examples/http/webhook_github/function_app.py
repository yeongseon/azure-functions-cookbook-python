"""GitHub webhook receiver with HMAC-SHA256 signature verification."""

from __future__ import annotations

import azure.functions as func

from app.core.logging import configure_logging
from app.functions.webhook import webhook_blueprint

configure_logging()

app = func.FunctionApp()
app.register_functions(webhook_blueprint)
