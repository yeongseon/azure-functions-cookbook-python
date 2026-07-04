"""HTTP endpoints that expose azure-functions-doctor diagnostics."""

from __future__ import annotations

import azure.functions as func

from app.core.logging import configure_logging
from app.functions.diagnostics import diagnostics_blueprint

configure_logging()

# Default auth level is FUNCTION so diagnostics endpoints require a key.
# The health probe overrides this to ANONYMOUS in its decorator.
app = func.FunctionApp(http_auth_level=func.AuthLevel.FUNCTION)
app.register_functions(diagnostics_blueprint)
