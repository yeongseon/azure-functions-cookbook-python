from __future__ import annotations

import azure.functions as func

from app.services.auth_service import get_admin_message, get_protected_message, get_public_message

auth_blueprint = func.Blueprint()


@auth_blueprint.route(route="public", methods=["GET"], auth_level=func.AuthLevel.ANONYMOUS)
def public_endpoint(req: func.HttpRequest) -> func.HttpResponse:
    del req
    return func.HttpResponse(get_public_message())


@auth_blueprint.route(route="protected", methods=["GET"], auth_level=func.AuthLevel.FUNCTION)
def protected_endpoint(req: func.HttpRequest) -> func.HttpResponse:
    del req
    return func.HttpResponse(get_protected_message())


@auth_blueprint.route(route="admin-only", methods=["GET"], auth_level=func.AuthLevel.ADMIN)
def admin_endpoint(req: func.HttpRequest) -> func.HttpResponse:
    del req
    return func.HttpResponse(get_admin_message())
