from __future__ import annotations

import json

import azure.durable_functions as df
import azure.functions as func

from app.services.counter_service import apply_counter_operation

bp = df.Blueprint()


@bp.entity_trigger(context_name="context")
def counter_entity(context: df.DurableEntityContext) -> None:
    current_value = context.get_state(lambda: 0)
    operation = context.operation_name or ""
    raw_amount = context.get_input()
    amount = int(raw_amount) if raw_amount is not None else None

    next_state, result = apply_counter_operation(current_value, operation, amount)
    if operation in {"add", "reset"}:
        context.set_state(next_state)
    context.set_result(result)


@bp.route(
    route="counter/{operation}",
    methods=["POST"],
    auth_level=func.AuthLevel.ANONYMOUS,
)
@bp.durable_client_input(client_name="client")
async def signal_counter(
    req: func.HttpRequest,
    client: df.DurableOrchestrationClient,
) -> func.HttpResponse:
    operation = req.route_params["operation"]
    entity_id = df.EntityId("counter_entity", "counter")

    amount_param = req.params.get("value")
    value: int | None = int(amount_param) if amount_param is not None else None

    if value is None and req.get_body():
        parsed_body = json.loads(req.get_body().decode("utf-8"))
        if isinstance(parsed_body, dict) and "value" in parsed_body:
            value = int(parsed_body["value"])

    signal_value = value if operation == "add" else None
    await client.signal_entity(entity_id, operation, signal_value)
    return func.HttpResponse(
        f"Signaled '{operation}' operation for durable entity '{entity_id.name}'.",
    )


@bp.route(route="counter", methods=["GET"], auth_level=func.AuthLevel.ANONYMOUS)
@bp.durable_client_input(client_name="client")
async def get_counter(
    req: func.HttpRequest,
    client: df.DurableOrchestrationClient,
) -> func.HttpResponse:
    del req
    entity_id = df.EntityId("counter_entity", "counter")
    state_response = await client.read_entity_state(entity_id)

    if not state_response.entity_exists:
        return func.HttpResponse(
            json.dumps({"value": 0}),
            mimetype="application/json",
            status_code=200,
        )

    return func.HttpResponse(
        json.dumps({"value": state_response.entity_state}),
        mimetype="application/json",
        status_code=200,
    )
