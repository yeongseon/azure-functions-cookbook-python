from app.services import user_service


def test_user_crud() -> None:
    user_service._users.clear()
    assert user_service.list_users() == []
    assert user_service.get_user("u1") is None

    created = user_service.create_user(user_id="u1", name="Ada")
    assert created == {"id": "u1", "name": "Ada"}
    assert user_service.get_user("u1") == {"id": "u1", "name": "Ada"}
    assert user_service.list_users() == [{"id": "u1", "name": "Ada"}]
