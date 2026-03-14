"""Example for local development and direct Python invocation."""

from __future__ import annotations

import azure.functions as func

from app.core.logging import configure_logging
from app.functions.greet import greet_blueprint

configure_logging()

app = func.FunctionApp()
app.register_functions(greet_blueprint)
