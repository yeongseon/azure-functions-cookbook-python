from app.services.jwt_service import (
    extract_bearer_token,
    get_profile_response,
    get_protected_response,
    has_claim,
)


def test_extract_bearer_token_valid() -> None:
    assert extract_bearer_token("Bearer eyJhbG.test.token") == "eyJhbG.test.token"


def test_extract_bearer_token_missing() -> None:
    assert extract_bearer_token(None) is None


def test_extract_bearer_token_no_bearer_prefix() -> None:
    assert extract_bearer_token("Basic dXNlcjpwYXNz") is None


def test_extract_bearer_token_empty_token() -> None:
    assert extract_bearer_token("Bearer ") is None


def test_extract_bearer_token_lowercase_bearer() -> None:
    """Lowercase 'bearer' prefix should not be accepted (case-sensitive)."""
    assert extract_bearer_token("bearer abc123") is None


def test_has_claim_present() -> None:
    claims = {"sub": "user-1", "email": "alice@example.com"}
    assert has_claim(claims, "sub") is True


def test_has_claim_missing() -> None:
    claims = {"sub": "user-1"}
    assert has_claim(claims, "email") is False


def test_has_claim_with_expected_value_match() -> None:
    claims = {"roles": "api.read"}
    assert has_claim(claims, "roles", "api.read") is True


def test_has_claim_with_expected_value_mismatch() -> None:
    claims = {"roles": "api.write"}
    assert has_claim(claims, "roles", "api.read") is False


def test_has_claim_with_boolean_true() -> None:
    """Boolean True claim should match string 'true'."""
    claims = {"email_verified": True}
    assert has_claim(claims, "email_verified", "true") is True


def test_has_claim_with_boolean_false() -> None:
    """Boolean False claim should match string 'false'."""
    claims = {"email_verified": False}
    assert has_claim(claims, "email_verified", "false") is True
    assert has_claim(claims, "email_verified", "true") is False


def test_get_profile_response() -> None:
    claims = {"sub": "user-1", "name": "Alice", "email": "alice@example.com", "iat": 123}
    body, status = get_profile_response(claims)
    assert status == 200
    assert body["subject"] == "user-1"
    assert body["name"] == "Alice"
    assert "iat" not in body["claims"]


def test_get_protected_response_with_required_role() -> None:
    claims = {"sub": "user-1", "roles": "api.read"}
    body, status = get_protected_response(claims)
    assert status == 200
    assert body["message"] == "Access granted to protected resource."


def test_get_protected_response_wrong_role() -> None:
    claims = {"sub": "user-1", "roles": "api.write"}
    body, status = get_protected_response(claims)
    assert status == 403
    assert "Forbidden" in body["error"]


def test_get_protected_response_missing_claim() -> None:
    claims = {"sub": "user-1"}
    body, status = get_protected_response(claims)
    assert status == 403
