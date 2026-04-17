from __future__ import annotations

import base64
import json
from collections.abc import Callable
from functools import wraps
from typing import TypeAlias, TypedDict, TypeVar, cast

import azure.functions as func


class Claim(TypedDict):
    typ: str
    val: str


class Principal(TypedDict):
    """Azure App Service EasyAuth client principal.

    Matches the ``X-MS-CLIENT-PRINCIPAL`` header structure described at
    https://learn.microsoft.com/azure/app-service/configure-authentication-user-identities
    """

    auth_typ: str
    name_typ: str
    role_typ: str
    claims: list[Claim]


ResponseBody: TypeAlias = dict[str, object]
ServiceResponse: TypeAlias = tuple[ResponseBody, int]
ServiceHandler: TypeAlias = Callable[[Principal], ServiceResponse]
HandlerT = TypeVar("HandlerT", bound=ServiceHandler)


def json_response(body: object, status_code: int = 200) -> func.HttpResponse:
    return func.HttpResponse(
        body=json.dumps(body),
        status_code=status_code,
        mimetype="application/json",
    )


def decode_client_principal(header_value: str | None) -> Principal | None:
    """Decode the X-MS-CLIENT-PRINCIPAL header from base64 JSON.

    Returns the parsed principal dict, or None if the header is missing or invalid.
    The expected JSON structure contains ``auth_typ``, ``name_typ``, ``role_typ``
    and a ``claims`` array of ``{"typ": ..., "val": ...}`` objects.
    """
    if not header_value:
        return None
    try:
        decoded = base64.b64decode(header_value)
        parsed_obj: object = json.loads(decoded.decode("utf-8"))
    except (ValueError, json.JSONDecodeError):
        return None
    if not isinstance(parsed_obj, dict):
        return None

    parsed = cast(dict[str, object], parsed_obj)

    auth_typ = parsed.get("auth_typ", "")
    name_typ = parsed.get("name_typ", "")
    role_typ = parsed.get("role_typ", "")
    raw_claims = parsed.get("claims", [])

    if not isinstance(auth_typ, str):
        return None
    if not isinstance(raw_claims, list):
        return None

    claims: list[Claim] = []
    for claim_obj in raw_claims:
        if not isinstance(claim_obj, dict):
            continue
        claim = cast(dict[str, object], claim_obj)
        typ = claim.get("typ")
        val = claim.get("val")
        if isinstance(typ, str) and isinstance(val, str):
            claims.append({"typ": typ, "val": val})

    return {
        "auth_typ": auth_typ,
        "name_typ": name_typ if isinstance(name_typ, str) else "",
        "role_typ": role_typ if isinstance(role_typ, str) else "",
        "claims": claims,
    }


def extract_claims(principal: Principal) -> dict[str, str]:
    """Extract claims from the principal into a flat dict.

    The principal JSON has a ``claims`` array of ``{"typ": ..., "val": ...}`` objects.
    """
    claims: dict[str, str] = {}
    for claim in principal.get("claims", []):
        typ = claim.get("typ", "")
        val = claim.get("val", "")
        if typ:
            claims[typ] = val
    return claims


def get_claim_value(principal: Principal, claim_type: str) -> str | None:
    """Get the first value for a claim type, or None if not found."""
    for claim in principal.get("claims", []):
        if claim.get("typ") == claim_type:
            return claim.get("val", "")
    return None


def get_roles(principal: Principal) -> list[str]:
    """Extract role claims from the principal.

    Roles are claims with typ ``roles`` or
    ``http://schemas.microsoft.com/ws/2008/06/identity/claims/role``.
    """
    claims = principal.get("claims", [])
    roles: list[str] = []
    for claim in claims:
        typ = claim.get("typ", "")
        if typ in ("roles", "http://schemas.microsoft.com/ws/2008/06/identity/claims/role"):
            val = claim.get("val", "")
            if val:
                roles.append(val)
    return roles


def has_role(principal: Principal, role: str) -> bool:
    """Check whether the principal has a specific role."""
    return role in get_roles(principal)


def require_role(role: str) -> Callable[[HandlerT], HandlerT]:
    """Enforce role-based access for service handlers."""

    def decorator(handler: HandlerT) -> HandlerT:
        @wraps(handler)
        def wrapper(principal: Principal) -> ServiceResponse:
            if not has_role(principal, role):
                return {"error": f"Forbidden. Role '{role}' is required."}, 403
            return handler(principal)

        return cast(HandlerT, wrapper)

    return decorator


def get_user_claims_response(principal: Principal) -> ServiceResponse:
    """Build the response body for the /auth/me endpoint."""
    claims = extract_claims(principal)
    roles = get_roles(principal)
    return {
        "identity_provider": principal.get("auth_typ", "unknown"),
        "user_id": get_claim_value(
            principal,
            "http://schemas.xmlsoap.org/ws/2005/05/identity/claims/nameidentifier",
        )
        or "unknown",
        "claims": claims,
        "roles": roles,
    }, 200


@require_role("admin")
def get_admin_response(principal: Principal) -> ServiceResponse:
    """Build the response body for the /auth/admin endpoint.

    Returns 403 if user lacks the ``admin`` role.
    """
    return {
        "message": "Welcome, admin!",
        "user_id": get_claim_value(
            principal,
            "http://schemas.xmlsoap.org/ws/2005/05/identity/claims/nameidentifier",
        )
        or "unknown",
    }, 200
