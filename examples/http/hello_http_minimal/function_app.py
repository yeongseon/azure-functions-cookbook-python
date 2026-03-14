"""Minimal HTTP trigger — the Hello World of Azure Functions."""

from __future__ import annotations

import azure.functions as func

app = func.FunctionApp()


@app.route(route="hello", methods=["GET"], auth_level=func.AuthLevel.ANONYMOUS)
def hello(req: func.HttpRequest) -> func.HttpResponse:
    """Return a greeting. Accepts an optional 'name' query parameter."""
    name = req.params.get("name", "World")
    return func.HttpResponse(f"Hello, {name}!")
