# Design

## Overview

Azure Functions Python Cookbook is a content-first repository that helps developers discover proven Azure Functions implementation patterns before they commit to a project structure.

## Design Principles

- Start from a developer problem, not from a library feature.
- Keep recipes focused on one use case and one architectural story.
- Pair each recipe with an example that can evolve into a scaffold starter later.
- Preserve independence from the other repositories at the documentation level.

## Information Architecture

The repository is organized into four layers:

1. `docs/patterns/`
   - Source pattern documents
   - Architecture, use cases, pitfalls, and scaffold guidance
2. `examples/`
- Runnable sample projects (82 total)
   - Organized by category: apis-and-ingress, scheduled-and-background, blob-and-file-triggers, async-apis-and-jobs, messaging-and-pubsub, streams-and-telemetry, data-and-pipelines, orchestration-and-workflows, reliability, security-and-tenancy, runtime-and-ops, realtime, ai-and-agents, guides
3. `docs/`
   - Published documentation and navigation structure
   - Concept guides for cross-cutting topics
4. `tests/`
   - Smoke tests that import and validate every example

## Recipe Categories

| Category | Count | Description |
| --- | --- | --- |
| APIs & Ingress | 10 | HTTP-first APIs, auth, webhooks, APIM backend, and edge request shaping |
| Scheduled & Background | 3 | Scheduled execution, timer reminders, and queue-backed dispatch |
| Blob & File Triggers | 4 | Polling and Event Grid blob/file processing, CSV and thumbnail pipelines |
| Async APIs & Jobs | 3 | Long-running request workflows and async completion patterns |
| Messaging & Pub/Sub | 9 | Queue, Service Bus, Event Grid messaging, and claim-check pattern |
| Streams & Telemetry | 3 | Event Hub ingestion and replay patterns |
| Data & Pipelines | 6 | Change feed, ETL, CQRS, and persistence-oriented flows |
| Orchestration & Workflows | 11 | Durable orchestration, entities, sagas, sub-orchestration, and testing |
| Reliability | 5 | Retry, outbox, poison handling, circuit breaker, and throttling patterns |
| Security & Tenancy | 4 | Identity-based connections, secrets, and tenant isolation |
| Runtime & Ops | 6 | Blueprints, bindings vs SDKs, tuning, tracing, and cold start |
| Realtime | 1 | WebSocket proxy |
| AI & Agents | 11 | MCP, RAG, agent, chat, and multimodal AI workloads |
| Guides | 1 | Local development and direct invocation guide |

## Verification Levels

Every `recipe.yaml` declares the highest level that the required jobs in
`.github/workflows/ci-test.yml` back for that recipe. `tests/test_recipes.py` enforces the declared
level against these required automations.

- `docs`: no recipe-local test suite, and not in the `host-smoke` matrix.
- `unit`: the required per-recipe job (`recipe-tests`, `scripts/run_recipe_tests.py`) runs a
  recipe-local `tests/test_*.py` suite.
- `func-host`: the recipe is in the required `host-smoke` matrix, which starts the Functions host.
- `azure`: a required job exercises a deployed Azure resource (none does today).

Optional e2e, toolkit and scheduled checks, and repository-level tests under `tests/` that target one
recipe, do not change the level. Never infer a level from the services a recipe uses.

## Future Extension Points

- Recipe search and tagging
- Scaffold command mapping
- Static gallery experience
- Automated validation of recipe examples
- Azurite-based integration test suite
