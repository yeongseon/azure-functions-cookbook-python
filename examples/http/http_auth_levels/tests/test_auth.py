from app.services.auth_service import get_admin_message, get_protected_message, get_public_message


def test_public_message() -> None:
    assert get_public_message() == "This endpoint is public (anonymous)."


def test_protected_message() -> None:
    assert get_protected_message() == "This endpoint requires a function key."


def test_admin_message() -> None:
    assert get_admin_message() == "This endpoint requires the admin/master key."
