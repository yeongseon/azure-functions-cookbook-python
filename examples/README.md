# Examples

`azure-functions-python-cookbook` includes runnable Azure Functions projects
that match each recipe in `recipes/`. Every project is a self-contained
function app ready for `func start`.

## HTTP

| Example | Description |
| --- | --- |
| `examples/http/hello_http_minimal` | Smallest possible HTTP trigger |
| `examples/http/http_routing_query_body` | Route params, query strings, JSON body, status codes |
| `examples/http/http_auth_levels` | Anonymous, Function, and Admin auth levels |
| `examples/http/webhook_github` | GitHub webhook with HMAC-SHA256 verification |

## Timer

| Example | Description |
| --- | --- |
| `examples/timer/timer_cron_job` | NCRONTAB scheduled job with catch-up |

## Queue

| Example | Description |
| --- | --- |
| `examples/queue/queue_producer` | HTTP trigger with Queue output binding |
| `examples/queue/queue_consumer` | Queue trigger message processing |

## Blob

| Example | Description |
| --- | --- |
| `examples/blob/blob_upload_processor` | Polling-based blob trigger |
| `examples/blob/blob_eventgrid_trigger` | Event Grid-based blob trigger |

## Service Bus

| Example | Description |
| --- | --- |
| `examples/servicebus/servicebus_worker` | Service Bus queue trigger |

## Event Hub

| Example | Description |
| --- | --- |
| `examples/eventhub/eventhub_consumer` | Event Hub stream processing |

## Cosmos DB

| Example | Description |
| --- | --- |
| `examples/cosmosdb/change_feed_processor` | Cosmos DB change feed trigger |

## Patterns

| Example | Description |
| --- | --- |
| `examples/recipes/blueprint_modular_app` | Modular function app with Blueprints |
| `examples/recipes/retry_and_idempotency` | Retry policies and idempotency patterns |
| `examples/recipes/output_binding_vs_sdk` | Binding vs SDK client comparison |
| `examples/recipes/managed_identity_storage` | Identity-based Storage connection |
| `examples/recipes/managed_identity_servicebus` | Identity-based Service Bus connection |
| `examples/recipes/host_json_tuning` | host.json configuration patterns |
| `examples/recipes/concurrency_tuning` | Dynamic concurrency |

## Durable Functions

| Example | Description |
| --- | --- |
| `examples/durable/durable_hello_sequence` | Activity chaining pattern |
| `examples/durable/durable_fan_out_fan_in` | Parallel activity execution |
| `examples/durable/durable_human_interaction` | External events with timeout |
| `examples/durable/durable_entity_counter` | Durable entity state management |
| `examples/durable/durable_retry_pattern` | Activity retry with RetryOptions |
| `examples/durable/durable_determinism_gotchas` | Orchestrator determinism rules |
| `examples/durable/durable_unit_testing` | Mock-based orchestrator testing |

## AI

| Example | Description |
| --- | --- |
| `examples/ai/mcp_server_example` | MCP server on Azure Functions |

## Local Development

| Example | Description |
| --- | --- |
| `examples/local_run_and_direct_invoke` | func start vs direct Python invocation |

Each example corresponds to a recipe under `recipes/`.

## Run Any Example

```bash
cd examples/http/hello_http_minimal
pip install -r requirements.txt
func start
```
