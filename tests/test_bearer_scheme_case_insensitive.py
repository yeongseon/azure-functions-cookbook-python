"""Regression coverage for #359: parse the bearer scheme case-insensitively.

extract_bearer_token() only accepted the exact prefix "Bearer ". RFC 9110
section 11.1 defines HTTP authentication scheme names as case-insensitive,
so "bearer <token>" and mixed-case spellings are equally valid but were
rejected as malformed before JWT validation ran.

Exercises the actual registered handlers; only the external JWT/JWKS
validation boundary (validate_jwt) is replaced by a deterministic mock, via
the handler module's own globals, matching the issue's own probe. No
signature bypass or network request is involved -- the token content
itself must still reach validate_jwt unchanged.
"""

from __future__ import annotations

from collections.abc import Callable
from unittest.mock import Mock, patch

import azure.functions as func

from tests._isolation import import_function_module, load_example_module

EXAMPLE_PATH = "apis-and-ingress/auth_jwt_validation"

Handler = Callable[[func.HttpRequest], func.HttpResponse]


def _request(authorization: str) -> func.HttpRequest:
    return func.HttpRequest(
        method="GET",
        url="https://example.invalid/api/auth/profile",
        params={},
        body=b"",
        headers={"Authorization": authorization},
    )


def _handlers() -> tuple[Handler, Handler]:
    load_example_module(EXAMPLE_PATH)
    auth_module = import_function_module(EXAMPLE_PATH, "app.functions.auth")
    profile: Handler = auth_module.auth_profile.build().get_user_function()
    protected: Handler = auth_module.auth_protected.build().get_user_function()
    return profile, protected


def test_bearer_scheme_accepted_case_insensitively_for_both_routes() -> None:
    profile_handler, protected_handler = _handlers()

    for handler in (profile_handler, protected_handler):
        for scheme in ("Bearer", "bearer", "bEaReR"):
            validator = Mock(return_value={"sub": "one", "roles": ["api.read"]})
            with patch.dict(handler.__globals__, {"validate_jwt": validator}):
                response = handler(_request(f"{scheme} AbCd.Token"))

            assert response.status_code == 200
            validator.assert_called_once()
            assert validator.call_args.args[0] == "AbCd.Token"


def test_unsupported_scheme_still_rejected() -> None:
    profile_handler, _ = _handlers()
    validator = Mock(return_value={"sub": "one"})

    with patch.dict(profile_handler.__globals__, {"validate_jwt": validator}):
        response = profile_handler(_request("Basic AbCd.Token"))

    assert response.status_code == 401
    validator.assert_not_called()


def test_missing_authorization_header_still_rejected() -> None:
    profile_handler, _ = _handlers()
    validator = Mock(return_value={"sub": "one"})

    with patch.dict(profile_handler.__globals__, {"validate_jwt": validator}):
        req = func.HttpRequest(
            method="GET", url="https://example.invalid/api/auth/profile", params={}, body=b""
        )
        response = profile_handler(req)

    assert response.status_code == 401
    validator.assert_not_called()


def test_cryptographically_invalid_token_still_rejected() -> None:
    profile_handler, _ = _handlers()
    validator = Mock(return_value=None)

    with patch.dict(profile_handler.__globals__, {"validate_jwt": validator}):
        response = profile_handler(_request("Bearer bad.token"))

    assert response.status_code == 401
    validator.assert_called_once()
