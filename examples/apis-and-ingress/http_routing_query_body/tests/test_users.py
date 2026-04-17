from app.services import user_service


def reset_users() -> None:
    user_service.USERS.clear()
    user_service.USERS.update(
        {
            "1": {"id": "1", "name": "Ada Lovelace", "email": "ada@example.com"},
            "2": {"id": "2", "name": "Grace Hopper", "email": "grace@example.com"},
        }
    )


def test_list_all_users_returns_seeded_users() -> None:
    reset_users()

    result = user_service.list_all_users()

    assert len(result["users"]) == 2


def test_get_user_by_id_returns_none_for_missing_user() -> None:
    reset_users()

    result = user_service.get_user_by_id("404")

    assert result is None


def test_create_user_creates_new_user() -> None:
    reset_users()

    body, status = user_service.create_user({"name": "Linus", "email": "linus@example.com"})

    assert status == 201
    assert body["name"] == "Linus"


def test_update_user_returns_not_found_for_missing_user() -> None:
    reset_users()

    body, status = user_service.update_user("404", {"name": "Nope"})

    assert status == 404
    assert body == {"error": "User '404' not found."}


def test_delete_user_removes_existing_user() -> None:
    reset_users()

    _, status = user_service.delete_user("1")

    assert status == 204
    assert user_service.get_user_by_id("1") is None


def test_search_users_respects_limit() -> None:
    reset_users()

    result = user_service.search_users("example.com", 1)

    assert result["q"] == "example.com"
    assert result["limit"] == 1
    assert len(result["results"]) == 1
