# Durable Functions Overview

Durable Functions adds stateful workflow orchestration to Azure Functions.

In a normal stateless function, each invocation is isolated. In Durable Functions, the runtime persists execution history so long-running workflows can survive restarts, scale events, and delays.

## When to use Durable Functions

Use Durable Functions when you need one or more of the following:

- Multi-step workflows with explicit control flow.
- Checkpoints between steps for resiliency.
- Long-running waits (minutes, hours, days) without keeping a VM busy.
- Parallel fan-out work followed by aggregation.
- Human approval or external event callbacks.
- Stateful counters/aggregates represented as entities.

Do not use Durable Functions for tiny one-step handlers where normal triggers and queues are enough.

## Core pieces in Python

Python Durable apps usually include:

- A `df.Blueprint()` that contains orchestration/activity/entity definitions.
- A host app (`func.FunctionApp`) that registers the durable blueprint.
- A starter endpoint or trigger that starts orchestration instances.

High-level shape:

```python
import azure.functions as func
import azure.durable_functions as df

app = func.FunctionApp()
bp = df.Blueprint()

app.register_functions(bp)
```

## Durable function types

| Function type | Purpose | Typical decorator |
| --- | --- | --- |
| Orchestrator | Coordinates workflow logic and calls activities/entities | `@bp.orchestration_trigger(...)` |
| Activity | Executes stateless work unit | `@bp.activity_trigger(...)` |
| Entity | Maintains small consistent state with serialized operations | `@bp.entity_trigger(...)` |
| Starter/Client | Starts and queries orchestrations | `@bp.durable_client_input(...)` |

## Key patterns

### 1) Function chaining

Run activities in sequence where each step depends on previous output.

```python
@bp.orchestration_trigger(context_name="context")
def chain_orchestrator(context: df.DurableOrchestrationContext):
    a = yield context.call_activity("step_a", context.get_input())
    b = yield context.call_activity("step_b", a)
    c = yield context.call_activity("step_c", b)
    return c
```

Best for ETL-style staged transformations.

### 2) Fan-out/fan-in

Run many activities in parallel, then aggregate.

```python
@bp.orchestration_trigger(context_name="context")
def fanout_orchestrator(context: df.DurableOrchestrationContext):
    items = context.get_input() or []
    tasks = [context.call_activity("process_item", i) for i in items]
    results = yield context.task_all(tasks)
    return {"count": len(results), "results": results}
```

Best for independent units that can be parallelized.

### 3) Human interaction

Wait for external events with timeout fallback.

```python
from datetime import timedelta

@bp.orchestration_trigger(context_name="context")
def approval_orchestrator(context: df.DurableOrchestrationContext):
    deadline = context.current_utc_datetime + timedelta(hours=24)
    timeout = context.create_timer(deadline)
    approval = context.wait_for_external_event("approval")
    winner = yield context.task_any([approval, timeout])
    return "approved" if winner == approval else "timed_out"
```

Best for approval workflows and callback-driven business processes.

### 4) Monitoring loop

Poll until success/failure criteria are met.

```python
from datetime import timedelta

@bp.orchestration_trigger(context_name="context")
def monitor_orchestrator(context: df.DurableOrchestrationContext):
    while True:
        status = yield context.call_activity("check_status", context.get_input())
        if status in {"done", "failed"}:
            return status
        next_poll = context.current_utc_datetime + timedelta(minutes=5)
        yield context.create_timer(next_poll)
```

Best for external job tracking and synchronization.

### 5) Durable entities

Represent frequently updated small state as single-threaded entity operations.

```python
@bp.entity_trigger(context_name="context")
def counter_entity(context: df.DurableEntityContext):
    value = context.get_state(lambda: 0)
    op = context.operation_name
    if op == "add":
        context.set_state(value + int(context.get_input()))
    elif op == "reset":
        context.set_state(0)
    elif op == "get":
        context.set_result(value)
```

Best for counters, flags, quotas, and compact aggregates.

## Python-specific orchestration behavior

Python orchestrators are generator functions.

- Use `def`, not `async def`.
- Use `yield` for Durable tasks (`call_activity`, `task_all`, timers).
- The runtime replays orchestration history, so code can execute multiple times deterministically.

Starter endpoint example:

```python
import azure.functions as func
import azure.durable_functions as df

app = func.FunctionApp()
bp = df.Blueprint()

@app.route(route="orchestrators/{name}", methods=["POST"])
@bp.durable_client_input(client_name="client")
async def http_start(req: func.HttpRequest, client: df.DurableOrchestrationClient):
    name = req.route_params.get("name")
    payload = req.get_json()
    instance_id = await client.start_new(name, client_input=payload)
    return client.create_check_status_response(req, instance_id)

app.register_functions(bp)
```

## Determinism rules (critical)

Orchestrator logic must be deterministic during replay.

Avoid inside orchestrators:

- `datetime.utcnow()` / system time calls.
- `uuid.uuid4()` random IDs.
- Random number generation.
- Network I/O or database calls directly.
- Non-deterministic iteration over unstable collections.

Use Durable context APIs instead:

- `context.current_utc_datetime` for time.
- `context.new_guid()` for replay-safe IDs.
- Activity functions for all external I/O.

If determinism is broken, replay can fail with non-deterministic orchestration exceptions.

## Retries and error handling

Durable retries are explicit and per call site.

```python
retry = df.RetryOptions(first_retry_interval_in_milliseconds=5000, max_number_of_attempts=5)
result = yield context.call_activity_with_retry("charge_payment", retry, payload)
```

Guidelines:

- Retry transient failures (network, throttling, lock contention).
- Do not retry unrecoverable validation failures.
- Add idempotency keys in activity inputs.

## Extension bundle and package requirements

Durable requires the Durable extension to be available through extension bundle/runtime setup.

Typical prerequisites:

- `FUNCTIONS_EXTENSION_VERSION=~4`.
- Extension bundle configured in `host.json` (bundle version that includes Durable).
- Python dependencies include `azure-functions-durable`.

Check local startup logs if orchestrator/entity decorators are not discovered.

## Hosting and scaling considerations

- Consumption plan works well for many orchestrations, but cold starts can impact starter endpoints.
- Premium plan reduces cold start and supports pre-warmed instances.
- Dedicated plan is useful for predictable steady workload with custom sizing.

Operational guidance:

- Separate starter APIs from heavy activity compute where needed.
- Keep activity functions small and composable.
- Monitor orchestration state growth and retention strategy.

## Testing strategy

- Unit test activity functions like normal Python functions.
- Mock orchestration context for orchestrator logic tests.
- Add integration tests for full orchestration lifecycle.
- Validate timeout paths and external-event paths explicitly.

## Troubleshooting checklist

- Orchestrator not discovered -> verify blueprint registration and function names.
- Non-deterministic error -> move side effects into activities.
- Stuck pending -> verify starter called correct orchestrator name.
- Activity failures repeating -> inspect retry policy and poison-input handling.
- Scale lag -> inspect storage account health and host concurrency settings.

## Microsoft Learn references

- Durable Functions overview: https://learn.microsoft.com/azure/azure-functions/durable/durable-functions-overview
- Durable bindings and triggers: https://learn.microsoft.com/azure/azure-functions/durable/durable-functions-bindings
- Durable patterns: https://learn.microsoft.com/azure/azure-functions/durable/durable-functions-overview#application-patterns
- Durable orchestrations in Python: https://learn.microsoft.com/azure/azure-functions/durable/quickstart-python-vscode
- Orchestrator code constraints (determinism): https://learn.microsoft.com/azure/azure-functions/durable/durable-functions-code-constraints

## Related pages

- [Python v2 Programming Model](python-v2-programming-model.md)
- [Triggers and Bindings Overview](triggers-and-bindings-overview.md)
- [Identity-Based Connections](identity-based-connections.md)
- [Deployment Patterns](deployment-patterns.md)
