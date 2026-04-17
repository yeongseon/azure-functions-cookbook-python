from app.services.health_service import get_health_payload


def test_get_health_payload() -> None:
    assert get_health_payload() == {"status": "healthy"}
