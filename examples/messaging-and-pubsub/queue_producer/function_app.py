"""HTTP trigger that validates and enqueues tasks to Azure Storage Queue."""

from __future__ import annotations

import azure.functions as func

from app.core.logging import configure_logging
from app.functions.enqueue import enqueue_blueprint

configure_logging()

app = func.FunctionApp()
app.register_functions(enqueue_blueprint)
