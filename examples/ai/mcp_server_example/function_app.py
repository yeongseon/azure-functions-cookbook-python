"""MCP server hosted on Azure Functions Python."""

from __future__ import annotations

import azure.functions as func

from app.core.logging import configure_logging
from app.functions.mcp import mcp_blueprint

configure_logging()

app = func.FunctionApp()
app.register_functions(mcp_blueprint)
