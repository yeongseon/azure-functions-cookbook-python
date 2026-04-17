import base64
import json

from app.services.tenant_service import (
    decode_client_principal,
    extract_tenant_id,
    get_data_response,
    is_tenant_allowed,
    parse_allowed_tenants,
)


def _make_principal(
    claims: list[dict[str, str]] | None = None,
    auth_typ: str = "aad",
) -> dict[str, object]:
    return {
        "auth_typ": auth_typ,
        "name_typ": "http://schemas.xmlsoap.org/ws/2005/05/identity/claims/name",
        "role_typ": "http://schemas.microsoft.com/ws/2008/06/identity/claims/role",
        "claims": claims or [],
    }


def _encode_principal(principal: dict[str, object]) -> str:
    return base64.b64encode(json.dumps(principal).encode()).decode()


def test_decode_client_principal_valid() -> None:
    principal = _make_principal()
    encoded = _encode_principal(principal)
    result = decode_client_principal(encoded)
    assert result is not None
    assert result["auth_typ"] == "aad"


def test_decode_client_principal_none() -> None:
    assert decode_client_principal(None) is None


def test_decode_client_principal_invalid() -> None:
    assert decode_client_principal("not-valid!!!") is None


def test_decode_client_principal_non_dict() -> None:
    """Non-dict JSON (e.g. array) should return None."""
    encoded = base64.b64encode(json.dumps([1, 2, 3]).encode()).decode()
    assert decode_client_principal(encoded) is None


def test_decode_client_principal_string_json() -> None:
    """A base64-encoded JSON string should return None."""
    encoded = base64.b64encode(b'"just-a-string"').decode()
    assert decode_client_principal(encoded) is None


def test_extract_tenant_id_with_tid() -> None:
    principal = _make_principal(claims=[{"typ": "tid", "val": "tenant-abc"}])
    assert extract_tenant_id(principal) == "tenant-abc"


def test_extract_tenant_id_with_long_form() -> None:
    principal = _make_principal(claims=[
        {"typ": "http://schemas.microsoft.com/identity/claims/tenantid", "val": "tenant-xyz"},
    ])
    assert extract_tenant_id(principal) == "tenant-xyz"


def test_extract_tenant_id_missing() -> None:
    principal = _make_principal(claims=[{"typ": "name", "val": "Alice"}])
    assert extract_tenant_id(principal) is None


def test_extract_tenant_id_non_dict_claim() -> None:
    """Non-dict claim entries should be safely skipped."""
    principal: dict[str, object] = {
        "auth_typ": "aad",
        "claims": ["not-a-dict", {"typ": "tid", "val": "tenant-abc"}],
    }
    assert extract_tenant_id(principal) == "tenant-abc"


def test_parse_allowed_tenants() -> None:
    result = parse_allowed_tenants("tenant-a, tenant-b, tenant-c")
    assert result == ["tenant-a", "tenant-b", "tenant-c"]


def test_parse_allowed_tenants_empty() -> None:
    assert parse_allowed_tenants("") == []


def test_parse_allowed_tenants_with_blanks() -> None:
    result = parse_allowed_tenants("tenant-a,,, tenant-b,")
    assert result == ["tenant-a", "tenant-b"]


def test_is_tenant_allowed_true() -> None:
    assert is_tenant_allowed("tenant-a", ["tenant-a", "tenant-b"]) is True


def test_is_tenant_allowed_false() -> None:
    assert is_tenant_allowed("tenant-c", ["tenant-a", "tenant-b"]) is False


def test_is_tenant_allowed_empty_list() -> None:
    assert is_tenant_allowed("tenant-a", []) is False


def test_get_data_response() -> None:
    principal = _make_principal(
        claims=[
            {"typ": "http://schemas.xmlsoap.org/ws/2005/05/identity/claims/nameidentifier", "val": "user-1"},
        ]
    )
    body, status = get_data_response(principal, "tenant-abc")
    assert status == 200
    assert body["tenant_id"] == "tenant-abc"
    assert body["user_id"] == "user-1"
    assert body["identity_provider"] == "aad"
    assert body["message"] == "Access granted."
