# Cosmos DB Trigger, Input, and Output Bindings

Cosmos DB bindings cover both change-feed processing and point-read/query helpers. They are useful when your function app is tightly coupled to a container and you want binding-based access patterns instead of wiring the SDK in every handler.

## Trigger

Use `@app.cosmos_db_trigger(...)` to consume the change feed.

Key parameters: `database_name`, `container_name`, `connection`, `lease_container_name`, `create_lease_container_if_not_exists`, and `feed_poll_delay`.

```python
import azure.functions as func

app = func.FunctionApp()

@app.cosmos_db_trigger(
    arg_name="documents",
    database_name="appdb",
    container_name="orders",
    connection="CosmosDBConnection",
    lease_container_name="leases",
    create_lease_container_if_not_exists=True,
)
def cosmos_change_feed(documents: func.DocumentList) -> None:
    for doc in documents:
        print(doc.to_json())
```

## Input Binding

Use the input binding for point reads or parameterized queries.

```python
import azure.functions as func

app = func.FunctionApp()

@app.route(route="orders/{id}", methods=["GET"])
@app.cosmos_db_input(
    arg_name="document",
    database_name="appdb",
    container_name="orders",
    id="{id}",
    partition_key="{id}",
    connection="CosmosDBConnection",
)
def get_order(req: func.HttpRequest, document: str) -> func.HttpResponse:
    return func.HttpResponse(document, mimetype="application/json")
```

## Output Binding

The output binding is convenient for simple upserts from HTTP or message handlers.

```python
import json
import azure.functions as func

app = func.FunctionApp()

@app.route(route="orders", methods=["POST"])
@app.cosmos_db_output(
    arg_name="document",
    database_name="appdb",
    container_name="orders",
    connection="CosmosDBConnection",
)
def save_order(req: func.HttpRequest, document: func.Out[str]) -> func.HttpResponse:
    payload = req.get_json()
    document.set(json.dumps(payload))
    return func.HttpResponse(status_code=201)
```

## Configuration

Change-feed tuning usually lives in `host.json` only when you need custom extension behavior:

```json
{
  "version": "2.0"
}
```

`local.settings.json` typically includes `CosmosDBConnection`. Lease containers, databases, and throughput are configured in Cosmos DB itself rather than in the Functions host.

## Scaling Behavior

Cosmos DB triggers scale according to feed ranges and lease ownership. Parallelism is tied to partitioning of the monitored container, and each worker checkpoints progress through the lease container. Delivery is at-least-once, so handlers must tolerate replays after restarts, lease movement, or downstream failures.

## Common Pitfalls

- The trigger reads the change feed, not arbitrary queries; deletes and updates appear as change events, not full diff semantics.
- A poor partition-key strategy limits scale because feed ranges follow the container's physical partitions.
- Lease-container misconfiguration is a common cause of silent non-processing.

## Related Patterns

- [Change Feed Processor](../patterns/data-and-pipelines/change-feed-processor.md)
- [DB Input and Output Bindings](../patterns/data-and-pipelines/db-input-output.md)
- [Retry and Idempotency](../patterns/reliability/retry-and-idempotency.md)

## Related Links

- https://learn.microsoft.com/azure/azure-functions/functions-bindings-cosmosdb-v2-trigger?pivots=programming-language-python&tabs=python-v2
- https://learn.microsoft.com/azure/azure-functions/functions-bindings-cosmosdb-v2-input?pivots=programming-language-python&tabs=python-v2
