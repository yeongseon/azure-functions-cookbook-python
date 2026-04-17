"""Compare queue output binding with direct Azure Storage Queue SDK usage."""

from __future__ import annotations

import azure.functions as func

from app.core.logging import configure_logging
from app.functions.binding_route import binding_blueprint
from app.functions.sdk_route import sdk_blueprint

configure_logging()

app = func.FunctionApp()
app.register_functions(binding_blueprint)
app.register_functions(sdk_blueprint)
