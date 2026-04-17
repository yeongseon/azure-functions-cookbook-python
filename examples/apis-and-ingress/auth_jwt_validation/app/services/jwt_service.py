from __future__ import annotations

import json
import logging
from collections.abc import Callable
from typing import Any

import azure.functions as func
import jwt
from jwt import PyJWKClient

ClaimsResponse = tuple[dict[str, Any], int]
ClaimsHandler = Callable[[dict[str, Any]], ClaimsResponse]


def _json_response(body: object, status_code: int = 200) -> func.HttpResponse:
    return func.HttpResponse(
        body=json.dumps(body),
        status_code=status_code,
        mimetype="application/json",
    )


def extract_bearer_token(auth_header: str | None) -> str | None:
    """Extract the token from an Authorization: Bearer <token> header."""
    if not auth_header or not auth_header.startswith("Bearer "):
        return None
    token = auth_header[7:].strip()
    return token if token else None


def validate_jwt(
    token: str,
    *,
    tenant_id: str,
    audience: str,
    jwks_uri: str | None = None,
) -> dict[str, Any] | None:
    """Validate a JWT token against Azure AD JWKS endpoint.

    Returns decoded claims dict on success, or None on any validation failure.
    """
    if not tenant_id or not audience:
        logging.error("AZURE_TENANT_ID and AZURE_CLIENT_ID must be configured.")
        return None

    if jwks_uri is None:
        jwks_uri = (
            f"https://login.microsoftonline.com/{tenant_id}/discovery/v2.0/keys"
        )

    try:
        jwks_client = PyJWKClient(jwks_uri, cache_keys=True)
        signing_key = jwks_client.get_signing_key_from_jwt(token)
        decoded = jwt.decode(
            token,
            signing_key.key,
            algorithms=["RS256"],
            audience=audience,
            issuer=f"https://login.microsoftonline.com/{tenant_id}/v2.0",
        )
        return decoded
    except (jwt.InvalidTokenError, jwt.PyJWKClientError) as exc:
        logging.warning("JWT validation error: %s", exc)
        return None


def has_claim(claims: dict[str, Any], claim_name: str, expected_value: str | None = None) -> bool:
    """Check whether claims contain a specific claim with an optional expected value.

    Handles both string and boolean claim values by normalizing to string comparison.
    """
    if claim_name not in claims:
        return False
    if expected_value is not None:
        val = claims[claim_name]
        if isinstance(val, bool):
            return str(val).lower() == expected_value.lower()
        return str(val) == expected_value
    return True


def require_claim(
    claim_name: str,
    expected_value: str | None = None,
) -> Callable[[ClaimsHandler], ClaimsHandler]:
    """Decorator for claim-based authorization on response builders."""

    def decorator(handler: ClaimsHandler) -> ClaimsHandler:
        def wrapper(claims: dict[str, Any]) -> ClaimsResponse:
            if not has_claim(claims, claim_name, expected_value):
                return {
                    "error": (
                        f"Forbidden. Claim '{claim_name}'"
                        f" must be '{expected_value}'."
                    )
                }, 403
            return handler(claims)

        return wrapper

    return decorator


def get_profile_response(claims: dict[str, Any]) -> tuple[dict[str, Any], int]:
    """Build the response body for the /auth/profile endpoint."""
    return {
        "subject": claims.get("sub", "unknown"),
        "name": claims.get("name", "unknown"),
        "email": claims.get("email", claims.get("preferred_username", "unknown")),
        "claims": {k: v for k, v in claims.items() if k not in ("iat", "exp", "nbf")},
    }, 200


@require_claim("roles", "api.read")
def get_protected_response(claims: dict[str, Any]) -> tuple[dict[str, Any], int]:
    """Build the response body for the /auth/protected endpoint.

    Requires the ``roles`` claim to contain ``api.read``.
    """
    return {
        "message": "Access granted to protected resource.",
        "subject": claims.get("sub", "unknown"),
    }, 200
