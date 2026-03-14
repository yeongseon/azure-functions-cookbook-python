from app.services.queue_service import process_queue_message


def test_process_queue_message() -> None:
    result = process_queue_message("order-1")
    assert result == "Received queue message through StorageConnection: order-1"
