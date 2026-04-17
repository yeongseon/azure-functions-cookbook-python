import base64
import json

from app.services.auth_service import (
    Claim,
    Principal,
    decode_client_principal,
    extract_claims,
    get_admin_response,
    get_claim_value,
    get_roles,
    get_user_claims_response,
    has_role,
)


def _make_principal(
    claims: list[Claim] | None = None,
    auth_typ: str = "aad",
    name_typ: str = "http://schemas.xmlsoap.org/ws/2005/05/identity/claims/name",
    role_typ: str = "http://schemas.microsoft.com/ws/2008/06/identity/claims/role",
) -> Principal:
    return {
        "auth_typ": auth_typ,
        "name_typ": name_typ,
        "role_typ": role_typ,
        "claims": claims or [],
    }


def _encode_principal(principal: Principal) -> str:
    return base64.b64encode(json.dumps(principal).encode()).decode()


def test_decode_client_principal_valid() -> None:
    principal = _make_principal()
    encoded = _encode_principal(principal)
    result = decode_client_principal(encoded)
    assert result is not None
    assert result["auth_typ"] == "aad"


def test_decode_client_principal_none() -> None:
    assert decode_client_principal(None) is None


def test_decode_client_principal_empty_string() -> None:
    assert decode_client_principal("") is None


def test_decode_client_principal_invalid_base64() -> None:
    assert decode_client_principal("not-valid-base64!!!") is None


def test_decode_client_principal_non_dict() -> None:
    """Non-dict JSON (e.g. array) should return None."""
    encoded = base64.b64encode(json.dumps([1, 2, 3]).encode()).decode()
    assert decode_client_principal(encoded) is None


def test_decode_client_principal_non_string_json() -> None:
    """A base64-encoded JSON string should return None."""
    encoded = base64.b64encode(b'"just-a-string"').decode()
    assert decode_client_principal(encoded) is None


def test_extract_claims() -> None:
    principal = _make_principal(
        claims=[
            {"typ": "name", "val": "Alice"},
            {"typ": "email", "val": "alice@example.com"},
        ]
    )
    claims = extract_claims(principal)
    assert claims["name"] == "Alice"
    assert claims["email"] == "alice@example.com"


def test_get_claim_value() -> None:
    principal = _make_principal(
        claims=[
            {"typ": "http://schemas.xmlsoap.org/ws/2005/05/identity/claims/nameidentifier", "val": "user-1"},
            {"typ": "name", "val": "Alice"},
        ]
    )
    assert get_claim_value(principal, "http://schemas.xmlsoap.org/ws/2005/05/identity/claims/nameidentifier") == "user-1"
    assert get_claim_value(principal, "name") == "Alice"
    assert get_claim_value(principal, "missing") is None


def test_get_roles() -> None:
    principal = _make_principal(
        claims=[
            {"typ": "roles", "val": "admin"},
            {"typ": "roles", "val": "reader"},
            {"typ": "name", "val": "Alice"},
        ]
    )
    roles = get_roles(principal)
    assert "admin" in roles
    assert "reader" in roles
    assert len(roles) == 2


def test_has_role_true() -> None:
    principal = _make_principal(claims=[{"typ": "roles", "val": "admin"}])
    assert has_role(principal, "admin") is True


def test_has_role_false() -> None:
    principal = _make_principal(claims=[{"typ": "roles", "val": "reader"}])
    assert has_role(principal, "admin") is False


def test_get_user_claims_response() -> None:
    principal = _make_principal(
        claims=[
            {"typ": "name", "val": "Alice"},
            {"typ": "http://schemas.xmlsoap.org/ws/2005/05/identity/claims/nameidentifier", "val": "user-1"},
        ]
    )
    body, status = get_user_claims_response(principal)
    assert status == 200
    assert body["identity_provider"] == "aad"
    assert body["user_id"] == "user-1"
    claims = body["claims"]
    assert isinstance(claims, dict)
    assert claims["name"] == "Alice"


def test_get_admin_response_with_admin_role() -> None:
    principal = _make_principal(
        claims=[
            {"typ": "roles", "val": "admin"},
            {"typ": "http://schemas.xmlsoap.org/ws/2005/05/identity/claims/nameidentifier", "val": "user-1"},
        ]
    )
    body, status = get_admin_response(principal)
    assert status == 200
    assert body["message"] == "Welcome, admin!"
    assert body["user_id"] == "user-1"


def test_get_admin_response_without_admin_role() -> None:
    principal = _make_principal(claims=[{"typ": "roles", "val": "reader"}])
    body, status = get_admin_response(principal)
    assert status == 403
    error = body["error"]
    assert isinstance(error, str)
    assert "Forbidden" in error
    assert "'admin'" in error
