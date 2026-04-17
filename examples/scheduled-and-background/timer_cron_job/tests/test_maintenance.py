from app.services.maintenance_service import perform_maintenance


def test_perform_maintenance_returns_expected_summary() -> None:
    assert perform_maintenance() == "Maintenance complete - 0 stale entries purged"
