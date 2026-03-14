from app.services.data_service import fetch_data


def test_fetch_data_returns_expected_result() -> None:
    assert fetch_data("resource-1") == "I/O completed for resource-1"
