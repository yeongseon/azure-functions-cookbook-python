from __future__ import annotations


def process_servicebus_message(payload: str) -> str:
    return f"Received Service Bus message through ServiceBusConnection: {payload}"
