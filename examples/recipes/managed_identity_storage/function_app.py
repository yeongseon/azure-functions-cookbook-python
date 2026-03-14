"""Use identity-based Azure Storage Queue connections in Azure Functions."""

from __future__ import annotations

import azure.functions as func

from app.core.logging import configure_logging
from app.functions.queue_identity import queue_identity_blueprint

configure_logging()

app = func.FunctionApp()
app.register_functions(queue_identity_blueprint)
