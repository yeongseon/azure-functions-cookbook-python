from __future__ import annotations

import logging

import azure.functions as func

from app.services.servicebus_service import process_servicebus_message

sb_identity_blueprint = func.Blueprint()


@sb_identity_blueprint.function_name(name="servicebus_queue_trigger_identity")
@sb_identity_blueprint.service_bus_queue_trigger(
    arg_name="message",
    queue_name="orders",
    connection="ServiceBusConnection",
)
def servicebus_queue_trigger_identity(message: func.ServiceBusMessage) -> None:
    payload = message.get_body().decode("utf-8")
    logging.info(process_servicebus_message(payload))
