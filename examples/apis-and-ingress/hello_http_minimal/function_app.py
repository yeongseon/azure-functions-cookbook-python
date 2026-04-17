"""Minimal HTTP trigger - the Hello World of Azure Functions."""

from __future__ import annotations

import azure.functions as func

from app.core.logging import configure_logging
from app.functions.http import http_blueprint

configure_logging()

app = func.FunctionApp()
app.register_functions(http_blueprint)
