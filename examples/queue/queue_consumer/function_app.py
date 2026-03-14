"""Queue-triggered worker that parses and processes outbound task messages."""

from __future__ import annotations

import azure.functions as func

from app.core.logging import configure_logging
from app.functions.worker import worker_blueprint

configure_logging()

app = func.FunctionApp()
app.register_functions(worker_blueprint)
