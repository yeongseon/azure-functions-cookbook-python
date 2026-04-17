from __future__ import annotations

import azure.functions as func

from app.services.hello_service import build_greeting

http_blueprint = func.Blueprint()


@http_blueprint.route(route="hello", methods=["GET"], auth_level=func.AuthLevel.ANONYMOUS)
def hello(req: func.HttpRequest) -> func.HttpResponse:
    """Return a greeting. Accepts an optional 'name' query parameter."""
    name = req.params.get("name", "World")
    return func.HttpResponse(build_greeting(name))
