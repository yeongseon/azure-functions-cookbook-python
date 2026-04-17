"""Event Hub trigger that parses telemetry messages from a stream."""

from __future__ import annotations

import azure.functions as func

from app.core.logging import configure_logging
from app.functions.eventhub import eventhub_blueprint

configure_logging()

app = func.FunctionApp()
app.register_functions(eventhub_blueprint)
