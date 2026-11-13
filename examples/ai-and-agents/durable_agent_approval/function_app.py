"""Durable agent workflow: HTTP start, agent draft activity, human approval, bounded completion."""

from __future__ import annotations

import azure.functions as func

from app.functions.workflow import bp

app = func.FunctionApp()
app.register_functions(bp)
