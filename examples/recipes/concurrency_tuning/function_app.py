"""Queue-triggered function demonstrating dynamic concurrency settings."""

from __future__ import annotations

import azure.functions as func

from app.core.logging import configure_logging
from app.functions.queue_concurrency import queue_concurrency_blueprint

configure_logging()

app = func.FunctionApp()
app.register_functions(queue_concurrency_blueprint)
