# Azure Functions Python Cookbook

[![Python Version](https://img.shields.io/badge/python-3.11%20%7C%203.12%20%7C%203.13%20%7C%203.14-blue)](https://github.com/yeongseon/azure-functions-cookbook-python)
[![CI](https://github.com/yeongseon/azure-functions-cookbook-python/actions/workflows/ci-smoke.yml/badge.svg)](https://github.com/yeongseon/azure-functions-cookbook-python/actions/workflows/ci-smoke.yml)
[![codecov](https://codecov.io/gh/yeongseon/azure-functions-cookbook-python/branch/main/graph/badge.svg)](https://codecov.io/gh/yeongseon/azure-functions-cookbook-python)
[![pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit)](https://pre-commit.com/)
[![Docs](https://github.com/yeongseon/azure-functions-cookbook-python/actions/workflows/docs.yml/badge.svg)](https://github.com/yeongseon/azure-functions-cookbook-python/actions/workflows/docs.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

Read this in: [Korean](README.ko.md) | [日本語](README.ja.md) | [简体中文](README.zh-CN.md)

> This English README is canonical. Translations are community-maintained snapshots that may lag behind it; each states the release it was last aligned with. See [Documentation and Translations](CONTRIBUTING.md#documentation-and-translations).

Practical recipes for building real-world Azure Functions with Python.

> **Supported Python: 3.11, 3.12, 3.13, and 3.14.** The authoritative range is `requires-python` in [`pyproject.toml`](pyproject.toml). All four minors are generally available on the Azure Functions Python runtime, so pick the newest one your dependencies allow. See [Azure Functions supported languages](https://learn.microsoft.com/azure/azure-functions/supported-languages) for runtime end-of-support dates.

> **Stability and verification.** The Cookbook is released as `0.x` snapshots and the toolkit packages it uses are `<1`, so recipe routes and settings carry no SemVer promise. "Verified" means only what a recipe's `verification` level in `recipe.yaml` says (`docs`, `unit` or `func-host`); no recipe is verified in a deployed Azure environment. See [Stability and compatibility](docs/stability-and-compatibility.md).

## Why Use It

Starting a new Azure Functions project often means piecing together scattered documentation,
blog posts, and sample code. This cookbook provides curated, runnable recipes that answer:

- What should I build for this scenario?
- How should the architecture look?
- How do I start from a working baseline?

## Scope

- Azure Functions Python **v2 programming model**
- Decorator-based `func.FunctionApp()` applications
- Practical recipes with runnable examples
- Architecture explanations and production notes

This repository is content-first. It is not a CLI tool.

`main` is moving development content; tagged [GitHub Releases](https://github.com/yeongseon/azure-functions-cookbook-python/releases) are reproducible snapshots (the cookbook is not published to PyPI). See [Versions, snapshots, and verification](docs/snapshots-and-verification.md) for what each CI level does and does not verify.

## Choose Another Option When...

These recipes teach Azure Functions Python v2 patterns. Pick something else when:

- **You need a full web framework.** HTTP recipes use one plain `@app.route` handler per route. For an existing FastAPI/Starlette-style app, or when you need its middleware and routing, wrap the ASGI app with [`AsgiFunctionApp`](https://learn.microsoft.com/python/api/azure-functions/azure.functions.asgifunctionapp) or run it in a container. HTTP-triggered functions must respond within [230 seconds](https://learn.microsoft.com/azure/azure-functions/functions-scale#function-app-timeout-duration) whatever the function timeout is.
- **You need exact database-change semantics.** `azure-functions-db` (used by several recipes) includes a poll-based pseudo trigger. For Azure SQL, the built-in [SQL trigger](https://learn.microsoft.com/azure/azure-functions/functions-bindings-azure-sql-trigger) is based on SQL change tracking. For Cosmos DB, the [Cosmos DB trigger](https://learn.microsoft.com/azure/azure-functions/functions-bindings-cosmosdb-v2-trigger) reads the change feed, which publishes inserts and updates but not deletes, and Cosmos DB documents [at-least-once delivery](https://learn.microsoft.com/azure/cosmos-db/change-feed-processor) for its change feed processor. The [Outbox Pattern](examples/reliability/outbox_pattern/) recipe relays from that change feed and states that it is not exactly-once; if you need exactly-once, make consumers idempotent or choose a platform feature that provides it.
- **Native telemetry is enough.** The Python `logging` root logger already reaches Application Insights when your app runs in Azure, and Functions supports [OpenTelemetry](https://learn.microsoft.com/azure/azure-functions/opentelemetry-howto) with Azure Monitor. Skip the extra structured-logging layer used in the [Observability Tracing](examples/runtime-and-ops/observability_tracing/) recipe unless you want its correlation-ID conventions.
- **The official tools already do the job.** Use [`func init`/`func new`](https://learn.microsoft.com/azure/azure-functions/functions-core-tools-reference#func-init) or [`azd init`](https://learn.microsoft.com/azure/developer/azure-developer-cli/reference#azd-init) to start a project, and the portal's [Diagnose and solve problems](https://learn.microsoft.com/azure/azure-functions/functions-diagnostics) for a deployed app, before reaching for the scaffold and doctor recipes.
- **Your LangGraph agent outgrows Functions.** The LangGraph recipes run short request/response graphs; none demonstrates streaming, and the persistent Blob memory in [Personal LangGraph Agent](examples/ai-and-agents/personal_langgraph_agent/) does not promise exactly-once tool effects. For runs longer than the HTTP limit above, streaming, or durable execution across instances, look at [LangSmith Deployment](https://docs.langchain.com/langsmith/deployments) (it advertises durable execution, real-time streaming and horizontal scaling) or host the agent on [Azure Container Apps](https://learn.microsoft.com/azure/container-apps/overview).
- **A plain Functions recipe is enough.** Many recipes use only `azure-functions` ([Toolkit usage by recipe](docs/toolkit-usage.md) lists which). If you only need the trigger or binding pattern, start from those and add an optional toolkit package only for a need you actually have.

## Quick Index

Jump to a category: [APIs and Ingress](#apis-and-ingress) · [Scheduled and Background](#scheduled-and-background) · [Blob and File Triggers](#blob-and-file-triggers) · [Async APIs and Jobs](#async-apis-and-jobs) · [Messaging and Pub/Sub](#messaging-and-pubsub) · [Streams and Telemetry](#streams-and-telemetry) · [Data and Pipelines](#data-and-pipelines) · [Orchestration and Workflows](#orchestration-and-workflows) · [Reliability](#reliability) · [Security and Tenancy](#security-and-tenancy) · [Runtime and Ops](#runtime-and-ops) · [Realtime](#realtime) · [AI and Agents](#ai-and-agents) · [Guides](#guides)

Prefer to search programmatically? A machine-readable index of every recipe
(slug, title, category, example_path, tags) lives in [`recipes.json`](recipes.json),
regenerated with `python scripts/gen_recipe_index.py`. Look recipes up by
keyword or tag with the `find_recipe` helper:

```python
from azure_functions_python_cookbook.recipes import find_recipe

# Free-text search across slug, title, category, description, and tags
for recipe in find_recipe("durable retry"):
    print(recipe.title, "->", recipe.example_path)

# Filter by an exact tag
durable = find_recipe(tag="durable")
```

---

## Recipes

<!-- BEGIN RECIPES (generated by scripts/gen_recipe_table.py) -->

### APIs and Ingress

| Recipe | Difficulty | Description |
| --- | --- | --- |
| [APIM Function Backend](examples/apis-and-ingress/apim_function_backend/) | Intermediate | HTTP-triggered Azure Functions backend intended to sit behind Azure API Management policies for auth, rate limiting, and caching. |
| [BFF Facade API](examples/apis-and-ingress/bff_facade_api/) | Intermediate | HTTP Backend-for-Frontend facade that aggregates multiple backend service calls into one client-facing response. |
| [EasyAuth Claims Extraction](examples/apis-and-ingress/auth_easyauth/) | Intermediate | EasyAuth principal extraction with role-based access control for Azure Functions. |
| [Full Stack CRUD API](examples/apis-and-ingress/full_stack_crud_api/) | Advanced | Showcase HTTP API that wires the Azure Functions Python DX Toolkit together around one `items` resource. |
| [HTTP Auth Levels](examples/apis-and-ingress/http_auth_levels/) | Beginner | HTTP trigger example that demonstrates anonymous, function-key, and admin-key endpoints. |
| [HTTP Routing Query Body](examples/apis-and-ingress/http_routing_query_body/) | Beginner | HTTP CRUD and search example showing route params, query strings, JSON body parsing, and status codes. |
| [Hello HTTP Minimal](examples/apis-and-ingress/hello_http_minimal/) | Beginner | Minimal HTTP-triggered Azure Function that returns a greeting. |
| [JWT Bearer Validation](examples/apis-and-ingress/auth_jwt_validation/) | Intermediate | JWT Bearer token validation with claim-based access control for Azure Functions. |
| [Multi-Tenant Auth](examples/apis-and-ingress/auth_multitenant/) | Intermediate | Multi-tenant access control with tenant allowlist for Azure Functions. |
| [OpenAPI Return-Type Inference](examples/apis-and-ingress/openapi_inference/) | Intermediate | Infer the OpenAPI 200 response schema directly from a handler's return-type annotation using azure-functions-openapi. |
| [OpenAPI Return-Type Inference Opt-Out](examples/apis-and-ingress/openapi_inference_opt_out/) | Intermediate | Opt out of inferred OpenAPI 200 response schemas per handler with infer_return_types=False. |
| [OpenAPI Validation Supersedes Inference](examples/apis-and-ingress/openapi_supersedes/) | Intermediate | Show how a validation response_model supersedes the return-type-inferred OpenAPI 200 schema. |
| [Webhook GitHub](examples/apis-and-ingress/webhook_github/) | Intermediate | GitHub webhook receiver example with HMAC-SHA256 signature verification. |
| [scaffold_walkthrough_app](examples/apis-and-ingress/scaffold_walkthrough_app/) | Beginner | This recipe is the **committed output of `azure-functions-scaffold`** with the default `strict` preset. Use it to see exactly what the scaffold CLI generates for a fresh Azure Functions Python v2 HTTP project and to learn the recommended local dev loop. |

### Scheduled and Background

| Recipe | Difficulty | Description |
| --- | --- | --- |
| [Durable Timer Reminder](examples/scheduled-and-background/durable_timer_reminder/) | Intermediate | Durable Functions orchestration that waits for a long delay and then executes a reminder callback activity. |
| [Queue Scheduled Dispatch](examples/scheduled-and-background/queue_scheduled_dispatch/) | Intermediate | Timer-driven scheduled dispatch pattern that releases due work onto Azure Storage Queue for downstream workers. |
| [Timer Cron Job](examples/scheduled-and-background/timer_cron_job/) | Beginner | Timer-triggered Azure Function that runs a scheduled maintenance job every 5 minutes. |

### Blob and File Triggers

| Recipe | Difficulty | Description |
| --- | --- | --- |
| [Blob CSV to Table](examples/blob-and-file-triggers/blob_csv_to_table/) | Intermediate | Event Grid-driven ingestion pattern that reads uploaded CSV blobs and writes normalized rows into Azure Table Storage. |
| [Blob Event Grid Trigger](examples/blob-and-file-triggers/blob_eventgrid_trigger/) | Intermediate | Blob-triggered Azure Function configured for Event Grid source notifications. |
| [Blob Thumbnail Generator](examples/blob-and-file-triggers/blob_thumbnail_generator/) | Intermediate | Event Grid-driven blob processor that generates thumbnails and writes them to a separate output container. |
| [Blob Upload Processor](examples/blob-and-file-triggers/blob_upload_processor/) | Intermediate | Blob-triggered Azure Function that processes uploaded files from `uploads/{name}`. |

### Async APIs and Jobs

| Recipe | Difficulty | Description |
| --- | --- | --- |
| [Async HTTP 202 Polling](examples/async-apis-and-jobs/async_http_polling/) | Intermediate | HTTP-triggered Durable Functions example that returns `202 Accepted` and a `statusQueryGetUri` for client polling. |
| [Callback Completion](examples/async-apis-and-jobs/callback_completion/) | Intermediate | HTTP + Queue example that accepts work at `/api/tasks` and sends an HTTP callback when background processing finishes. |
| [Queue-Backed Job](examples/async-apis-and-jobs/queue_backed_job/) | Intermediate | HTTP + Storage Queue recipe for accepting a job, returning `202 Accepted`, and polling a stored status record. |

### Messaging and Pub/Sub

| Recipe | Difficulty | Description |
| --- | --- | --- |
| [Claim Check Pattern](examples/messaging-and-pubsub/claim_check_pattern/) | Advanced | Large-message pattern that stores payloads in Blob Storage and passes only a reference through the queue. |
| [Event Grid Domain Events](examples/messaging-and-pubsub/eventgrid_domain_events/) | Intermediate | HTTP-triggered Azure Function that publishes custom order domain events to an Event Grid custom topic, plus an Event Grid-triggered subscriber that logs the resulting events. |
| [Event Grid Event Router](examples/messaging-and-pubsub/eventgrid_router/) | Intermediate | Event Grid-triggered Azure Function that routes events to different handlers using event type and subject filters. |
| [Queue Consumer](examples/messaging-and-pubsub/queue_consumer/) | Beginner | Queue-triggered Azure Function that parses and processes task messages. |
| [Queue Producer](examples/messaging-and-pubsub/queue_producer/) | Beginner | HTTP-triggered Azure Function that validates JSON and enqueues tasks to Storage Queue. |
| [Service Bus DLQ Replay](examples/messaging-and-pubsub/servicebus_dlq_replay/) | Advanced | Replay dead-lettered Service Bus queue messages back to the main queue after inspection and remediation. |
| [Service Bus Sessions](examples/messaging-and-pubsub/servicebus_sessions/) | Advanced | Azure Functions example showing ordered message processing with Azure Service Bus sessions. |
| [Service Bus Topic Fan-out](examples/messaging-and-pubsub/servicebus_topic_fanout/) | Intermediate | Azure Functions example showing Service Bus topic fan-out with three independent subscription handlers. |
| [Service Bus Worker](examples/messaging-and-pubsub/servicebus_worker/) | Intermediate | Service Bus queue-triggered Azure Function for reliable background work consumption. |

### Streams and Telemetry

| Recipe | Difficulty | Description |
| --- | --- | --- |
| [Event Hub Batch Window](examples/streams-and-telemetry/eventhub_batch_window/) | Intermediate | Event Hub-triggered Azure Function that processes a batch window and logs aggregate telemetry totals. |
| [Event Hub Checkpoint Replay](examples/streams-and-telemetry/eventhub_checkpoint_replay/) | Advanced | Azure Functions example showing replay-aware Event Hub consumption with offset tracking and idempotent processing. |
| [Event Hub Consumer](examples/streams-and-telemetry/eventhub_consumer/) | Intermediate | Event Hub-triggered Azure Function for near real-time telemetry stream processing. |

### Data and Pipelines

| Recipe | Difficulty | Description |
| --- | --- | --- |
| [CQRS Read Projection](examples/data-and-pipelines/cqrs_read_projection/) | Advanced | CQRS sample for Azure Functions Python where: |
| [Change Feed Processor](examples/data-and-pipelines/change_feed_processor/) | Intermediate | Cosmos DB change feed-triggered Azure Function for downstream synchronization. |
| [DB Input and Output Bindings](examples/data-and-pipelines/db_input_output/) | Intermediate | Demonstrates `azure-functions-db-python` input/output bindings with SQLAlchemy-backed storage, combined with `azure-functions-validation-python` and `azure-functions-openapi-python`. |
| [ETL Enrichment](examples/data-and-pipelines/etl_enrichment/) | Intermediate | Blob-triggered ETL example that reads raw JSON customer records, enriches them with lookup data, and writes the enriched rows to a database. |
| [File Processing Pipeline](examples/data-and-pipelines/file_processing_pipeline/) | Intermediate | Blob-triggered Azure Function that validates uploaded CSV or JSON files, transforms the records, and persists the processed result to a database. |
| [SQLAlchemy REST Pagination](examples/data-and-pipelines/sqlalchemy_rest_pagination/) | Intermediate | HTTP API example that combines: |

### Orchestration and Workflows

| Recipe | Difficulty | Description |
| --- | --- | --- |
| [Async Job Lifecycle](examples/orchestration-and-workflows/async_job_lifecycle/) | Advanced | Durable Functions recipe for full async job lifecycle management: create, status, cancel, and purge. |
| [Durable Determinism Gotchas](examples/orchestration-and-workflows/durable_determinism_gotchas/) | Advanced | Durable Functions orchestrator showing deterministic coding patterns. |
| [Durable Entity Counter](examples/orchestration-and-workflows/durable_entity_counter/) | Intermediate | Durable Entity example managing counter state. |
| [Durable Fan-Out Fan-In](examples/orchestration-and-workflows/durable_fan_out_fan_in/) | Intermediate | Durable Functions fan-out/fan-in orchestration with parallel activities. |
| [Durable Hello Sequence](examples/orchestration-and-workflows/durable_hello_sequence/) | Beginner | Durable Functions orchestrator chaining activities in sequence. |
| [Durable Human Interaction](examples/orchestration-and-workflows/durable_human_interaction/) | Intermediate | Durable Functions workflow waiting for an external approval event with timeout. |
| [Durable Retry Pattern](examples/orchestration-and-workflows/durable_retry_pattern/) | Intermediate | Durable Functions orchestration retrying a flaky activity. |
| [Durable Singleton Monitor](examples/orchestration-and-workflows/durable_singleton_monitor/) | Advanced | Durable Functions singleton orchestration that continuously polls an external dependency and emits alerts on changes. |
| [Durable Unit Testing](examples/orchestration-and-workflows/durable_unit_testing/) | Intermediate | Durable Functions sample focused on mock-based orchestrator unit testing. |
| [Saga Compensation](examples/orchestration-and-workflows/saga_compensation/) | Advanced | Durable Functions saga orchestration that compensates previously completed steps on failure. |
| [Sub-Orchestration](examples/orchestration-and-workflows/sub_orchestration/) | Advanced | Durable Functions parent orchestration delegating work to two child sub-orchestrators. |

### Reliability

| Recipe | Difficulty | Description |
| --- | --- | --- |
| [Circuit Breaker](examples/reliability/circuit_breaker/) | Intermediate | This recipe shows an HTTP-triggered Azure Function protecting a downstream API with a simple in-memory circuit breaker. |
| [Outbox Pattern](examples/reliability/outbox_pattern/) | Advanced | Transactional outbox sample for Azure Functions Python where: |
| [Poison Message Handling](examples/reliability/poison_message_handling/) | Intermediate | Queue-triggered Azure Functions recipe that lets repeated failures move automatically to the poison queue and then logs the failed payload for operator follow-up. |
| [Rate Limiting / Throttle](examples/reliability/rate_limiting/) | Intermediate | This recipe shows an HTTP-triggered Azure Function using an in-memory token bucket to throttle requests and return `429 Too Many Requests` when the local bucket is empty. |
| [Retry and Idempotency](examples/reliability/retry_and_idempotency/) | Intermediate | This recipe shows two related resilience patterns: |

### Security and Tenancy

| Recipe | Difficulty | Description |
| --- | --- | --- |
| [Managed Identity Service Bus](examples/security-and-tenancy/managed_identity_servicebus/) | Advanced | This recipe shows a Service Bus queue trigger using `connection="ServiceBusConnection"`. |
| [Managed Identity Storage](examples/security-and-tenancy/managed_identity_storage/) | Advanced | This recipe shows an Azure Storage Queue trigger using `connection="StorageConnection"`. You can back that setting with either a connection string or managed identity settings. |
| [Secretless Key Vault](examples/security-and-tenancy/secretless_keyvault/) | Intermediate | HTTP-triggered Azure Function that reads secrets from environment variables populated by Azure Key Vault references. The function uses standard environment access and `azure_functions_logging` only. |
| [Tenant Isolation](examples/security-and-tenancy/tenant_isolation/) | Advanced | HTTP recipe for resolving tenant context from `X-Tenant-ID` or a bearer token claim, then querying a tenant-specific database with `azure-functions-db-python`. |

### Runtime and Ops

| Recipe | Difficulty | Description |
| --- | --- | --- |
| [Blueprint Modular App](examples/runtime-and-ops/blueprint_modular_app/) | Intermediate | This recipe demonstrates a modular Azure Functions app using `func.Blueprint`. |
| [Cold Start Mitigation](examples/runtime-and-ops/cold_start_mitigation/) | Intermediate | This recipe demonstrates practical cold-start mitigation for Azure Functions Python: |
| [Concurrency Tuning](examples/runtime-and-ops/concurrency_tuning/) | Advanced | This recipe demonstrates host-level dynamic concurrency: |
| [Doctor Diagnostics Endpoint](examples/runtime-and-ops/doctor_diagnostics_endpoint/) | Intermediate | Expose [`azure-functions-doctor`](https://github.com/yeongseon/azure-functions-doctor-python) diagnostics as authenticated HTTP endpoints so operators can query deployment health post-deploy without shelling into the container. |
| [Observability Tracing](examples/runtime-and-ops/observability_tracing/) | Intermediate | HTTP-triggered tracing recipe showing correlation ID propagation, structured logging, and Application Insights-friendly trace context. |
| [Output Binding vs SDK](examples/runtime-and-ops/output_binding_vs_sdk/) | Intermediate | This recipe compares two ways to send the same queue message: |
| [host.json Tuning](examples/runtime-and-ops/host_json_tuning/) | Advanced | This recipe focuses on host-level tuning using a timer trigger plus a richly configured `host.json`. |

### Realtime

| Recipe | Difficulty | Description |
| --- | --- | --- |
| [WebSocket Proxy](examples/realtime/websocket_proxy/) | Advanced | Azure Functions front door for Azure Web PubSub that negotiates client tokens and forwards publish requests. |

### AI and Agents

| Recipe | Difficulty | Description |
| --- | --- | --- |
| [AI Image Generation](examples/ai-and-agents/ai_image_generation/) | Intermediate | HTTP-triggered sample that sends a prompt to Azure OpenAI image generation and returns the generated image URL. |
| [Azure OpenAI Direct Chat](examples/ai-and-agents/openai_direct_chat/) | Beginner | Minimal HTTP-triggered Azure Functions sample that sends one message to Azure OpenAI with the `openai` Python SDK. |
| [Durable AI Pipeline](examples/ai-and-agents/durable_ai_pipeline/) | Advanced | Durable Functions sample that orchestrates three AI steps: embedding, vector search, and answer generation. |
| [Embedding Vector Search](examples/ai-and-agents/embedding_vector_search/) | Advanced | HTTP-triggered sample that creates Azure OpenAI embeddings and uses them to run a vector query against Azure AI Search. |
| [LangGraph Agent](examples/ai-and-agents/langgraph_agent/) | Intermediate | Demonstrates `azure-functions-langgraph-python` adapter with `azure-functions-logging-python`, `azure-functions-validation-python`, and `azure-functions-openapi-python`. |
| [LangGraph RAG Agent](examples/ai-and-agents/langgraph_rag_agent/) | Advanced | This example shows how to combine: |
| [Langgraph Tool Use](examples/ai-and-agents/langgraph_tool_use/) | Advanced | Tool-use LangGraph agent with azure-functions-langgraph, routing between a reasoning node and callable tools. |
| [MCP Server Example](examples/ai-and-agents/mcp_server_example/) | Advanced | This example hosts a manual Model Context Protocol (MCP) server on Azure Functions using a standard HTTP trigger and JSON-RPC 2.0 messages. |
| [Personal LangGraph Agent](examples/ai-and-agents/personal_langgraph_agent/) | Advanced | Build a tool-calling personal notes agent with deterministic local mode, Azure OpenAI, and restart-safe Blob memory. |
| [RAG Knowledge API](examples/ai-and-agents/rag_knowledge_api/) | Advanced | Demonstrates a minimal RAG API using Azure AI Search and Azure OpenAI, combined with `azure-functions-validation-python`, `azure-functions-openapi-python`, and `azure-functions-logging-python`. |
| [Streaming AI Response](examples/ai-and-agents/streaming_ai_response/) | Intermediate | HTTP-triggered sample that converts Azure OpenAI streaming chat completions into Server-Sent Events. |

### Guides

| Recipe | Difficulty | Description |
| --- | --- | --- |
| [Local Run and Direct Invoke](examples/guides/local_run_and_direct_invoke/) | Beginner | This example shows two local testing workflows for an Azure Functions Python app: |

_82 recipes._

<!-- END RECIPES -->

Each pattern page lives under `docs/patterns/` with a matching runnable project in `examples/`.

## Running Examples

Every recipe runs locally with the Azure Functions Core Tools. Most triggers can
be emulated with [Azurite](https://learn.microsoft.com/azure/storage/common/storage-use-azurite);
a few need real cloud services or API keys. The table below lists the external
dependency by category and how to run without a live service.

<details>
<summary><strong>Local emulation cheat sheet</strong> — external dependency & how to run each category locally</summary>

| Category | External service | Run locally with |
| --- | --- | --- |
| APIs and Ingress | None (plain HTTP) | `func start` — no emulator needed |
| Scheduled and Background | Storage (timer/queue state) | Azurite (`AzureWebJobsStorage=UseDevelopmentStorage=true`) |
| Blob and File Triggers | Azure Storage / Event Grid | Azurite for blobs; Event Grid trigger needs a real subscription or replayed payload |
| Async APIs and Jobs | Storage Queue | Azurite |
| Messaging and Pub/Sub | Service Bus / Event Grid / Storage Queue | Azurite for Storage Queue; Service Bus & Event Grid need a real namespace |
| Streams and Telemetry | Event Hubs | Real Event Hubs namespace (no local emulator) |
| Data and Pipelines | Cosmos DB / SQL / Storage | Azurite or SQLite for DB recipes; Cosmos change-feed needs a real account |
| Orchestration and Workflows | Durable Functions (Storage) | Azurite (Durable task hub) |
| Reliability | Storage Queue | Azurite |
| Security and Tenancy | Managed Identity / Key Vault / Service Bus | Local dev uses connection strings; identity paths need Azure |
| Runtime and Ops | None / Storage | `func start`; some use Azurite |
| Realtime | Web PubSub / SignalR | Real Web PubSub service |
| AI and Agents | Azure OpenAI / Azure AI Search | Runs against a local stub by default; set endpoint/key env vars for real services |
| Guides | None | `func start` |

</details>

Each example's `README.md` documents its specific `local.settings.json` values.
AI examples ship a local fallback stub so they run without credentials — see
each recipe's README for the environment variables that switch on real services.

For a cumulative model → tool → model walkthrough with per-thread memory and optional
Blob persistence, see [Personal LangGraph Agent](docs/patterns/ai-and-agents/personal-langgraph-agent.md).
Its explicit fake mode is credential-free; real mode fails clearly instead of falling back.

The [MCP recipe](examples/ai-and-agents/mcp_server_example/) accepts
`notifications/initialized` after `initialize` with HTTP 202 and an empty body.
Its tool inputs are schema-checked; the calculator uses bounded AST arithmetic
without `eval` (see the recipe for supported operators and limits).

### Test tiers

Tests are separated by pytest marker so you can run the fast tier by default and
opt into the heavier tiers explicitly:

- **unit** (default) — `make test`; no external services, no emulator.
- **smoke** — `hatch run smoke`; module-import checks for non-emulatable triggers.
- **e2e** — `hatch run e2e`; requires Azurite and a running `func` host.

## Repository Layout

```text
docs/              Published documentation
  patterns/        Curated pattern documents
examples/          Runnable example projects organized by category
  apis-and-ingress/
  scheduled-and-background/
  blob-and-file-triggers/
  async-apis-and-jobs/
  messaging-and-pubsub/
  streams-and-telemetry/
  data-and-pipelines/
  orchestration-and-workflows/
  reliability/
  security-and-tenancy/
  runtime-and-ops/
  realtime/
  ai-and-agents/
  guides/
```

## Development

```bash
git clone https://github.com/yeongseon/azure-functions-cookbook-python.git
cd azure-functions-cookbook-python
make install
make check-all
make docs
```

## Documentation

Request assignment by commenting on the task; the maintainer confirms ownership,
and duplicate PRs must not be opened without coordination. Issues labeled
`good first issue` or `help wanted`, or assigned to an external contributor, are
reserved for human contributors unless the maintainer explicitly authorizes that
particular issue; see [contributor-reserved issues](CONTRIBUTING.md#contributor-reserved-issues).

- Product requirements: `PRD.md`
- Design principles: `DESIGN.md`
- Contributing guide: `CONTRIBUTING.md`
- AI & Agent Learning Path: [`docs/patterns/ai-and-agents/learning-path.md`](docs/patterns/ai-and-agents/learning-path.md)

## Ecosystem

This cookbook is the **dogfood** of the **Azure Functions Python DX Toolkit**: many examples are real, runnable Azure Functions that opt in to toolkit libraries in production-realistic scenarios, while others are plain Azure Functions examples that use no toolkit package. 47 of the 82 recipes declare at least one toolkit package and 35 are plain Azure Functions only; [Toolkit usage by recipe](docs/toolkit-usage.md) lists both kinds.

The **Status** column reflects how each package is currently used in this repo: **Dogfooded** (declared as a dependency by example projects), **Experimental** (advertised but not yet used by any example), or **Planned** (integration tracked but not started). Counts are the number of example projects whose `pyproject.toml` declares the package, the same definition the repository tests use for the docs home page; one CLI-generated example (`scaffold_walkthrough_app`) declares the packages its template generates and is called out where it applies. A declared dependency is not evidence that the package was exercised in a Functions host or in Azure; see each recipe's `verification` level and [Stability and compatibility](docs/stability-and-compatibility.md).

| Package | Role | Status |
|---------|------|--------|
| [azure-functions-openapi-python](https://github.com/yeongseon/azure-functions-openapi-python) | OpenAPI spec generation and Swagger UI | Dogfooded ([28 examples](https://github.com/search?q=repo%3Ayeongseon%2Fazure-functions-cookbook-python+azure_functions_openapi+path%3Aexamples&type=code)) |
| [azure-functions-validation-python](https://github.com/yeongseon/azure-functions-validation-python) | Request/response validation and serialization | Dogfooded ([26 examples, one CLI-generated](https://github.com/search?q=repo%3Ayeongseon%2Fazure-functions-cookbook-python+azure_functions_validation+path%3Aexamples&type=code)) |
| [azure-functions-logging-python](https://github.com/yeongseon/azure-functions-logging-python) | Structured logging and observability | Dogfooded ([45 examples](https://github.com/search?q=repo%3Ayeongseon%2Fazure-functions-cookbook-python+azure_functions_logging+path%3Aexamples&type=code)) |
| [azure-functions-db-python](https://github.com/yeongseon/azure-functions-db-python) | SQLAlchemy-powered DB integration helpers (poll-based pseudo trigger, input/output/client injection) | Dogfooded ([9 examples](https://github.com/search?q=repo%3Ayeongseon%2Fazure-functions-cookbook-python+azure_functions_db+path%3Aexamples&type=code)) |
| [azure-functions-langgraph-python](https://github.com/yeongseon/azure-functions-langgraph-python) | LangGraph deployment adapter for Azure Functions | Dogfooded ([4 examples](https://github.com/search?q=repo%3Ayeongseon%2Fazure-functions-cookbook-python+azure_functions_langgraph+path%3Aexamples&type=code)) |
| [azure-functions-scaffold-python](https://github.com/yeongseon/azure-functions-scaffold-python) | Project scaffolding CLI | Dogfooded ([1 example, CLI-generated](examples/apis-and-ingress/scaffold_walkthrough_app/)) |
| [azure-functions-doctor-python](https://github.com/yeongseon/azure-functions-doctor-python) | Pre-deploy diagnostic CLI | Dogfooded ([2 examples, one CLI-generated](https://github.com/search?q=repo%3Ayeongseon%2Fazure-functions-cookbook-python+azure_functions_doctor+path%3Aexamples&type=code)) |
| **azure-functions-cookbook-python** *(this repo)* | Dogfood examples for the full toolkit | 82 examples |

## For AI Coding Assistants

This repository includes `llms.txt` and `llms-full.txt` in the root directory — quick and full references optimized for LLM context windows. Use them for better context when working with these recipes in AI-assisted coding environments.

## Contributing

Contributions are welcome. The [Contributing Guide](CONTRIBUTING.md) covers local setup, the checks to run, and the pull request workflow.

Looking for something to work on?

- [Good first issue](https://github.com/yeongseon/azure-functions-cookbook-python/labels/good%20first%20issue): small, self-contained starter tasks.
- [Help wanted](https://github.com/yeongseon/azure-functions-cookbook-python/labels/help%20wanted): tasks that may need more familiarity with this codebase or Azure Functions.

Please comment on an issue to request assignment before you open a pull request. Either list can be empty at any time, so bug reports and small documentation suggestions are always welcome too.

## Disclaimer

This project is an independent community project and is not affiliated with,
endorsed by, or maintained by Microsoft.

Azure and Azure Functions are trademarks of Microsoft Corporation.

## License

MIT
