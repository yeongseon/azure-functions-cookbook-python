"""Durable Functions determinism-safe orchestrator patterns."""

from __future__ import annotations

import azure.functions as func

from app.core.logging import configure_logging
from app.functions.orchestration import bp

configure_logging()

app = func.FunctionApp()
app.register_functions(bp)
