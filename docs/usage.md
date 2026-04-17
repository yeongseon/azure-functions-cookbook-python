# Usage

This page explains how to use the cookbook effectively as a recipe catalog.

## Core model

Use the repository in this order:

1. Pick a pattern in `recipes/`.
2. Run the matching implementation in `examples/`.
3. Adapt the sample for your own function app.
4. Validate with tests, lint, and security checks.

!!! info
    There is no package API to import from this repository for app runtime.
    The value is in the recipe content and runnable examples.

## How recipes are organized

Current recipes:

**HTTP** (7 recipes): hello-http-minimal, http-routing-query-body, http-auth-levels, webhook-github, auth-easyauth-claims, auth-jwt-validation, auth-multitenant
**Timer** (1): timer-cron-job
**Queue** (2): queue-producer, queue-consumer
**Blob** (2): blob-upload-processor, blob-eventgrid-trigger
**Service Bus** (1): servicebus-worker
**Event Hub** (1): eventhub-consumer
**Cosmos DB** (1): change-feed-processor
**Patterns** (7): blueprint-modular-app, retry-and-idempotency, output-binding-vs-sdk, managed-identity-storage, managed-identity-servicebus, host-json-tuning, concurrency-tuning
**Durable Functions** (7): durable-hello-sequence, durable-fan-out-fan-in, durable-human-interaction, durable-entity-counter, durable-retry-pattern, durable-determinism-gotchas, durable-unit-testing
**AI** (1): mcp-server-example
**Local Development** (1): local-run-and-direct-invoke

Each recipe targets a specific trigger style and operational concern.

| Recipe | Trigger | Focus |
| --- | --- | --- |
| Hello HTTP Minimal | HTTP | Simplest GET endpoint |
| HTTP Routing, Query & Body | HTTP | Route params, query strings, JSON body |
| Queue Consumer | Queue | Message processing with retry semantics |
| Timer Cron Job | Timer | NCRONTAB scheduled execution |
| Blob Upload Processor | Blob | Polling-based blob trigger |
| Service Bus Worker | Service Bus | Correlation ID tracking and dead-letter |
| Durable Hello Sequence | Durable | Activity chaining pattern |

## Recipe format contract

New or updated recipe files should follow `recipes/_template.md`:

- Overview
- When to Use
- Architecture
- Project Structure
- Run Locally
- Production Considerations
- Scaffold Starter

This consistent section contract keeps pages easy to scan and compare.

## Mapping between recipes and examples

Each recipe has a runnable app under `examples/`:

- `recipes/hello-http-minimal.md` -> `examples/http/hello_http_minimal`
- `recipes/http-routing-query-body.md` -> `examples/http/http_routing_query_body`
- `recipes/webhook-github.md` -> `examples/http/webhook_github`
- `recipes/queue-consumer.md` -> `examples/queue/queue_consumer`
- `recipes/timer-cron-job.md` -> `examples/timer/timer_cron_job`
- ... and many more. See [Patterns Overview](patterns/index.md) for the full list.

!!! tip
    Keep docs and example code aligned in the same pull request.
    If behavior changes in code, update recipe narrative and run instructions.

## Typical usage patterns

### Pattern discovery

- Start with [Patterns Overview](patterns/index.md)
- Select by trigger and operational needs
- Open the deep-dive pattern page

### Prototype quickly

- Copy structure from an existing example
- Keep trigger decorator style (`func.FunctionApp` v2 model)
- Replace placeholder business logic first

### Production hardening

- Add input validation and explicit status codes
- Add idempotency for webhook and queue workflows
- Add observability and clear error paths
- Add security controls from [Security](security.md)

## Contributing new recipes

Recommended flow:

1. Duplicate `recipes/_template.md` into a new recipe page.
2. Add a matching runnable project under `examples/`.
3. Document local run steps and expected output.
4. Include production constraints and failure behavior.
5. Add docs navigation entry in `mkdocs.yml`.

See [Contributing Guidelines](contributing.md) for review standards.

## Ecosystem integration

The cookbook is designed to work with companion projects:

- `azure-functions-scaffold` for generating starter projects
- `azure-functions-validation` for request/response validation helpers
- `azure-functions-openapi` for contract generation and Swagger UI
- `azure-functions-logging` for structured logs
- `azure-functions-doctor` for local environment checks

Use recipes as the architecture baseline, then apply ecosystem tooling
incrementally as your app matures.

## Anti-patterns to avoid

- Treating examples as production-ready without review
- Copying snippets without local test execution
- Keeping secrets in source code
- Ignoring retry/idempotency behavior for queue and webhook patterns
- Updating examples without updating documentation

## Useful links

- Start here: [Getting Started](getting-started.md)
- Build and test: [Development](development.md), [Testing](testing.md)
- Diagnose problems: [Troubleshooting](troubleshooting.md)
- Read all patterns: [Patterns Overview](patterns/index.md)
