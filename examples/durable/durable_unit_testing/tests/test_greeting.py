from app.services.greeting_service import greet


def test_greet_returns_expected_message() -> None:
    assert greet("Seattle") == "Hello Seattle!"
