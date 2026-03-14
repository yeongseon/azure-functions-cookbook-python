from app.services.change_service import process_change


def test_process_change_returns_expected_summary() -> None:
    change = {"id": "42", "category": "inventory"}

    outcome = process_change(change)

    assert outcome == "id=42 category=inventory status=synced"
