# Triggers and Bindings Overview

This page is a practical catalog of Azure Functions Python v2 triggers and bindings, including decorator names, common parameters, connection rules, and minimal code examples.

## Trigger catalog (Python v2)

The table below covers the trigger types commonly available in Azure Functions runtime v4 with Python v2.

| Trigger type | v2 decorator | Common parameters | Typical payload |
| --- | --- | --- | --- |
| HTTP Trigger | `@app.route(...)` | `route`, `methods`, `auth_level` | `func.HttpRequest` |
| Timer Trigger | `@app.timer_trigger(...)` | `schedule`, `arg_name`, `run_on_startup`, `use_monitor` | `func.TimerRequest` |
| Queue Storage Trigger | `@app.queue_trigger(...)` | `arg_name`, `queue_name`, `connection` | `func.QueueMessage` or `str` |
| Blob Trigger | `@app.blob_trigger(...)` | `arg_name`, `path`, `connection`, `source` | bytes/stream/blob content |
| Event Hub Trigger | `@app.event_hub_message_trigger(...)` | `arg_name`, `event_hub_name`, `connection`, `consumer_group` | Event Hub event batch |
| Service Bus Queue Trigger | `@app.service_bus_queue_trigger(...)` | `arg_name`, `queue_name`, `connection`, `is_sessions_enabled` | Service Bus message |
| Service Bus Topic Trigger | `@app.service_bus_topic_trigger(...)` | `arg_name`, `topic_name`, `subscription_name`, `connection` | Service Bus message |
| Cosmos DB Trigger | `@app.cosmos_db_trigger(...)` | `arg_name`, `database_name`, `container_name`, `connection`, `lease_container_name` | changed docs list |
| Event Grid Trigger | `@app.event_grid_trigger(...)` | `arg_name` | `func.EventGridEvent` |
| Warmup Trigger | `@app.warm_up_trigger(...)` | `arg_name` | warmup context |
| Durable Orchestrator Trigger | `@bp.orchestration_trigger(...)` | `context_name` | orchestration context |
| Durable Activity Trigger | `@bp.activity_trigger(...)` | `input_name` | activity input object |
| Durable Entity Trigger | `@bp.entity_trigger(...)` | `context_name` | durable entity context |

## Binding catalog (Input and Output)

Bindings connect your function to Azure services without requiring full SDK plumbing in every handler.

| Binding kind | Direction | v2 decorator | Core parameters | Notes |
| --- | --- | --- | --- | --- |
| HTTP response | Output | return value / `func.HttpResponse` | N/A | Implicit for HTTP-triggered functions |
| Queue Storage | Input | `@app.queue_input(...)` | `arg_name`, `queue_name`, `connection` | Read auxiliary messages |
| Queue Storage | Output | `@app.queue_output(...)` | `arg_name`, `queue_name`, `connection` | Emit async work items |
| Blob Storage | Input | `@app.blob_input(...)` | `arg_name`, `path`, `connection` | Read file/blob content |
| Blob Storage | Output | `@app.blob_output(...)` | `arg_name`, `path`, `connection` | Write transformed files |
| Event Hub | Output | `@app.event_hub_output(...)` | `arg_name`, `event_hub_name`, `connection` | Publish stream events |
| Service Bus | Output | `@app.service_bus_queue_output(...)` | `arg_name`, `queue_name`, `connection` | Send queue messages |
| Service Bus | Output | `@app.service_bus_topic_output(...)` | `arg_name`, `topic_name`, `connection` | Publish topic events |
| Cosmos DB | Input | `@app.cosmos_db_input(...)` | `arg_name`, `database_name`, `container_name`, `connection` | Read docs by query or id |
| Cosmos DB | Output | `@app.cosmos_db_output(...)` | `arg_name`, `database_name`, `container_name`, `connection` | Persist documents |
| Event Grid | Output | `@app.event_grid_output(...)` | `arg_name`, `topic_endpoint_uri`, `topic_key_setting` | Publish Event Grid events |
| Durable client | Input | `@bp.durable_client_input(...)` | `client_name` | Start/query orchestrations |

## Connection settings model

### Basic app-setting connection

Most decorators reference `connection="NAME"`.

- For classic connection strings, `NAME` maps directly to an app setting.
- Example: `connection="AzureWebJobsStorage"` reads `AzureWebJobsStorage=<connection-string>`.

### Identity-based connection

For managed identity, `NAME` is a prefix with service-specific suffix settings.

- Queue/Blob/Table Storage use URI suffix settings such as `NAME__queueServiceUri`.
- Service Bus uses `NAME__fullyQualifiedNamespace`.
- Event Hubs uses `NAME__fullyQualifiedNamespace`.
- Cosmos DB commonly uses `NAME__accountEndpoint`.

Details and role mappings are documented in [Identity-Based Connections](../guides/identity-based-connections.md).

## Trigger examples

Each sample is intentionally short and focuses on decorator shape.

### 1) HTTP Trigger

```python
import azure.functions as func

app = func.FunctionApp()

@app.function_name(name="http_ping")
@app.route(route="ping", methods=["GET"])
def http_ping(req: func.HttpRequest) -> func.HttpResponse:
    return func.HttpResponse("pong")
```

### 2) Timer Trigger

```python
import logging
import azure.functions as func

app = func.FunctionApp()

@app.function_name(name="hourly_job")
@app.timer_trigger(schedule="0 0 * * * *", arg_name="timer")
def hourly_job(timer: func.TimerRequest) -> None:
    logging.info("hourly timer fired")
```

### 3) Queue Storage Trigger

```python
import logging
import azure.functions as func

app = func.FunctionApp()

@app.function_name(name="queue_consumer")
@app.queue_trigger(arg_name="msg", queue_name="orders", connection="StorageConn")
def queue_consumer(msg: func.QueueMessage) -> None:
    logging.info("message=%s", msg.get_body().decode("utf-8"))
```

### 4) Blob Trigger

```python
import logging
import azure.functions as func

app = func.FunctionApp()

@app.function_name(name="blob_ingest")
@app.blob_trigger(arg_name="blob", path="incoming/{name}", connection="StorageConn")
def blob_ingest(blob: bytes) -> None:
    logging.info("blob length=%d", len(blob))
```

### 5) Event Hub Trigger

```python
import logging
import azure.functions as func

app = func.FunctionApp()

@app.function_name(name="hub_consumer")
@app.event_hub_message_trigger(
    arg_name="events",
    event_hub_name="telemetry",
    connection="EventHubConn",
)
def hub_consumer(events) -> None:
    logging.info("event batch size=%d", len(events))
```

### 6) Service Bus Queue Trigger

```python
import logging
import azure.functions as func

app = func.FunctionApp()

@app.function_name(name="sb_queue_worker")
@app.service_bus_queue_trigger(
    arg_name="msg",
    queue_name="jobs",
    connection="ServiceBusConn",
)
def sb_queue_worker(msg) -> None:
    logging.info("processed service bus queue message")
```

### 7) Service Bus Topic Trigger

```python
import logging
import azure.functions as func

app = func.FunctionApp()

@app.function_name(name="sb_topic_worker")
@app.service_bus_topic_trigger(
    arg_name="msg",
    topic_name="events",
    subscription_name="functions-sub",
    connection="ServiceBusConn",
)
def sb_topic_worker(msg) -> None:
    logging.info("processed service bus topic message")
```

### 8) Cosmos DB Trigger

```python
import logging
import azure.functions as func

app = func.FunctionApp()

@app.function_name(name="cosmos_changes")
@app.cosmos_db_trigger(
    arg_name="documents",
    database_name="appdb",
    container_name="orders",
    lease_container_name="leases",
    connection="CosmosConn",
)
def cosmos_changes(documents: list) -> None:
    logging.info("changed docs=%d", len(documents))
```

### 9) Event Grid Trigger

```python
import logging
import azure.functions as func

app = func.FunctionApp()

@app.function_name(name="grid_listener")
@app.event_grid_trigger(arg_name="event")
def grid_listener(event: func.EventGridEvent) -> None:
    logging.info("event type=%s", event.event_type)
```

### 10) Warmup Trigger

```python
import logging
import azure.functions as func

app = func.FunctionApp()

@app.function_name(name="warmup")
@app.warm_up_trigger(arg_name="context")
def warmup(context) -> None:
    logging.info("instance warmup invoked")
```

### 11) Durable Orchestrator Trigger

```python
import azure.durable_functions as df

bp = df.Blueprint()

@bp.orchestration_trigger(context_name="context")
def order_orchestrator(context: df.DurableOrchestrationContext):
    result = yield context.call_activity("validate_order", context.get_input())
    return result
```

### 12) Durable Activity Trigger

```python
import azure.durable_functions as df

bp = df.Blueprint()

@bp.activity_trigger(input_name="order")
def validate_order(order: dict) -> dict:
    return {"valid": True, "id": order.get("id")}
```

### 13) Durable Entity Trigger

```python
import azure.durable_functions as df

bp = df.Blueprint()

@bp.entity_trigger(context_name="context")
def counter_entity(context: df.DurableEntityContext):
    current = context.get_state(lambda: 0)
    if context.operation_name == "add":
        context.set_state(current + context.get_input())
    elif context.operation_name == "get":
        context.set_result(current)
```

## Rules of thumb for choosing triggers

- Use HTTP for request/response APIs and webhooks.
- Use Queue or Service Bus for buffered async work.
- Use Event Hub for high-throughput append-only event streams.
- Use Blob trigger for object lifecycle processing.
- Use Cosmos DB trigger for change feed processors.
- Use Timer for scheduled maintenance and compaction jobs.
- Use Durable triggers for multi-step stateful workflows.

## Common pitfalls

- Missing `connection` setting names.
- Using trigger-specific SDK types without correct package versions.
- Assuming at-least-once triggers are exactly once.
- Performing long CPU work in HTTP handlers instead of offloading.
- Forgetting to configure dead-letter/retry/idempotency strategy.

## Microsoft Learn links by trigger

- Triggers and bindings overview: https://learn.microsoft.com/azure/azure-functions/functions-triggers-bindings
- HTTP trigger: https://learn.microsoft.com/azure/azure-functions/functions-bindings-http-webhook-trigger
- Timer trigger: https://learn.microsoft.com/azure/azure-functions/functions-bindings-timer
- Queue Storage trigger/binding: https://learn.microsoft.com/azure/azure-functions/functions-bindings-storage-queue
- Blob trigger/binding: https://learn.microsoft.com/azure/azure-functions/functions-bindings-storage-blob
- Event Hub trigger/binding: https://learn.microsoft.com/azure/azure-functions/functions-bindings-event-hubs
- Service Bus trigger/binding: https://learn.microsoft.com/azure/azure-functions/functions-bindings-service-bus
- Cosmos DB trigger/binding: https://learn.microsoft.com/azure/azure-functions/functions-bindings-cosmosdb-v2
- Event Grid trigger/binding: https://learn.microsoft.com/azure/azure-functions/functions-bindings-event-grid
- Warmup trigger: https://learn.microsoft.com/azure/azure-functions/functions-bindings-warmup
- Durable Functions bindings: https://learn.microsoft.com/azure/azure-functions/durable/durable-functions-bindings
