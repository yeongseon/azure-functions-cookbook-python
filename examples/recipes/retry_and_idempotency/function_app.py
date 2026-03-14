"""Retry and idempotency patterns for Azure Functions triggers."""

from __future__ import annotations

import azure.functions as func

from app.core.logging import configure_logging
from app.functions.retry import retry_blueprint

configure_logging()

app = func.FunctionApp()
app.register_functions(retry_blueprint)
