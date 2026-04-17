# pyright: reportMissingImports=false, reportUnknownVariableType=false, reportUnknownMemberType=false, reportUnknownParameterType=false, reportUnknownArgumentType=false, reportUntypedFunctionDecorator=false, reportAny=false, reportExplicitAny=false

from __future__ import annotations

from collections.abc import Generator
from typing import Any, TypedDict, cast

import azure.durable_functions as df
import azure.functions as func
from azure_functions_logging import get_logger, setup_logging, with_context

setup_logging(format="json")
logger = get_logger(__name__)

app = df.DFApp(http_auth_level=func.AuthLevel.ANONYMOUS)


class WorkflowInput(TypedDict):
    customer_id: str
    customer_segment: str
    skus: list[str]


class CustomerSyncResult(TypedDict):
    step: str
    customerId: str
    segment: str
    status: str


class InventorySyncResult(TypedDict):
    step: str
    skuCount: int
    skus: list[str]
    status: str


class ParentWorkflowResult(TypedDict):
    instanceId: str
    customer: CustomerSyncResult
    inventory: InventorySyncResult
    status: str


DEFAULT_INPUT: WorkflowInput = {
    "customer_id": "cust-1001",
    "customer_segment": "enterprise",
    "skus": ["SKU-100", "SKU-200"],
}


def _build_input(req: func.HttpRequest) -> WorkflowInput:
    try:
        payload = req.get_json()
    except ValueError:
        payload = {}

    workflow_input: WorkflowInput = {
        "customer_id": DEFAULT_INPUT["customer_id"],
        "customer_segment": DEFAULT_INPUT["customer_segment"],
        "skus": list(DEFAULT_INPUT["skus"]),
    }

    if isinstance(payload, dict):
        if isinstance(payload.get("customer_id"), str) and payload["customer_id"]:
            workflow_input["customer_id"] = payload["customer_id"]
        if isinstance(payload.get("customer_segment"), str) and payload["customer_segment"]:
            workflow_input["customer_segment"] = payload["customer_segment"]
        if isinstance(payload.get("skus"), list):
            skus = [sku for sku in payload["skus"] if isinstance(sku, str) and sku]
            if skus:
                workflow_input["skus"] = skus

    return workflow_input


@app.route(route="start-sub-orchestration", methods=["POST"])
@app.durable_client_input(client_name="client")
@with_context
async def start_sub_orchestration(
    req: func.HttpRequest,
    client: df.DurableOrchestrationClient,
) -> func.HttpResponse:
    workflow_input = _build_input(req)
    instance_id = await client.start_new("parent_workflow_orchestrator", None, workflow_input)

    logger.info(
        "Started parent workflow orchestration",
        extra={
            "instance_id": instance_id,
            "customer_id": workflow_input["customer_id"],
            "sku_count": len(workflow_input["skus"]),
        },
    )

    return client.create_check_status_response(req, instance_id)


@app.orchestration_trigger(context_name="context")
def parent_workflow_orchestrator(
    context: df.DurableOrchestrationContext,
) -> Generator[Any, Any, ParentWorkflowResult]:
    workflow_input = cast(WorkflowInput, context.get_input() or dict(DEFAULT_INPUT))
    customer_result = cast(
        CustomerSyncResult,
        (yield context.call_sub_orchestrator("customer_sync_sub_orchestrator", workflow_input)),
    )
    inventory_result = cast(
        InventorySyncResult,
        (yield context.call_sub_orchestrator("inventory_sync_sub_orchestrator", workflow_input)),
    )

    return {
        "instanceId": context.instance_id,
        "customer": customer_result,
        "inventory": inventory_result,
        "status": "completed",
    }


@app.orchestration_trigger(context_name="context")
def customer_sync_sub_orchestrator(
    context: df.DurableOrchestrationContext,
) -> Generator[Any, Any, CustomerSyncResult]:
    workflow_input = cast(WorkflowInput, context.get_input() or dict(DEFAULT_INPUT))
    result = yield context.call_activity("sync_customer_profile", workflow_input)
    return cast(CustomerSyncResult, result)


@app.orchestration_trigger(context_name="context")
def inventory_sync_sub_orchestrator(
    context: df.DurableOrchestrationContext,
) -> Generator[Any, Any, InventorySyncResult]:
    workflow_input = cast(WorkflowInput, context.get_input() or dict(DEFAULT_INPUT))
    result = yield context.call_activity("build_inventory_snapshot", workflow_input)
    return cast(InventorySyncResult, result)


@app.activity_trigger(input_name="workflow_input")
def sync_customer_profile(workflow_input: WorkflowInput) -> CustomerSyncResult:
    logger.info(
        "Synced customer profile",
        extra={
            "customer_id": workflow_input["customer_id"],
            "segment": workflow_input["customer_segment"],
        },
    )
    return {
        "step": "customer_sync",
        "customerId": workflow_input["customer_id"],
        "segment": workflow_input["customer_segment"],
        "status": "completed",
    }


@app.activity_trigger(input_name="workflow_input")
def build_inventory_snapshot(workflow_input: WorkflowInput) -> InventorySyncResult:
    logger.info(
        "Built inventory snapshot",
        extra={
            "customer_id": workflow_input["customer_id"],
            "sku_count": len(workflow_input["skus"]),
        },
    )
    return {
        "step": "inventory_sync",
        "skuCount": len(workflow_input["skus"]),
        "skus": list(workflow_input["skus"]),
        "status": "completed",
    }
