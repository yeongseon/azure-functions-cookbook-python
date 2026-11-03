# Anonymous endpoint classification

Many recipes bind HTTP routes with `func.AuthLevel.ANONYMOUS` because they are tutorials meant to run locally. Anonymous is not automatically unsafe, and switching every route to `FUNCTION` would break the recipes that deliberately demonstrate JWT, EasyAuth, webhook signatures or public health checks. This page classifies **every** recipe by deployment risk so you know which examples are safe to publish as-is and which need extra controls first.

!!! warning "Function keys are not authorization"
    A function key is a shared secret that gates the HTTP trigger. It does not identify a user, does not enforce per-user permissions, and does not provide rate limiting, quotas or abuse protection. For anything exposed to untrusted callers, add identity (Microsoft Entra ID or EasyAuth), per-caller authorization in the handler, and edge controls such as API Management or Front Door limits.

Ordinary `func start` does not enforce function keys locally, so the auth level only matters after deployment.

## How the classification is maintained

The classification comes from `security/recipe-security-manifest.json`, which `make security-manifest` compares against each recipe's declared bindings. This page is a reading aid generated from that manifest; the manifest is authoritative. Route lists show the auth level of each HTTP route as indexed by the check.

When you add a recipe with an HTTP route, add it to the manifest with a category that matches the table below and an honest reason. Prefer `FUNCTION` unless the recipe's purpose requires anonymous access.

## Categories

| Category | Meaning |
|---|---|
| **Paid backend** (3) | Calls a billed model API. Defaults to `FUNCTION`; becomes anonymous only with the explicit `COOKBOOK_PUBLIC_DEMO=true` opt-in. See [Paid AI recipe security](paid-ai-security.md). |
| **Cloud backend demo (anonymous)** (25) | Anonymous routes that start jobs or write to Azure services (Storage, Service Bus, Durable, Event Grid, Web PubSub, search or model backends). Tutorial defaults only: put identity-based access, per-caller authorization and quotas in front of them before deploying. |
| **Local demo (anonymous)** (11) | Anonymous routes with no paid or external backend (greetings, in-memory CRUD, in-process rate limiter, tracing). Intended for learning and local runs; not an access boundary. |
| **Authentication demonstration** (4) | Binding is anonymous or mixed on purpose because the recipe demonstrates handler-level JWT, tenant or EasyAuth checks, or contrasts auth levels. |
| **Edge authentication demonstration** (1) | Anonymous backend meant to sit behind API Management; restrict direct backend ingress in production. |
| **Public documentation routes** (1) | Anonymous health and OpenAPI/Swagger routes; the webhook route keeps `FUNCTION`. |
| **Public webhook with own verification** (1) | Anonymous by design; the handler verifies an HMAC-SHA256 signature. |
| **Public health** (1) | Only the lightweight health route is anonymous; other routes inherit `FUNCTION`. |
| **Protected (function key)** (12) | All HTTP routes require `FUNCTION`. A function key is shared-secret access control, not per-user authorization. |
| **No HTTP route** (23) | Queue, blob, timer, Event Hub, Service Bus or Event Grid triggers only. |

## Deployment guidance by risk

- **Paid backend**: keep the default `FUNCTION` level, leave `COOKBOOK_PUBLIC_DEMO` unset, and add Entra/APIM and distributed rate limits if callers are untrusted.
- **Cloud backend demo**: do not publish unchanged. Authenticate callers, authorize each operation (for example job status, cancel, purge, approve), restrict network ingress, and cap concurrency and cost.
- **Local demo**: safe to run locally; if deployed, treat every route as public.
- **Authentication, edge and webhook demonstrations**: the anonymous binding is intentional, but the protection lives in the handler or in front of the app. Copy the verification code, not just the binding.
- **Protected**: a function key is the only gate; still add per-user authorization where data is user-specific.

## Recipes by category

### Paid backend

| Recipe | HTTP routes | Note |
|---|---|---|
| [AI Image Generation](patterns/ai-and-agents/ai-image-generation.md) | `generate_image=FUNCTION` | One paid image per request; FUNCTION unless explicitly opted into a public demo. |
| [Azure OpenAI Direct Chat](patterns/ai-and-agents/openai-direct-chat.md) | `chat=FUNCTION` | Paid chat requires FUNCTION unless explicitly opted into a public demo. |
| [Streaming AI Response](patterns/ai-and-agents/streaming-ai-response.md) | `stream_chat=FUNCTION` | Paid streaming chat requires FUNCTION unless explicitly opted into a public demo. |

### Cloud backend demo (anonymous)

| Recipe | HTTP routes | Note |
|---|---|---|
| [Durable AI Pipeline](patterns/ai-and-agents/durable-ai-pipeline.md) | `sample_result=ANONYMOUS`, `start_pipeline=ANONYMOUS` | Durable model/search demo; isolate ingress and apply quotas before deployment. |
| [Embedding Vector Search](patterns/ai-and-agents/embedding-vector-search.md) | `search=ANONYMOUS` | Embedding/search demo; requires production ingress and budget controls. |
| [LangGraph RAG Agent](patterns/ai-and-agents/langgraph-rag-agent.md) | `adapter-routes=ANONYMOUS`, `chat=ANONYMOUS`, `get_thread_state=ANONYMOUS` | RAG adapter/chat/state educational surface; isolate before deploying with credentials. |
| [RAG Knowledge API](patterns/ai-and-agents/rag-knowledge-api.md) | `ask=ANONYMOUS`, `healthz=ANONYMOUS`, `ingest=ANONYMOUS` | Anonymous health plus RAG ask/ingest demo; isolate data/model routes before production. |
| [Async HTTP 202 Polling](patterns/async-apis-and-jobs/async-http-202-polling.md) | `start_report_job=ANONYMOUS` | Durable polling tutorial; authorize job operations before production. |
| [Callback Completion](patterns/async-apis-and-jobs/callback-completion.md) | `submit_task=ANONYMOUS` | Queue callback tutorial; restrict callers and callback egress before production. |
| [Queue-Backed Job](patterns/async-apis-and-jobs/queue-backed-job.md) | `get_job_status=ANONYMOUS`, `submit_job=ANONYMOUS` | Storage-backed submission/status demo; production needs job authorization. |
| [Claim Check Pattern](patterns/messaging-and-pubsub/claim-check-pattern.md) | `enqueue_claim_check=ANONYMOUS` | Storage claim-check demo; restrict ingestion before production. |
| [Event Grid Domain Events](patterns/messaging-and-pubsub/eventgrid-domain-events.md) | `publish_order_event=ANONYMOUS` | Event publisher tutorial; restrict callers before production. |
| [Queue Producer](patterns/messaging-and-pubsub/queue-producer.md) | `enqueue_task=ANONYMOUS` | Queue ingestion tutorial; restrict public enqueue before production. |
| [Async Job Lifecycle](patterns/orchestration-and-workflows/async-job-lifecycle.md) | `cancel_job=ANONYMOUS`, `create_job=ANONYMOUS`, `get_job_status=ANONYMOUS`, `purge_job_history=ANONYMOUS` | Lifecycle demonstration; authorize create/status/cancel/purge per caller in production. |
| [Durable Determinism Gotchas](patterns/orchestration-and-workflows/durable-determinism-gotchas.md) | `start_determinism_demo=ANONYMOUS` | Durable starter tutorial; restrict ingress before deployment. |
| [Durable Entity Counter](patterns/orchestration-and-workflows/durable-entity-counter.md) | `get_counter=ANONYMOUS`, `signal_counter=ANONYMOUS` | Counter signal/read tutorial; production requires entity authorization. |
| [Durable Fan-Out Fan-In](patterns/orchestration-and-workflows/durable-fan-out-fan-in.md) | `start_fanout=ANONYMOUS` | Durable fan-out starter tutorial; restrict ingress and concurrency. |
| [Durable Hello Sequence](patterns/orchestration-and-workflows/durable-hello-sequence.md) | `start_sequence=ANONYMOUS` | Durable sequence starter tutorial; restrict ingress before deployment. |
| [Durable Human Interaction](patterns/orchestration-and-workflows/durable-human-interaction.md) | `approve_instance=ANONYMOUS`, `start_approval=ANONYMOUS` | Human approval tutorial; production requires caller/approver authorization. |
| [Durable Retry Pattern](patterns/orchestration-and-workflows/durable-retry-pattern.md) | `start_retry=ANONYMOUS` | Durable retry starter tutorial; restrict ingress before deployment. |
| [Durable Singleton Monitor](patterns/orchestration-and-workflows/durable-singleton-monitor.md) | `start_monitor=ANONYMOUS` | Singleton monitor starter tutorial; restrict ingress before deployment. |
| [Durable Unit Testing](patterns/orchestration-and-workflows/durable-unit-testing.md) | `start_unit_test=ANONYMOUS` | Durable testing tutorial; restrict starter ingress before deployment. |
| [Saga Compensation](patterns/orchestration-and-workflows/saga-compensation.md) | `start_saga_compensation=ANONYMOUS` | Saga starter tutorial; production requires caller authorization. |
| [Sub-Orchestration](patterns/orchestration-and-workflows/sub-orchestration.md) | `start_sub_orchestration=ANONYMOUS` | Sub-orchestration starter tutorial; restrict ingress before deployment. |
| [WebSocket Proxy](patterns/realtime/websocket-proxy.md) | `handle_event=ANONYMOUS`, `negotiate=ANONYMOUS`, `publish=ANONYMOUS` | PubSub negotiation/event/publish tutorial; configure identity and quotas before deployment. |
| [Circuit Breaker](patterns/reliability/circuit-breaker.md) | `circuit_breaker_demo=ANONYMOUS` | Circuit-breaker backend demo; restrict ingress and egress before production. |
| [Outbox Pattern](patterns/reliability/outbox-pattern.md) | `create_order=ANONYMOUS` | Outbox tutorial; production order submission requires caller authorization. |
| [Durable Timer Reminder](patterns/scheduled-and-background/durable-timer-reminder.md) | `start_reminder=ANONYMOUS` | Reminder starter tutorial; restrict ingress before deployment. |

### Local demo (anonymous)

| Recipe | HTTP routes | Note |
|---|---|---|
| [BFF Facade API](patterns/apis-and-ingress/bff-facade-api.md) | `dashboard=ANONYMOUS` | Local facade demo; backend configuration needs production ingress controls. |
| [Full Stack CRUD API](patterns/apis-and-ingress/full-stack-crud-api.md) | `create_item=ANONYMOUS`, `delete_item=ANONYMOUS`, `get_item=ANONYMOUS`, `list_items=ANONYMOUS`, `openapi_json=ANONYMOUS`, `update_item=ANONYMOUS` | Educational local CRUD and OpenAPI surface, not a production access boundary. |
| [Hello HTTP Minimal](patterns/apis-and-ingress/hello-http-minimal.md) | `hello=ANONYMOUS` | Public greeting with no paid backend. |
| [HTTP Routing Query Body](patterns/apis-and-ingress/http-routing-query-body.md) | `create_user_http=ANONYMOUS`, `delete_user_http=ANONYMOUS`, `get_user=ANONYMOUS`, `list_users=ANONYMOUS`, `search_users_http=ANONYMOUS`, `update_user_http=ANONYMOUS` | In-memory routing/CRUD tutorial without external backend. |
| [OpenAPI Return-Type Inference](patterns/apis-and-ingress/openapi-inference.md) | `inferred_greeting=ANONYMOUS` | Public schema inference greeting demo. |
| [OpenAPI Return-Type Inference Opt-Out](patterns/apis-and-ingress/openapi-inference-opt-out.md) | `inferred_greeting=ANONYMOUS`, `opted_out_greeting=ANONYMOUS` | Public schema inference opt-out tutorial. |
| [OpenAPI Validation Supersedes Inference](patterns/apis-and-ingress/openapi-supersedes.md) | `supersedes_greeting=ANONYMOUS` | Public schema precedence greeting demo. |
| Local Run and Direct Invoke | `greet=ANONYMOUS` | Local greeting/direct-invoke tutorial. |
| [Rate Limiting / Throttle](patterns/reliability/rate-limiting-throttle.md) | `rate_limit=ANONYMOUS` | In-process token bucket tutorial, not distributed quota enforcement. |
| [Cold Start Mitigation](patterns/runtime-and-ops/cold-start-mitigation.md) | `cold_start_demo=ANONYMOUS` | Public cold-start measurement tutorial. |
| [Observability Tracing](patterns/runtime-and-ops/observability-tracing.md) | `trace_demo=ANONYMOUS` | Public trace-context tutorial; no paid backend. |

### Authentication demonstration

| Recipe | HTTP routes | Note |
|---|---|---|
| [EasyAuth Claims Extraction](patterns/apis-and-ingress/auth-easyauth-claims.md) | `auth_admin=ANONYMOUS`, `auth_me=ANONYMOUS` | Binding deliberately anonymous; trusted EasyAuth ingress supplies identity. |
| [JWT Bearer Validation](patterns/apis-and-ingress/auth-jwt-validation.md) | `auth_profile=ANONYMOUS`, `auth_protected=ANONYMOUS` | Handlers verify JWTs rather than function keys. |
| [Multi-Tenant Auth](patterns/apis-and-ingress/auth-multitenant.md) | `auth_data=ANONYMOUS` | Handler JWT/tenant allowlist demonstrates tenant authorization. |
| [HTTP Auth Levels](patterns/apis-and-ingress/http-auth-levels.md) | `admin_endpoint=ADMIN`, `protected_endpoint=FUNCTION`, `public_endpoint=ANONYMOUS` | Contrasts anonymous, function and admin bindings deliberately. |

### Edge authentication demonstration

| Recipe | HTTP routes | Note |
|---|---|---|
| [APIM Function Backend](patterns/apis-and-ingress/apim-function-backend.md) | `get_catalog_item=ANONYMOUS`, `health=ANONYMOUS` | Public health and APIM backend example; restrict direct backend ingress in production. |

### Public documentation routes

| Recipe | HTTP routes | Note |
|---|---|---|
| scaffold_walkthrough_app | `health=ANONYMOUS`, `receive_webhook=FUNCTION`, `openapi_json=ANONYMOUS`, `openapi_yaml=ANONYMOUS`, `swagger_ui=ANONYMOUS` | Anonymous health/docs; webhook keeps FUNCTION protection. |

### Public webhook with own verification

| Recipe | HTTP routes | Note |
|---|---|---|
| [Webhook GitHub](patterns/apis-and-ingress/webhook-github.md) | `github_webhook=ANONYMOUS` | Public webhook validates HMAC-SHA256 signatures. |

### Public health

| Recipe | HTTP routes | Note |
|---|---|---|
| [Doctor Diagnostics Endpoint](patterns/runtime-and-ops/doctor-diagnostics-endpoint.md) | `get_diagnostics=FUNCTION`, `get_diagnostics_summary=FUNCTION`, `get_health=ANONYMOUS` | Lightweight health is anonymous; diagnostics/summary inherit FUNCTION. |

### Protected (function key)

| Recipe | HTTP routes | Note |
|---|---|---|
| [LangGraph Agent](patterns/ai-and-agents/langgraph-agent.md) | `adapter-routes=FUNCTION`, `invoke_agent=FUNCTION` | Adapter and custom invocation require function keys. |
| [Langgraph Tool Use](patterns/ai-and-agents/langgraph-tool-use.md) | `adapter-routes=FUNCTION`, `invoke_tool_agent=FUNCTION` | Tool adapter and invocation require function keys. |
| [MCP Server Example](patterns/ai-and-agents/mcp-server-example.md) | `mcp=FUNCTION` | Function-key MCP endpoint; calculator eval is separately tracked in #426. |
| [Personal LangGraph Agent](patterns/ai-and-agents/personal-langgraph-agent.md) | `adapter-routes=FUNCTION` | Adapter requires FUNCTION; its library-provided lightweight health route is intentionally public. |
| [CQRS Read Projection](patterns/data-and-pipelines/cqrs-read-projection.md) | `create_order=FUNCTION`, `get_order_projection=FUNCTION` | Order write/read projection requires function key. |
| [DB Input and Output Bindings](patterns/data-and-pipelines/db-input-output.md) | `create_item=FUNCTION`, `list_items=FUNCTION` | Database read/write endpoints require function key. |
| [SQLAlchemy REST Pagination](patterns/data-and-pipelines/sqlalchemy-rest-pagination.md) | `create_item=FUNCTION`, `list_items=FUNCTION` | Paginated database API requires function key. |
| [Service Bus DLQ Replay](patterns/messaging-and-pubsub/servicebus-dlq-replay.md) | `inspect_dead_letter_queue=FUNCTION`, `replay_dead_letter_queue=FUNCTION` | Dead-letter inspection/replay requires function key. |
| [Blueprint Modular App](patterns/runtime-and-ops/blueprint-modular-app.md) | `get_health=FUNCTION`, `create_user_route=FUNCTION`, `get_user_route=FUNCTION`, `list_users_route=FUNCTION` | Blueprint health/users inherit FUNCTION default. |
| [Output Binding vs SDK](patterns/runtime-and-ops/output-binding-vs-sdk.md) | `enqueue_via_binding=FUNCTION`, `enqueue_via_sdk=FUNCTION` | Both queue submission routes inherit FUNCTION. |
| [Secretless Key Vault](patterns/security-and-tenancy/secretless-keyvault.md) | `secretless_keyvault=FUNCTION` | Secretless configuration demonstration requires function key. |
| [Tenant Isolation](patterns/security-and-tenancy/tenant-isolation.md) | `query_tenant_invoices=FUNCTION` | Tenant database query requires function key plus handler tenant resolution. |

### No HTTP route

| Recipe | HTTP routes | Note |
|---|---|---|
| [Blob CSV to Table](patterns/blob-and-file-triggers/blob-csv-to-table.md) | none | Blob ingestion trigger; no declared HTTP route. |
| [Blob Event Grid Trigger](patterns/blob-and-file-triggers/blob-eventgrid-trigger.md) | none | Blob Event Grid trigger; no declared HTTP route. |
| [Blob Thumbnail Generator](patterns/blob-and-file-triggers/blob-thumbnail-generator.md) | none | Blob thumbnail trigger; no declared HTTP route. |
| [Blob Upload Processor](patterns/blob-and-file-triggers/blob-upload-processor.md) | none | Blob upload trigger; no declared HTTP route. |
| [Change Feed Processor](patterns/data-and-pipelines/change-feed-processor.md) | none | Cosmos change feed trigger; no HTTP route. |
| [ETL Enrichment](patterns/data-and-pipelines/etl-enrichment.md) | none | ETL ingestion trigger; no HTTP route. |
| [File Processing Pipeline](patterns/data-and-pipelines/file-processing-pipeline.md) | none | File processing trigger; no HTTP route. |
| [Event Grid Event Router](patterns/messaging-and-pubsub/eventgrid-event-router.md) | none | Event Grid trigger; no declared HTTP route. |
| [Queue Consumer](patterns/messaging-and-pubsub/queue-consumer.md) | none | Queue trigger; no HTTP route. |
| [Service Bus Sessions](patterns/messaging-and-pubsub/servicebus-sessions.md) | none | Service Bus session trigger; no HTTP route. |
| [Service Bus Topic Fan-out](patterns/messaging-and-pubsub/servicebus-topic-fanout.md) | none | Service Bus topic triggers; no HTTP route. |
| [Service Bus Worker](patterns/messaging-and-pubsub/servicebus-worker.md) | none | Service Bus trigger; no HTTP route. |
| [Poison Message Handling](patterns/reliability/poison-message-handling.md) | none | Queue/poison triggers; no HTTP route. |
| [Retry and Idempotency](patterns/reliability/retry-and-idempotency.md) | none | Queue retry trigger; no HTTP route. |
| [Concurrency Tuning](patterns/runtime-and-ops/concurrency-tuning.md) | none | Queue concurrency trigger; no HTTP route. |
| [host.json Tuning](patterns/runtime-and-ops/host-json-tuning.md) | none | Timer tuning trigger; no HTTP route. |
| [Queue Scheduled Dispatch](patterns/scheduled-and-background/queue-scheduled-dispatch.md) | none | Scheduled dispatch trigger; no HTTP route. |
| [Timer Cron Job](patterns/scheduled-and-background/timer-cron-job.md) | none | Timer trigger; no HTTP route. |
| [Managed Identity Service Bus](patterns/security-and-tenancy/managed-identity-servicebus.md) | none | Identity-backed Service Bus trigger; no HTTP route. |
| [Managed Identity Storage](patterns/security-and-tenancy/managed-identity-storage.md) | none | Identity-backed storage trigger; no HTTP route. |
| [Event Hub Batch Window](patterns/streams-and-telemetry/eventhub-batch-window.md) | none | Event Hub batch trigger; no HTTP route. |
| [Event Hub Checkpoint Replay](patterns/streams-and-telemetry/eventhub-checkpoint-replay.md) | none | Event Hub replay trigger; no HTTP route. |
| [Event Hub Consumer](patterns/streams-and-telemetry/eventhub-consumer.md) | none | Event Hub trigger; no HTTP route. |
