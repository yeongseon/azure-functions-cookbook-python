# Recipes

Practical recipes for building real-world Azure Functions with Python v2.
Each recipe is paired with a runnable project in `examples/`.

!!! tip
    Read the recipe, then run the matching example.
    Every example includes a `function_app.py` ready for `func start`.

---

## HTTP

| Recipe | Difficulty | Description |
| --- | --- | --- |
| [Hello HTTP Minimal](hello-http-minimal.md) | Beginner | Simplest GET endpoint with optional `name` parameter |
| [HTTP Routing, Query & Body](http-routing-query-body.md) | Intermediate | Full CRUD with route params, query strings, and JSON body parsing |
| [HTTP Auth Levels](http-auth-levels.md) | Beginner | ANONYMOUS, FUNCTION, and ADMIN auth level comparison |
| [Webhook (GitHub)](webhook-github.md) | Intermediate | HMAC-SHA256 signature verification and event dispatch |

## Timer

| Recipe | Difficulty | Description |
| --- | --- | --- |
| [Timer Cron Job](timer-cron-job.md) | Beginner | NCRONTAB scheduled execution with `past_due` detection |

## Queue

| Recipe | Difficulty | Description |
| --- | --- | --- |
| [Queue Producer](queue-producer.md) | Beginner | HTTP POST to queue output binding with payload validation |
| [Queue Consumer](queue-consumer.md) | Beginner | Queue trigger with JSON deserialization and dequeue-count logging |

## Blob

| Recipe | Difficulty | Description |
| --- | --- | --- |
| [Blob Upload Processor](blob-upload-processor.md) | Intermediate | Polling-based blob trigger with checksum calculation |
| [Blob Event Grid Trigger](blob-eventgrid-trigger.md) | Intermediate | Low-latency push-based blob trigger via Event Grid |

## Service Bus

| Recipe | Difficulty | Description |
| --- | --- | --- |
| [Service Bus Worker](servicebus-worker.md) | Intermediate | Queue trigger with correlation ID tracking and dead-letter guidance |

## Event Hub

| Recipe | Difficulty | Description |
| --- | --- | --- |
| [Event Hub Consumer](eventhub-consumer.md) | Intermediate | Partition-aware event processing with offset tracking |

## Cosmos DB

| Recipe | Difficulty | Description |
| --- | --- | --- |
| [Change Feed Processor](change-feed-processor.md) | Intermediate | Change feed trigger with lease container and batch processing |

## Patterns

| Recipe | Difficulty | Description |
| --- | --- | --- |
| [Blueprint Modular App](blueprint-modular-app.md) | Intermediate | Multi-file structure with `func.Blueprint()` for large projects |
| [Retry & Idempotency](retry-and-idempotency.md) | Intermediate | `@app.retry()` decorator with fixed-delay strategy and dedup |
| [Output Binding vs SDK](output-binding-vs-sdk.md) | Intermediate | Side-by-side comparison of binding vs `QueueClient` SDK |
| [Managed Identity (Storage)](managed-identity-storage.md) | Advanced | Identity-based Storage Queue connections with `__queueServiceUri` |
| [Managed Identity (Service Bus)](managed-identity-servicebus.md) | Advanced | Identity-based Service Bus with `__fullyQualifiedNamespace` |
| [host.json Tuning](host-json-tuning.md) | Advanced | Logging, timeout, and extension settings for performance |
| [Concurrency Tuning](concurrency-tuning.md) | Advanced | Dynamic concurrency vs static `batchSize` strategies |

## Durable Functions

| Recipe | Difficulty | Description |
| --- | --- | --- |
| [Hello Sequence](durable-hello-sequence.md) | Beginner | Orchestrator chaining three sequential activities |
| [Fan-Out / Fan-In](durable-fan-out-fan-in.md) | Intermediate | Parallel activity execution with `context.task_all()` |
| [Human Interaction](durable-human-interaction.md) | Intermediate | Approval workflow with external event and timeout |
| [Entity Counter](durable-entity-counter.md) | Intermediate | Durable entity with add/reset/get operations |
| [Retry Pattern](durable-retry-pattern.md) | Intermediate | `call_activity_with_retry` with `RetryOptions` |
| [Determinism Gotchas](durable-determinism-gotchas.md) | Advanced | Safe vs unsafe patterns in orchestrator replay |
| [Unit Testing](durable-unit-testing.md) | Advanced | Mock-based testing with generator stepping |

## AI

| Recipe | Difficulty | Description |
| --- | --- | --- |
| [MCP Server](mcp-server-example.md) | Advanced | Model Context Protocol JSON-RPC 2.0 server over HTTP |

## Local Development

| Recipe | Difficulty | Description |
| --- | --- | --- |
| [Local Run & Direct Invoke](local-run-and-direct-invoke.md) | Beginner | Two approaches: `func start` vs direct Python import |

---

## How to Choose

Pick by your primary trigger:

1. **Synchronous request/response** &rarr; HTTP recipes
2. **Scheduled execution** &rarr; Timer recipe
3. **Async message processing** &rarr; Queue or Service Bus recipes
4. **Event streaming** &rarr; Event Hub recipe
5. **File processing** &rarr; Blob recipes
6. **Change data capture** &rarr; Cosmos DB recipe
7. **Multi-step workflows** &rarr; Durable Functions recipes
8. **AI tool serving** &rarr; MCP Server recipe

Then refine with patterns:

- Need **modular code** &rarr; Blueprint Modular App
- Need **managed identity** &rarr; Identity recipes
- Need **performance tuning** &rarr; host.json or Concurrency recipes
- Need **reliability** &rarr; Retry & Idempotency

## Structure of Each Recipe

Every recipe follows a consistent format:

- **Overview** &mdash; What and why
- **When to Use** &mdash; Decision criteria
- **Architecture** &mdash; ASCII data-flow diagram
- **Prerequisites** &mdash; Tools and packages
- **Project Structure** &mdash; File layout
- **Implementation** &mdash; Code walkthrough with real snippets
- **Run Locally** &mdash; Step-by-step local execution
- **Expected Output** &mdash; What you should see
- **Production Considerations** &mdash; Scaling, retries, security
- **Related Recipes** &mdash; Cross-links

## Related

- [Concepts: Python v2 Programming Model](../concepts/python-v2-programming-model.md)
- [Concepts: Triggers & Bindings](../concepts/triggers-and-bindings-overview.md)
- [Concepts: Durable Functions](../concepts/durable-functions-overview.md)
- [Concepts: Identity-Based Connections](../concepts/identity-based-connections.md)
- [Concepts: Deployment Patterns](../concepts/deployment-patterns.md)
