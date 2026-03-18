# Azure Functions Python Cookbook

Practical, production-oriented recipes for building Azure Functions with the
Python v2 programming model.

!!! info "What this project is"
    This repository is a cookbook and pattern catalog.
    It is not a runtime library you install as application dependency.

## Why this cookbook exists

Azure Functions documentation is broad, but many teams still need concrete,
copy-adapt-run patterns for common workloads. This cookbook focuses on that
gap by pairing clear recipe narratives with runnable examples.

## What you get

- Trigger-focused recipes for real workloads (HTTP, webhook, queue, timer)
- Runnable sample apps under `examples/`
- Production considerations in every recipe
- Consistent structure for learning, implementation, and contribution

## Recipe cards

### HTTP

- [Hello HTTP Minimal](recipes/hello-http-minimal.md) — minimal route handler
- [HTTP Routing, Query, and Body](recipes/http-routing-query-body.md) — parse params and JSON body
- [HTTP Auth Levels](recipes/http-auth-levels.md) — function vs anonymous vs admin keys
- [GitHub Webhook](recipes/webhook-github.md) — secure signed event ingestion

### Queue & Service Bus

- [Queue Producer](recipes/queue-producer.md) — enqueue messages via output binding
- [Queue Consumer](recipes/queue-consumer.md) — process messages with retry semantics
- [Service Bus Worker](recipes/servicebus-worker.md) — durable message processing

### Blob & Event Hub & Cosmos DB

- [Blob Upload Processor](recipes/blob-upload-processor.md) — react to new blob arrivals
- [Blob Event Grid Trigger](recipes/blob-eventgrid-trigger.md) — Event Grid-backed blob trigger
- [Event Hub Consumer](recipes/eventhub-consumer.md) — high-throughput stream processing
- [Change Feed Processor](recipes/change-feed-processor.md) — Cosmos DB downstream sync

### Timer

- [Timer Cron Job](recipes/timer-cron-job.md) — scheduled maintenance and periodic automation

### Patterns

- [Blueprint Modular App](recipes/blueprint-modular-app.md) — split handlers across modules
- [Retry and Idempotency](recipes/retry-and-idempotency.md) — safe retries and deduplication
- [Output Binding vs SDK](recipes/output-binding-vs-sdk.md) — when to use bindings vs direct calls
- [Managed Identity (Storage)](recipes/managed-identity-storage.md) — keyless storage access
- [Managed Identity (Service Bus)](recipes/managed-identity-servicebus.md) — keyless bus access
- [host.json Tuning](recipes/host-json-tuning.md) — concurrency and retry knobs
- [Concurrency Tuning](recipes/concurrency-tuning.md) — worker process and thread settings

### Durable Functions

- [Hello Sequence](recipes/durable-hello-sequence.md) — basic orchestration chain
- [Fan-Out / Fan-In](recipes/durable-fan-out-fan-in.md) — parallel activity execution
- [Human Interaction](recipes/durable-human-interaction.md) — approval and wait patterns
- [Entity Counter](recipes/durable-entity-counter.md) — stateful entity pattern
- [Retry Pattern](recipes/durable-retry-pattern.md) — activity-level retry strategies
- [Determinism Gotchas](recipes/durable-determinism-gotchas.md) — pitfalls to avoid
- [Unit Testing](recipes/durable-unit-testing.md) — test orchestrations without a host

### AI & Local Dev

- [MCP Server](recipes/mcp-server-example.md) — Model Context Protocol server example
- [Local Run and Direct Invoke](recipes/local-run-and-direct-invoke.md) — test without deploying
## Quick start

```bash
git clone https://github.com/yeongseon/azure-functions-python-cookbook.git
cd azure-functions-python-cookbook
python -m venv .venv
source .venv/bin/activate
```

Run one example:

```bash
cd examples/http/hello_http_minimal
pip install -e .
func start
```

Then test:

```bash
curl http://localhost:7071/api/items
```

## Recommended learning path

1. [Installation](installation.md)
2. [Getting Started](getting-started.md)
3. [Recipes Overview](recipes/index.md)
4. Pick one deep-dive recipe page
5. Run the matching `examples/<name>` project
6. Validate with [Testing](testing.md)

## Repository map

```text
docs/       Documentation site pages and recipe deep-dives
recipes/    Source recipe narratives and template contract
examples/   Runnable Azure Functions app implementations
```

## Ecosystem projects

These companion projects integrate well with cookbook patterns:

- `azure-functions-scaffold` -> project bootstrap from known templates
- `azure-functions-validation` -> request/response validation helpers
- `azure-functions-openapi` -> generated API contracts and Swagger UI
- `azure-functions-logging` -> structured telemetry and diagnostics
- `azure-functions-doctor` -> local environment diagnosis

## Contributing and quality

If you want to improve recipes or examples:

- Use [Development](development.md) for workflow
- Use [Testing](testing.md) before submitting changes
- Follow [Contributing Guidelines](contributing.md)

## Additional references

- Pattern model and boundaries: [Architecture](architecture.md)
- Planned expansion: [Roadmap](roadmap.md)
- Common failures and fixes: [Troubleshooting](troubleshooting.md)
- Frequently asked questions: [FAQ](faq.md)

!!! tip
    The fastest path to value is: pick one recipe, run its example, then adapt
    for your production constraints.
