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
   - Runnable or near-runnable sample projects
   - Organized by category: apis-and-ingress, scheduled-and-background, blob-and-file-triggers, async-apis-and-jobs, messaging-and-pubsub, streams-and-telemetry, data-and-pipelines, orchestration-and-workflows, reliability, security-and-tenancy, runtime-and-ops, realtime, ai-and-agents, guides
3. `docs/`
   - Published documentation and navigation structure
   - Concept guides for cross-cutting topics
4. `tests/`
   - Smoke tests that import and validate every example

## Recipe Categories

| Category | Count | Description |
| --- | --- | --- |
| APIs & Ingress | 9 | HTTP-first APIs, auth, webhooks, and edge request shaping |
| Scheduled & Background | 1 | Scheduled execution with NCRONTAB |
| Blob & File Triggers | 2 | Polling and Event Grid blob/file processing |
| Async APIs & Jobs | 4 | Long-running request workflows and async completion patterns |
| Messaging & Pub/Sub | 8 | Queue, Service Bus, and Event Grid messaging workloads |
| Streams & Telemetry | 3 | Event Hub ingestion and replay patterns |
| Data & Pipelines | 6 | Change feed, ETL, CQRS, and persistence-oriented flows |
| Orchestration & Workflows | 9 | Durable orchestration, entities, sagas, and testing |
| Reliability | 5 | Retry, outbox, poison handling, and throttling patterns |
| Security & Tenancy | 4 | Identity-based connections, secrets, and tenant isolation |
| Runtime & Ops | 6 | Blueprints, bindings vs SDKs, tuning, tracing, and cold start |
| Realtime | 1 | SignalR-based notifications |
| AI & Agents | 9 | MCP, RAG, agent, chat, and multimodal AI workloads |

## Future Extension Points

- Recipe search and tagging
- Scaffold command mapping
- Static gallery experience
- Automated validation of recipe examples
- Azurite-based integration test suite
