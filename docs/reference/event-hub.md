# Event Hub Trigger and Output Binding

Event Hubs is the streaming trigger for high-throughput append-only events. It is optimized for partitioned ingestion and consumer groups, making it the right fit for telemetry, clickstreams, and device/event pipelines rather than queue-style command processing.

## Trigger

Use `@app.event_hub_message_trigger(...)` to consume events from a hub.

Key parameters: `event_hub_name`, `connection`, `consumer_group`, `cardinality`, and `arg_name`.

```python
import azure.functions as func

app = func.FunctionApp()

@app.event_hub_message_trigger(
    arg_name="events",
    event_hub_name="telemetry",
    connection="EventHubConnection",
    consumer_group="$Default",
    cardinality="many",
)
def event_hub_example(events: list[func.EventHubEvent]) -> None:
    for event in events:
        print(event.get_body().decode("utf-8"))
```

## Input Binding

Stream processors often enrich batches with point lookups before writing curated outputs.

```python
import azure.functions as func

app = func.FunctionApp()

@app.event_hub_message_trigger(arg_name="events", event_hub_name="telemetry", connection="EventHubConnection")
@app.blob_input(arg_name="schema", path="schemas/telemetry.json", connection="AzureWebJobsStorage")
def enrich_stream(events: list[func.EventHubEvent], schema: bytes) -> None:
    print(f"schema_bytes={len(schema)} event_count={len(events)}")
```

## Output Binding

Use the output binding to emit derived events to another hub.

```python
import json
import azure.functions as func

app = func.FunctionApp()

@app.event_hub_message_trigger(arg_name="events", event_hub_name="telemetry", connection="EventHubConnection")
@app.event_hub_output(arg_name="out_events", event_hub_name="telemetry-curated", connection="EventHubConnection")
def republish_stream(events: list[func.EventHubEvent], out_events: func.Out[list[str]]) -> None:
    payloads = [json.dumps({"body": e.get_body().decode("utf-8")}) for e in events]
    out_events.set(payloads)
```

## Configuration

Event Hub scaling and checkpoint behavior is host-controlled:

```json
{
  "version": "2.0",
  "extensions": {
    "eventHubs": {
      "batchCheckpointFrequency": 1,
      "eventProcessorOptions": {
        "maxBatchSize": 100,
        "prefetchCount": 300,
        "loadBalancingUpdateInterval": "00:00:10"
      }
    }
  }
}
```

`local.settings.json` normally includes `EventHubConnection` plus `AzureWebJobsStorage` for leases/checkpoints when required by the extension version and hosting setup.

## Scaling Behavior

Event Hub triggers scale by partition ownership. A partition is processed by only one active consumer in a consumer group at a time, so total parallelism is bounded by partition count. Ordering is preserved within a partition, and checkpoints determine how far the processor will replay after restarts or failures.

## Common Pitfalls

- Consumer-group changes create a new checkpoint lineage, which can look like duplicate processing.
- `cardinality="many"` improves throughput but requires batch-safe code and memory budgeting.
- Ordering across partitions does not exist; aggregate downstream by partition key if you need localized order.

## Related Patterns

- [Event Hub Consumer](../patterns/streams-and-telemetry/eventhub-consumer.md)
- [Concurrency Tuning](../patterns/runtime-and-ops/concurrency-tuning.md)
- [Output Binding vs SDK](../patterns/runtime-and-ops/output-binding-vs-sdk.md)

## Related Links

- https://learn.microsoft.com/azure/azure-functions/functions-bindings-event-hubs-trigger?pivots=programming-language-python&tabs=python-v2
- https://learn.microsoft.com/azure/azure-functions/functions-bindings-event-hubs-output?pivots=programming-language-python&tabs=python-v2
