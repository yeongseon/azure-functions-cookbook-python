from __future__ import annotations

import logging

import azure.functions as func

from app.services.auth_service import (
    decode_client_principal,
    get_admin_response,
    get_user_claims_response,
    json_response,
)

auth_blueprint = func.Blueprint()


@auth_blueprint.route(
    route="auth/me", methods=["GET"], auth_level=func.AuthLevel.ANONYMOUS
)
def auth_me(req: func.HttpRequest) -> func.HttpResponse:
    """Return the decoded EasyAuth principal claims."""
    header = req.headers.get("X-MS-CLIENT-PRINCIPAL")
    principal = decode_client_principal(header)
    if principal is None:
        logging.warning("No X-MS-CLIENT-PRINCIPAL header found.")
        return json_response(
            {"error": "Not authenticated. Missing X-MS-CLIENT-PRINCIPAL header."},
            status_code=401,
        )

    body, status_code = get_user_claims_response(principal)
    return json_response(body, status_code=status_code)


@auth_blueprint.route(
    route="auth/admin", methods=["GET"], auth_level=func.AuthLevel.ANONYMOUS
)
def auth_admin(req: func.HttpRequest) -> func.HttpResponse:
    """Return admin-only content after role check."""
    header = req.headers.get("X-MS-CLIENT-PRINCIPAL")
    principal = decode_client_principal(header)
    if principal is None:
        logging.warning("No X-MS-CLIENT-PRINCIPAL header found.")
        return json_response(
            {"error": "Not authenticated. Missing X-MS-CLIENT-PRINCIPAL header."},
            status_code=401,
        )

    body, status_code = get_admin_response(principal)
    return json_response(body, status_code=status_code)
