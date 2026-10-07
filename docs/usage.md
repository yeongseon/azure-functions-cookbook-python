# Usage

This page explains how to use the cookbook effectively as a recipe catalog.

## Core model

Use the repository in this order:

1. Pick a pattern in `docs/patterns/`.
2. Run the matching implementation in `examples/`.
3. Adapt the sample for your own function app.
4. Validate with tests, lint, and security checks.

!!! info
    There is no package API to import from this repository for app runtime.
    The value is in the recipe content and runnable examples.

## How recipes are organized

Pattern pages live in `docs/patterns/<category>/`, one page per recipe, grouped into these
categories:

- **APIs & Ingress**
- **Scheduled & Background**
- **Blob & File Triggers**
- **Async APIs & Jobs**
- **Messaging & Pub/Sub**
- **Streams & Telemetry**
- **Data & Pipelines**
- **Orchestration & Workflows**
- **Reliability**
- **Security & Tenancy**
- **Runtime & Ops**
- **Realtime**
- **AI & Agents**
- **Guides**

Each recipe targets a specific trigger style and operational concern. For the current per-category
counts and the full recipe list, see the [Patterns Overview](patterns/index.md); it is generated from
the example inventory, so it never drifts from what is actually in the repository.

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

New or updated pattern pages under `docs/patterns/` should follow the same section contract used by existing pattern pages:

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

- `docs/patterns/apis-and-ingress/hello-http-minimal.md` -> `examples/apis-and-ingress/hello_http_minimal`
- `docs/patterns/apis-and-ingress/http-routing-query-body.md` -> `examples/apis-and-ingress/http_routing_query_body`
- `docs/patterns/apis-and-ingress/webhook-github.md` -> `examples/apis-and-ingress/webhook_github`
- `docs/patterns/messaging-and-pubsub/queue-consumer.md` -> `examples/messaging-and-pubsub/queue_consumer`
- `docs/patterns/scheduled-and-background/timer-cron-job.md` -> `examples/scheduled-and-background/timer_cron_job`
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

1. Copy a nearby page under `docs/patterns/<category>/` into a new pattern page and keep the section order consistent.
2. Add a matching runnable project under `examples/`.
3. Document local run steps and expected output.
4. Include production constraints and failure behavior.
5. Add docs navigation entry in `mkdocs.yml`.

See [Contributing Guidelines](contributing.md) for review standards.

## Ecosystem integration

The cookbook is designed to work with companion projects:

- `azure-functions-scaffold-python` for generating starter projects
- `azure-functions-validation-python` for request/response validation helpers
- `azure-functions-openapi-python` for contract generation and Swagger UI
- `azure-functions-logging-python` for structured logs
- `azure-functions-doctor-python` for local environment checks

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
