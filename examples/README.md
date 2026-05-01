# Examples

Runnable Azure Functions projects that match each pattern in `docs/patterns/`.
Every project is a self-contained function app ready for `func start`.

## APIs & Ingress

| Example | Description |
| --- | --- |
| `apis-and-ingress/hello_http_minimal` | Smallest possible HTTP trigger |
| `apis-and-ingress/http_routing_query_body` | Route params, query strings, JSON body, status codes |
| `apis-and-ingress/http_auth_levels` | Anonymous, Function, and Admin auth levels |
| `apis-and-ingress/webhook_github` | GitHub webhook with HMAC-SHA256 verification |
| `apis-and-ingress/auth_easyauth` | EasyAuth principal extraction with role-based access control |
| `apis-and-ingress/auth_jwt_validation` | JWT Bearer token validation with claim-based access control |
| `apis-and-ingress/auth_multitenant` | Multi-tenant access control with tenant allowlist |
| `apis-and-ingress/bff_facade_api` | BFF facade pattern for backend-for-frontend |
| `apis-and-ingress/full_stack_crud_api` | Full-stack CRUD with azure-functions-db-python toolkit |
| `apis-and-ingress/apim_function_backend` | Azure API Management backend function |

## Async APIs & Jobs

| Example | Description |
| --- | --- |
| `async-apis-and-jobs/async_http_polling` | HTTP 202 accepted with status polling |
| `async-apis-and-jobs/queue_backed_job` | Queue-backed background job processing |
| `async-apis-and-jobs/callback_completion` | Callback-based async completion |

## Messaging & Pub/Sub

| Example | Description |
| --- | --- |
| `messaging-and-pubsub/queue_producer` | HTTP trigger with Queue output binding |
| `messaging-and-pubsub/queue_consumer` | Queue trigger message processing |
| `messaging-and-pubsub/servicebus_worker` | Service Bus queue trigger |
| `messaging-and-pubsub/eventgrid_router` | Event Grid event routing |
| `messaging-and-pubsub/servicebus_topic_fanout` | Service Bus topic fan-out |
| `messaging-and-pubsub/servicebus_sessions` | Service Bus ordered sessions |
| `messaging-and-pubsub/servicebus_dlq_replay` | Service Bus dead-letter replay |
| `messaging-and-pubsub/eventgrid_domain_events` | Event Grid domain events |
| `messaging-and-pubsub/claim_check_pattern` | Claim-check pattern for large payloads |

## Streams & Telemetry

| Example | Description |
| --- | --- |
| `streams-and-telemetry/eventhub_consumer` | Event Hub stream processing |
| `streams-and-telemetry/eventhub_batch_window` | Event Hub batch windowing |
| `streams-and-telemetry/eventhub_checkpoint_replay` | Event Hub checkpoint replay |

## Blob & File Triggers

| Example | Description |
| --- | --- |
| `blob-and-file-triggers/blob_upload_processor` | Polling-based blob trigger |
| `blob-and-file-triggers/blob_eventgrid_trigger` | Event Grid-based blob trigger |
| `blob-and-file-triggers/blob_csv_to_table` | CSV blob to table pipeline |
| `blob-and-file-triggers/blob_thumbnail_generator` | Image thumbnail generation on upload |

## Scheduled & Background

| Example | Description |
| --- | --- |
| `scheduled-and-background/timer_cron_job` | NCRONTAB scheduled job with catch-up |
| `scheduled-and-background/durable_timer_reminder` | Durable timer-based reminder |
| `scheduled-and-background/queue_scheduled_dispatch` | Queue-backed scheduled dispatch |

## Orchestration & Workflows

| Example | Description |
| --- | --- |
| `orchestration-and-workflows/durable_hello_sequence` | Activity chaining pattern |
| `orchestration-and-workflows/durable_fan_out_fan_in` | Parallel activity execution |
| `orchestration-and-workflows/durable_human_interaction` | External events with timeout |
| `orchestration-and-workflows/durable_entity_counter` | Durable entity state management |
| `orchestration-and-workflows/durable_retry_pattern` | Activity retry with RetryOptions |
| `orchestration-and-workflows/durable_determinism_gotchas` | Orchestrator determinism rules |
| `orchestration-and-workflows/durable_unit_testing` | Mock-based orchestrator testing |
| `orchestration-and-workflows/durable_singleton_monitor` | Singleton monitor pattern |
| `orchestration-and-workflows/async_job_lifecycle` | Async job lifecycle management |
| `orchestration-and-workflows/saga_compensation` | Saga compensation pattern |
| `orchestration-and-workflows/sub_orchestration` | Sub-orchestration pattern |

## Reliability

| Example | Description |
| --- | --- |
| `reliability/retry_and_idempotency` | Retry policies and idempotency patterns |
| `reliability/circuit_breaker` | Circuit breaker pattern |
| `reliability/outbox_pattern` | Transactional outbox pattern |
| `reliability/poison_message_handling` | Poison message dead-letter handling |
| `reliability/rate_limiting` | Rate limiting pattern |

## Security & Tenancy

| Example | Description |
| --- | --- |
| `security-and-tenancy/managed_identity_storage` | Identity-based Storage connection |
| `security-and-tenancy/managed_identity_servicebus` | Identity-based Service Bus connection |
| `security-and-tenancy/secretless_keyvault` | Secretless Key Vault integration |
| `security-and-tenancy/tenant_isolation` | Multi-tenant data isolation |

## Runtime & Ops

| Example | Description |
| --- | --- |
| `runtime-and-ops/blueprint_modular_app` | Modular function app with Blueprints |
| `runtime-and-ops/output_binding_vs_sdk` | Binding vs SDK client comparison |
| `runtime-and-ops/host_json_tuning` | host.json configuration patterns |
| `runtime-and-ops/concurrency_tuning` | Dynamic concurrency |
| `runtime-and-ops/cold_start_mitigation` | Cold start mitigation techniques |
| `runtime-and-ops/observability_tracing` | OpenTelemetry tracing and observability |

## Data & Pipelines

| Example | Description |
| --- | --- |
| `data-and-pipelines/change_feed_processor` | Cosmos DB change feed trigger |
| `data-and-pipelines/db_input_output` | Database CRUD with azure-functions-db-python |
| `data-and-pipelines/file_processing_pipeline` | Blob-triggered file pipeline |
| `data-and-pipelines/cqrs_read_projection` | CQRS read-side projection |
| `data-and-pipelines/sqlalchemy_rest_pagination` | SQLAlchemy REST with pagination |
| `data-and-pipelines/etl_enrichment` | ETL enrichment pipeline |

## Realtime

| Example | Description |
| --- | --- |
| `realtime/websocket_proxy` | WebSocket proxy pattern |

## AI & Agents

| Example | Description |
| --- | --- |
| `ai-and-agents/mcp_server_example` | MCP server on Azure Functions |
| `ai-and-agents/langgraph_agent` | LangGraph agent with azure-functions-langgraph-python |
| `ai-and-agents/rag_knowledge_api` | RAG API with Azure AI Search and OpenAI |
| `ai-and-agents/langgraph_rag_agent` | LangGraph RAG agent with knowledge retrieval |
| `ai-and-agents/openai_direct_chat` | Direct Azure OpenAI chat endpoint |
| `ai-and-agents/durable_ai_pipeline` | Durable Functions AI processing pipeline |
| `ai-and-agents/streaming_ai_response` | Server-sent events streaming AI response |
| `ai-and-agents/ai_image_generation` | DALL-E 3 image generation endpoint |
| `ai-and-agents/embedding_vector_search` | Embedding and vector search with AI Search |

## Guides

| Example | Description |
| --- | --- |
| `guides/local_run_and_direct_invoke` | func start vs direct Python invocation |

## Run Any Example

```bash
cd examples/apis-and-ingress/hello_http_minimal
pip install -e .
func start
```

Each example corresponds to a pattern page under `docs/patterns/` or `docs/guides/`.
