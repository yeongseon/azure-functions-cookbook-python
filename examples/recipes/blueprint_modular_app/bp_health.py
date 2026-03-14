"""Health endpoints blueprint for modular function apps."""

from __future__ import annotations

import azure.functions as func

bp = func.Blueprint()


@bp.route(route="health", methods=["GET"])
def get_health(req: func.HttpRequest) -> func.HttpResponse:
    """Return a simple service health payload."""
    del req
    return func.HttpResponse(
        body='{"status": "healthy"}',
        mimetype="application/json",
        status_code=200,
    )
