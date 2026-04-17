from __future__ import annotations

import logging
import os

import azure.functions as func

from app.services.tenant_service import (
    _json_response,
    decode_client_principal,
    extract_tenant_id,
    get_data_response,
    is_tenant_allowed,
    parse_allowed_tenants,
)

auth_blueprint = func.Blueprint()


@auth_blueprint.route(route="auth/data", methods=["GET"], auth_level=func.AuthLevel.ANONYMOUS)
def auth_data(req: func.HttpRequest) -> func.HttpResponse:
    """Return tenant-scoped data after tenant allowlist check."""
    header = req.headers.get("X-MS-CLIENT-PRINCIPAL")
    principal = decode_client_principal(header)
    if principal is None:
        logging.warning("No X-MS-CLIENT-PRINCIPAL header found.")
        return _json_response(
            {"error": "Not authenticated. Missing X-MS-CLIENT-PRINCIPAL header."},
            status_code=401,
        )

    tenant_id = extract_tenant_id(principal)
    if not tenant_id:
        logging.warning("No tenant ID found in principal claims.")
        return _json_response(
            {"error": "No tenant ID (tid) found in token claims."},
            status_code=403,
        )

    allowed_raw = os.environ.get("ALLOWED_TENANT_IDS", "")
    allowed_tenants = parse_allowed_tenants(allowed_raw)

    if not is_tenant_allowed(tenant_id, allowed_tenants):
        logging.warning("Tenant %s is not in the allowlist.", tenant_id)
        return _json_response(
            {"error": f"Tenant '{tenant_id}' is not authorized."},
            status_code=403,
        )

    body, status_code = get_data_response(principal, tenant_id)
    return _json_response(body, status_code=status_code)
