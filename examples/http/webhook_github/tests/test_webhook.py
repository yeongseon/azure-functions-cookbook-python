import hashlib
import hmac

from app.services.webhook_service import (
    _handle_issues,
    _handle_pull_request,
    _handle_push,
    _is_signature_valid,
)


def test_is_signature_valid_accepts_matching_signature() -> None:
    secret = "topsecret"
    payload = b'{"event":"push"}'
    signature = "sha256=" + hmac.new(secret.encode("utf-8"), payload, hashlib.sha256).hexdigest()

    assert _is_signature_valid(signature, payload, secret) is True


def test_is_signature_valid_rejects_wrong_signature() -> None:
    assert _is_signature_valid("sha256=bad", b"{}", "topsecret") is False


def test_handle_push_returns_expected_payload() -> None:
    result = _handle_push(
        {
            "repository": {"full_name": "octo/repo"},
            "ref": "refs/heads/main",
            "commits": [{}, {}],
        }
    )

    assert result["event"] == "push"
    assert result["repository"] == "octo/repo"
    assert result["commits"] == 2


def test_handle_pull_request_returns_expected_payload() -> None:
    result = _handle_pull_request(
        {
            "action": "opened",
            "pull_request": {"number": 10, "title": "Add feature"},
        }
    )

    assert result["event"] == "pull_request"
    assert result["number"] == 10


def test_handle_issues_returns_expected_payload() -> None:
    result = _handle_issues(
        {
            "action": "opened",
            "issue": {"number": 5, "title": "Bug report"},
        }
    )

    assert result["event"] == "issues"
    assert result["number"] == 5
