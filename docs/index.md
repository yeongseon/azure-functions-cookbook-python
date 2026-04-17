# Azure Functions Python Cookbook

Practical, production-oriented patterns for building Azure Functions with the
Python v2 programming model.

!!! info "What this project is"
    This repository is a cookbook and pattern catalog.
    It is not a runtime library you install as application dependency.

## Why this cookbook exists

Azure Functions documentation is broad, but many teams still need concrete,
copy-adapt-run patterns for common workloads. This cookbook focuses on that
gap by pairing clear pattern narratives with runnable examples.

## What you get

- **67 patterns** across 14 categories covering APIs, messaging, orchestration, AI, and more
- **67 runnable example projects** under `examples/`, organized by category
- **Bicep and Terraform IaC templates** for every recipe
- Production considerations in every pattern
- Mermaid architecture and behavior diagrams
- Integration with the Azure Functions Python DX Toolkit

## Pattern catalog

### APIs & Ingress

- [Hello HTTP Minimal](patterns/apis-and-ingress/hello-http-minimal.md) — minimal route handler
- [HTTP Routing, Query, and Body](patterns/apis-and-ingress/http-routing-query-body.md) — parse params and JSON body
- [HTTP Auth Levels](patterns/apis-and-ingress/http-auth-levels.md) — function vs anonymous vs admin keys
- [GitHub Webhook](patterns/apis-and-ingress/webhook-github.md) — secure signed event ingestion
- [EasyAuth Claims](patterns/apis-and-ingress/auth-easyauth-claims.md) — EasyAuth principal extraction
- [JWT Validation](patterns/apis-and-ingress/auth-jwt-validation.md) — JWT Bearer token validation
- [Multi-Tenant Auth](patterns/apis-and-ingress/auth-multitenant.md) — multi-tenant access control
- [BFF Facade API](patterns/apis-and-ingress/bff-facade-api.md) — backend-for-frontend aggregation
- [Full-Stack CRUD API](patterns/apis-and-ingress/full-stack-crud-api.md) — complete CRUD with toolkit

### Async APIs & Jobs

- [Async HTTP 202 Polling](patterns/async-apis-and-jobs/async-http-202-polling.md) — accepted with polling
- [Queue-Backed Job](patterns/async-apis-and-jobs/queue-backed-job.md) — deferred job processing
- [Callback Completion](patterns/async-apis-and-jobs/callback-completion.md) — async callback pattern

### Messaging & Pub/Sub

- [Queue Producer](patterns/messaging-and-pubsub/queue-producer.md) — enqueue messages via output binding
- [Queue Consumer](patterns/messaging-and-pubsub/queue-consumer.md) — process messages with retry semantics
- [Service Bus Worker](patterns/messaging-and-pubsub/servicebus-worker.md) — durable message processing
- [Event Grid Event Router](patterns/messaging-and-pubsub/eventgrid-event-router.md)
- [Service Bus Topic Fanout](patterns/messaging-and-pubsub/servicebus-topic-fanout.md)
- [Service Bus Sessions](patterns/messaging-and-pubsub/servicebus-sessions.md)
- [Service Bus DLQ Replay](patterns/messaging-and-pubsub/servicebus-dlq-replay.md)
- [Event Grid Domain Events](patterns/messaging-and-pubsub/eventgrid-domain-events.md)

### Streams & Telemetry

- [Event Hub Consumer](patterns/streams-and-telemetry/eventhub-consumer.md) — high-throughput stream processing
- [Event Hub Batch Window](patterns/streams-and-telemetry/eventhub-batch-window.md)
- [Event Hub Checkpoint Replay](patterns/streams-and-telemetry/eventhub-checkpoint-replay.md)

### Blob & File Triggers

- [Blob Upload Processor](patterns/blob-and-file-triggers/blob-upload-processor.md) — react to new blob arrivals
- [Blob Event Grid Trigger](patterns/blob-and-file-triggers/blob-eventgrid-trigger.md) — Event Grid-backed blob trigger

### Scheduled & Background

- [Timer Cron Job](patterns/scheduled-and-background/timer-cron-job.md) — scheduled maintenance and periodic automation

### Orchestration & Workflows

- [Hello Sequence](patterns/orchestration-and-workflows/durable-hello-sequence.md) — basic orchestration chain
- [Fan-Out / Fan-In](patterns/orchestration-and-workflows/durable-fan-out-fan-in.md) — parallel activity execution
- [Human Interaction](patterns/orchestration-and-workflows/durable-human-interaction.md) — approval and wait patterns
- [Entity Counter](patterns/orchestration-and-workflows/durable-entity-counter.md) — stateful entity pattern
- [Retry Pattern](patterns/orchestration-and-workflows/durable-retry-pattern.md) — activity-level retry strategies
- [Determinism Gotchas](patterns/orchestration-and-workflows/durable-determinism-gotchas.md) — pitfalls to avoid
- [Unit Testing](patterns/orchestration-and-workflows/durable-unit-testing.md) — test orchestrations without a host

### Reliability

- [Retry and Idempotency](patterns/reliability/retry-and-idempotency.md) — safe retries and deduplication

### Security & Tenancy

- [Managed Identity (Storage)](patterns/security-and-tenancy/managed-identity-storage.md) — keyless storage access
- [Managed Identity (Service Bus)](patterns/security-and-tenancy/managed-identity-servicebus.md) — keyless bus access

### Runtime & Ops

- [Blueprint Modular App](patterns/runtime-and-ops/blueprint-modular-app.md) — split handlers across modules
- [Output Binding vs SDK](patterns/runtime-and-ops/output-binding-vs-sdk.md) — when to use bindings vs direct calls
- [host.json Tuning](patterns/runtime-and-ops/host-json-tuning.md) — concurrency and retry knobs
- [Concurrency Tuning](patterns/runtime-and-ops/concurrency-tuning.md) — worker process and thread settings

### Data & Pipelines

- [Change Feed Processor](patterns/data-and-pipelines/change-feed-processor.md) — Cosmos DB downstream sync
- [DB Input and Output](patterns/data-and-pipelines/db-input-output.md) — database CRUD with azure-functions-db
- [File Processing Pipeline](patterns/data-and-pipelines/file-processing-pipeline.md)
- [CQRS Read Projection](patterns/data-and-pipelines/cqrs-read-projection.md)
- [SQLAlchemy REST Pagination](patterns/data-and-pipelines/sqlalchemy-rest-pagination.md)
- [ETL Enrichment](patterns/data-and-pipelines/etl-enrichment.md)

### Realtime

- [SignalR Notifications](patterns/realtime/signalr-notifications.md) — push notifications

### AI & Agents

- [MCP Server](patterns/ai-and-agents/mcp-server-example.md) — Model Context Protocol server example
- [LangGraph Agent](patterns/ai-and-agents/langgraph-agent.md) — LangGraph RAG agent
- [RAG Knowledge API](patterns/ai-and-agents/rag-knowledge-api.md) — RAG search endpoint
- [LangGraph RAG Agent](patterns/ai-and-agents/langgraph-rag-agent.md) — LangGraph agent deployment
- [Azure OpenAI Direct Chat](patterns/ai-and-agents/openai-direct-chat.md) — chat completion endpoint
- [Durable AI Pipeline](patterns/ai-and-agents/durable-ai-pipeline.md) — multi-step AI orchestration
- [Streaming AI Response](patterns/ai-and-agents/streaming-ai-response.md) — SSE streaming from Azure OpenAI
- [AI Image Generation](patterns/ai-and-agents/ai-image-generation.md) — DALL-E 3 image generation
- [Embedding Vector Search](patterns/ai-and-agents/embedding-vector-search.md) — embeddings + vector search

### Guides

- [Local Run and Direct Invoke](guides/local-run-and-direct-invoke.md) — test without deploying
- [Scaffold Quick Start](guides/scaffold-quick-start.md) — generate projects with afs
- [Testing Patterns](guides/testing-patterns.md) — unit, integration, and e2e testing

## Quick start

```bash
git clone https://github.com/yeongseon/azure-functions-python-cookbook.git
cd azure-functions-python-cookbook
python -m venv .venv
source .venv/bin/activate
```

Run one example:

```bash
cd examples/apis-and-ingress/hello_http_minimal
pip install -e .
func start
```

Then test:

```bash
curl http://localhost:7071/api/hello
```

## Recommended learning path

1. [Installation](installation.md)
2. [Getting Started](getting-started.md)
3. [Patterns Overview](patterns/index.md)
4. Pick one deep-dive pattern page
5. Run the matching `examples/<category>/<name>` project
6. Validate with [Testing](testing.md)

## Repository map

```text
docs/patterns/   Pattern deep-dives organized by category
docs/foundations/ Core concepts (execution model, triggers & bindings)
docs/reference/   Reference pages (durable functions, etc.)
docs/guides/      Practical guides (deployment, identity, IaC, scaffold)
examples/         Runnable Azure Functions app implementations
```

## Ecosystem projects

These companion projects are **optional accelerators** — the cookbook works independently without them:

- [`azure-functions-scaffold`](https://github.com/yeongseon/azure-functions-scaffold) — project bootstrap from known templates
- [`azure-functions-validation`](https://github.com/yeongseon/azure-functions-validation) — request/response validation helpers
- [`azure-functions-openapi`](https://github.com/yeongseon/azure-functions-openapi) — generated API contracts and Swagger UI
- [`azure-functions-logging`](https://github.com/yeongseon/azure-functions-logging) — structured telemetry and diagnostics
- [`azure-functions-doctor`](https://github.com/yeongseon/azure-functions-doctor) — local environment diagnosis
- [`azure-functions-db`](https://github.com/yeongseon/azure-functions-db) — database integration helpers
- [`azure-functions-knowledge`](https://github.com/yeongseon/azure-functions-knowledge) — RAG knowledge base
- [`azure-functions-langgraph`](https://github.com/yeongseon/azure-functions-langgraph) — LangGraph agent deployment

## Contributing and quality

If you want to improve patterns or examples:

- Use [Development](development.md) for workflow
- Use [Testing](testing.md) before submitting changes
- Follow [Contributing Guidelines](contributing.md)

## Additional references

- Core concepts: [Foundations](foundations/index.md)
- Planned expansion: [Roadmap](roadmap.md)
- Common failures and fixes: [Troubleshooting](troubleshooting.md)
- Frequently asked questions: [FAQ](faq.md)

!!! tip
    The fastest path to value is: pick one pattern, run its example, then adapt
    for your production constraints.
