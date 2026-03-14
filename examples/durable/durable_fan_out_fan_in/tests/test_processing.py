from app.services.processing_service import process_item


def test_process_item_returns_expected_value() -> None:
    assert process_item("item-3") == "Processed item-3"
