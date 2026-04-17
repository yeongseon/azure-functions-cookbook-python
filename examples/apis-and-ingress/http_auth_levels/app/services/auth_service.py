from __future__ import annotations


def get_public_message() -> str:
    return "This endpoint is public (anonymous)."


def get_protected_message() -> str:
    return "This endpoint requires a function key."


def get_admin_message() -> str:
    return "This endpoint requires the admin/master key."
