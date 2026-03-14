from app.services.servicebus_service import process_servicebus_message


def test_process_servicebus_message() -> None:
    result = process_servicebus_message("order-123")
    assert result == "Received Service Bus message through ServiceBusConnection: order-123"
