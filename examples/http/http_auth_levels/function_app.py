"""Demonstrate Azure Functions HTTP auth levels."""

from __future__ import annotations

import azure.functions as func

app = func.FunctionApp()


@app.route(route="public", methods=["GET"], auth_level=func.AuthLevel.ANONYMOUS)
def public_endpoint(req: func.HttpRequest) -> func.HttpResponse:
    """No key required — open to anyone."""
    return func.HttpResponse("This endpoint is public (anonymous).")


@app.route(route="protected", methods=["GET"], auth_level=func.AuthLevel.FUNCTION)
def protected_endpoint(req: func.HttpRequest) -> func.HttpResponse:
    """Requires a function-level API key in the query string or header."""
    return func.HttpResponse("This endpoint requires a function key.")


@app.route(route="admin-only", methods=["GET"], auth_level=func.AuthLevel.ADMIN)
def admin_endpoint(req: func.HttpRequest) -> func.HttpResponse:
    """Requires the master (admin) key."""
    return func.HttpResponse("This endpoint requires the admin/master key.")
