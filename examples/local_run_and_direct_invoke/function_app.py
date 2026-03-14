"""Example for local development and direct Python invocation.

This project demonstrates two ways to test Azure Functions locally:

1. ``func start`` - runs the full Azure Functions host
2. Direct Python import - call function handlers as regular functions

The direct-invoke approach is useful for quick validation without
starting the full runtime.
"""

from __future__ import annotations

import json

import azure.functions as func

app = func.FunctionApp()


@app.route(route="greet", methods=["GET", "POST"], auth_level=func.AuthLevel.ANONYMOUS)
def greet(req: func.HttpRequest) -> func.HttpResponse:
    """Return a personalized greeting."""
    name = req.params.get("name")
    if not name:
        try:
            body = req.get_json()
            name = body.get("name")
        except ValueError:
            pass

    if not name:
        return func.HttpResponse(
            json.dumps({"error": "Please provide a 'name' query param or JSON body."}),
            mimetype="application/json",
            status_code=400,
        )

    return func.HttpResponse(
        json.dumps({"greeting": f"Hello, {name}!"}),
        mimetype="application/json",
        status_code=200,
    )
