"""Use identity-based Service Bus connections in Azure Functions."""

from __future__ import annotations

import azure.functions as func

from app.core.logging import configure_logging
from app.functions.sb_identity import sb_identity_blueprint

configure_logging()

app = func.FunctionApp()
app.register_functions(sb_identity_blueprint)
