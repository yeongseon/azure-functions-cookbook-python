"""Service Bus queue trigger for resilient background task processing."""

from __future__ import annotations

import azure.functions as func

from app.core.logging import configure_logging
from app.functions.servicebus import servicebus_blueprint

configure_logging()

app = func.FunctionApp()
app.register_functions(servicebus_blueprint)
