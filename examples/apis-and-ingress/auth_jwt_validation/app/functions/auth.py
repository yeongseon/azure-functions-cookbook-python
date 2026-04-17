from __future__ import annotations

import logging
import os

import azure.functions as func

from app.services.jwt_service import (
    _json_response,
    extract_bearer_token,
    get_profile_response,
    get_protected_response,
    validate_jwt,
)

auth_blueprint = func.Blueprint()


@auth_blueprint.route(route="auth/profile", methods=["GET"], auth_level=func.AuthLevel.ANONYMOUS)
def auth_profile(req: func.HttpRequest) -> func.HttpResponse:
    """Return decoded JWT claims from the Bearer token."""
    token = extract_bearer_token(req.headers.get("Authorization"))
    if token is None:
        logging.warning("Missing or malformed Authorization header.")
        return _json_response(
            {"error": "Missing or malformed Authorization header. Expected: Bearer <token>."},
            status_code=401,
        )

    tenant_id = os.environ.get("AZURE_TENANT_ID", "")
    audience = os.environ.get("AZURE_CLIENT_ID", "")
    claims = validate_jwt(token, tenant_id=tenant_id, audience=audience)
    if claims is None:
        logging.warning("JWT validation failed.")
        return _json_response({"error": "Invalid or expired token."}, status_code=401)

    body, status_code = get_profile_response(claims)
    return _json_response(body, status_code=status_code)


@auth_blueprint.route(
    route="auth/protected", methods=["GET"], auth_level=func.AuthLevel.ANONYMOUS
)
def auth_protected(req: func.HttpRequest) -> func.HttpResponse:
    """Return protected content after verifying email claim."""
    token = extract_bearer_token(req.headers.get("Authorization"))
    if token is None:
        logging.warning("Missing or malformed Authorization header.")
        return _json_response(
            {"error": "Missing or malformed Authorization header. Expected: Bearer <token>."},
            status_code=401,
        )

    tenant_id = os.environ.get("AZURE_TENANT_ID", "")
    audience = os.environ.get("AZURE_CLIENT_ID", "")
    claims = validate_jwt(token, tenant_id=tenant_id, audience=audience)
    if claims is None:
        logging.warning("JWT validation failed.")
        return _json_response({"error": "Invalid or expired token."}, status_code=401)

    body, status_code = get_protected_response(claims)
    return _json_response(body, status_code=status_code)
