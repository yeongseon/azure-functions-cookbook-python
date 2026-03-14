# Product Requirements

## Product Goal

Help developers discover, understand, and start real Azure Functions Python solutions through curated recipes.

## Target User

- Developers who are new to Azure Functions Python
- Developers who need a proven implementation pattern quickly
- Teams looking for practical serverless reference architectures

## Core Value

Each recipe should answer three questions:

1. What should I build for this scenario?
2. How should the architecture look?
3. How do I start from a working baseline?

## Scope

- A clear repository README
- 28 curated recipes covering all major Azure Functions patterns
- A reusable recipe template
- Published documentation with hierarchical navigation
- Standard repository tooling, testing, and release workflows

## Non-Goals

- A dedicated cookbook CLI in the first release
- Deep automation across the ecosystem in the first release
- Large numbers of low-quality sample projects

## Example-First Design

### Philosophy

The cookbook IS an example-first project. Every recipe exists to answer one question:
"How do I build this with Azure Functions Python?" If a recipe cannot take a developer
from zero to a running function in under five minutes, it has failed its purpose.

### Quick Start (Hello World)

The Hello HTTP Minimal recipe is the cookbook's Hello World:

```python
import azure.functions as func

app = func.FunctionApp()


@app.route(route="hello", methods=["GET"])
def hello(req: func.HttpRequest) -> func.HttpResponse:
    name = req.params.get("name", "World")
    return func.HttpResponse(f"Hello, {name}!")
```

Each recipe follows this progression:

1. What should I build for this scenario?
2. How should the architecture look?
3. Here is the working code — copy, run, extend.

### Why Examples Matter

1. **Lower entry barrier.** A cookbook that requires reading external docs before the first
   recipe is usable has already lost. Working code comes first, explanations second.
2. **AI agent discoverability.** Tools like GitHub Copilot, Cursor, and Claude Code recommend
   libraries based on README, PRD, and example content. Curated recipes make the cookbook
   visible to AI agents searching for Azure Functions Python patterns.
3. **Cookbook role.** This repository is entirely a cookbook — `recipes/` and `examples/` are
   the core deliverables. The bar for runnable, well-documented examples is higher here
   than in any other repository in the ecosystem.
4. **Proven approach.** FastAPI, LangChain, SQLAlchemy, and Pandas all achieved early adoption
   through extensive, copy-paste-friendly examples. The cookbook follows the same model.

### Recipes Inventory

#### HTTP

| Recipe | Example | Pattern |
|---|---|---|
| Hello HTTP Minimal | `examples/http/hello_http_minimal` | Smallest possible HTTP trigger |
| HTTP Routing, Query, and Body | `examples/http/http_routing_query_body` | Route params, query strings, JSON body |
| HTTP Auth Levels | `examples/http/http_auth_levels` | Anonymous, Function, Admin auth |
| GitHub Webhook | `examples/http/webhook_github` | HMAC-SHA256 webhook receiver |

#### Timer

| Recipe | Example | Pattern |
|---|---|---|
| Timer Cron Job | `examples/timer/timer_cron_job` | NCRONTAB scheduled execution |

#### Queue

| Recipe | Example | Pattern |
|---|---|---|
| Queue Producer | `examples/queue/queue_producer` | HTTP trigger with Queue output binding |
| Queue Consumer | `examples/queue/queue_consumer` | Queue trigger message processing |

#### Blob

| Recipe | Example | Pattern |
|---|---|---|
| Blob Upload Processor | `examples/blob/blob_upload_processor` | Polling-based blob trigger |
| Blob Event Grid Trigger | `examples/blob/blob_eventgrid_trigger` | Event Grid-based blob trigger |

#### Service Bus

| Recipe | Example | Pattern |
|---|---|---|
| Service Bus Worker | `examples/servicebus/servicebus_worker` | Service Bus queue trigger |

#### Event Hub

| Recipe | Example | Pattern |
|---|---|---|
| Event Hub Consumer | `examples/eventhub/eventhub_consumer` | Event Hub stream processing |

#### Cosmos DB

| Recipe | Example | Pattern |
|---|---|---|
| Change Feed Processor | `examples/cosmosdb/change_feed_processor` | Change feed trigger |

#### Patterns

| Recipe | Example | Pattern |
|---|---|---|
| Blueprint Modular App | `examples/recipes/blueprint_modular_app` | Modular app with Blueprints |
| Retry and Idempotency | `examples/recipes/retry_and_idempotency` | Runtime retry + deduplication |
| Output Binding vs SDK | `examples/recipes/output_binding_vs_sdk` | Binding vs SDK client comparison |
| Managed Identity (Storage) | `examples/recipes/managed_identity_storage` | Identity-based Storage connection |
| Managed Identity (Service Bus) | `examples/recipes/managed_identity_servicebus` | Identity-based Service Bus connection |
| host.json Tuning | `examples/recipes/host_json_tuning` | Configuration patterns |
| Concurrency Tuning | `examples/recipes/concurrency_tuning` | Dynamic concurrency |

#### Durable Functions

| Recipe | Example | Pattern |
|---|---|---|
| Hello Sequence | `examples/durable/durable_hello_sequence` | Activity chaining |
| Fan-Out / Fan-In | `examples/durable/durable_fan_out_fan_in` | Parallel execution |
| Human Interaction | `examples/durable/durable_human_interaction` | External events + timeout |
| Entity Counter | `examples/durable/durable_entity_counter` | Durable entity state |
| Retry Pattern | `examples/durable/durable_retry_pattern` | Activity retry with RetryOptions |
| Determinism Gotchas | `examples/durable/durable_determinism_gotchas` | Orchestrator rules |
| Unit Testing | `examples/durable/durable_unit_testing` | Mock-based testing |

#### AI

| Recipe | Example | Pattern |
|---|---|---|
| MCP Server | `examples/ai/mcp_server_example` | MCP server on Azure Functions |

#### Local Development

| Recipe | Example | Pattern |
|---|---|---|
| Local Run and Direct Invoke | `examples/local_run_and_direct_invoke` | func start vs direct invocation |

All recipes follow the `recipes/_template.md` format. New recipes must include runnable
code that works out of the box without external dependencies beyond the recipe's own requirements.
