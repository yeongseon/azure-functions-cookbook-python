# Sub-Orchestration

> **Trigger**: Durable Orchestration | **State**: durable | **Guarantee**: at-least-once | **Difficulty**: intermediate

## Overview
This recipe shows how a parent Durable Functions orchestrator can delegate parts of a workflow
to child sub-orchestrators with `context.call_sub_orchestrator(...)`.
The parent stays focused on high-level coordination while each child owns its own durable
history, retries, and activity scheduling.

This is useful when one orchestration would otherwise become too large or when a repeated
workflow segment deserves its own reusable orchestration boundary.
Sub-orchestrations still follow the same replay-safe rules as any other orchestrator: they only
coordinate durable work and do not perform direct I/O themselves.

## When to Use
- You want to decompose a large orchestration into smaller reusable workflow units.
- Different stages of the workflow need their own durable history and status boundaries.
- The parent workflow needs to invoke nested orchestration logic in a deterministic way.

## When NOT to Use
- A direct activity call is enough and you do not need another orchestration boundary.
- The workflow is so small that extra orchestration layers only add complexity.
- The child logic performs only synchronous computation with no durable coordination value.

## Architecture
```mermaid
flowchart LR
    parent[parent_workflow_orchestrator]
    child1[customer_sync_sub_orchestrator]
    child2[inventory_sync_sub_orchestrator]
    activity1[sync_customer_profile activity]
    activity2[build_inventory_snapshot activity]
    result[aggregated parent result]

    parent -->|call_sub_orchestrator| child1
    parent -->|call_sub_orchestrator| child2
    child1 -->|call_activity| activity1
    child2 -->|call_activity| activity2
    child1 --> parent
    child2 --> parent
    parent --> result
```

## Behavior
```mermaid
sequenceDiagram
    participant Starter as HTTP starter
    participant Parent as Parent orchestrator
    participant Customer as Customer sub-orchestrator
    participant Inventory as Inventory sub-orchestrator
    participant Activity as Activity functions

    Starter->>Parent: start_new("parent_workflow_orchestrator")
    Parent->>Customer: call_sub_orchestrator("customer_sync_sub_orchestrator")
    Customer->>Activity: call_activity("sync_customer_profile")
    Activity-->>Customer: customer sync result
    Customer-->>Parent: child result
    Parent->>Inventory: call_sub_orchestrator("inventory_sync_sub_orchestrator")
    Inventory->>Activity: call_activity("build_inventory_snapshot")
    Activity-->>Inventory: inventory snapshot result
    Inventory-->>Parent: child result
    Parent-->>Starter: final aggregated output via status endpoint
```

## Prerequisites
- Python 3.10+
- Azure Functions Core Tools v4
- Durable storage configured in local settings
- `azure-functions`, `azure-functions-durable`, and `azure-functions-logging` installed

## Project Structure
```text
examples/orchestration-and-workflows/sub_orchestration/
|- function_app.py
|- host.json
|- local.settings.json.example
|- requirements.txt
`- README.md
```

## Implementation
The starter launches the parent orchestration and returns the standard Durable status URLs.

```python
@app.route(route="start-sub-orchestration", methods=["POST"], auth_level=func.AuthLevel.ANONYMOUS)
@app.durable_client_input(client_name="client")
async def start_sub_orchestration(req: func.HttpRequest, client: df.DurableOrchestrationClient):
    instance_id = await client.start_new("parent_workflow_orchestrator", None, payload)
    return client.create_check_status_response(req, instance_id)
```

The parent orchestrator calls two child orchestrators in sequence and aggregates their outputs.

```python
@app.orchestration_trigger(context_name="context")
def parent_workflow_orchestrator(context: df.DurableOrchestrationContext):
    payload = context.get_input() or DEFAULT_INPUT
    customer_result = yield context.call_sub_orchestrator("customer_sync_sub_orchestrator", payload)
    inventory_result = yield context.call_sub_orchestrator("inventory_sync_sub_orchestrator", payload)
    return {
        "customer": customer_result,
        "inventory": inventory_result,
    }
```

Each child orchestrator remains small and only schedules its own activity.
That keeps orchestration boundaries explicit while still allowing the parent to compose them.

```python
@app.orchestration_trigger(context_name="context")
def customer_sync_sub_orchestrator(context: df.DurableOrchestrationContext):
    payload = context.get_input() or DEFAULT_INPUT
    return (yield context.call_activity("sync_customer_profile", payload))
```

Logging belongs in the starter and activities, not inside orchestrator replay paths.
This example uses `azure-functions-logging` for structured application logs while the durable
runtime manages orchestration history separately.

## Run Locally
```bash
cd examples/orchestration-and-workflows/sub_orchestration
pip install -r requirements.txt
func start
```

## Expected Output
```text
POST /api/start-sub-orchestration -> 202 Accepted

Final orchestration output:
{
  "instanceId": "<parent-instance-id>",
  "customer": {
    "step": "customer_sync",
    "customerId": "cust-1001",
    "segment": "enterprise",
    "status": "completed"
  },
  "inventory": {
    "step": "inventory_sync",
    "skuCount": 2,
    "status": "completed"
  }
}
```

## Production Considerations
- Composition: use sub-orchestrations to isolate reusable workflow segments and failure domains.
- Retries: apply retry policies at the child orchestration or activity level for transient faults.
- Idempotency: keep activities idempotent because child workflows can replay or retry independently.
- Observability: log parent and child correlation identifiers in starter and activity code.
- Versioning: evolve child orchestrators carefully because in-flight durable instances persist history.

## Related Links
- [Durable Hello Sequence](./durable-hello-sequence.md)
- [Durable Fan-Out Fan-In](./durable-fan-out-fan-in.md)
- [Sub-orchestrations](https://learn.microsoft.com/en-us/azure/azure-functions/durable/durable-functions-sub-orchestrations)
- [Durable Functions overview](https://learn.microsoft.com/en-us/azure/azure-functions/durable/durable-functions-overview)
