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

1. `recipes/`
   - Source recipe documents (28 recipes)
   - Architecture, use cases, pitfalls, and scaffold guidance
2. `examples/`
   - Runnable or near-runnable sample projects
   - Organized by category: http, timer, queue, blob, servicebus, eventhub, cosmosdb, recipes, durable, ai
3. `docs/`
   - Published documentation and navigation structure
   - Concept guides for cross-cutting topics
4. `tests/`
   - Smoke tests that import and validate every example

## Recipe Categories

| Category | Count | Description |
| --- | --- | --- |
| HTTP | 4 | Request/response patterns from minimal to webhook |
| Timer | 1 | Scheduled execution with NCRONTAB |
| Queue | 2 | Producer/consumer with Storage Queue |
| Blob | 2 | Polling and Event Grid blob triggers |
| Service Bus | 1 | Enterprise message queue processing |
| Event Hub | 1 | High-throughput stream processing |
| Cosmos DB | 1 | Change feed trigger |
| Patterns | 7 | Cross-cutting: blueprints, retry, identity, tuning |
| Durable | 7 | Orchestration, entities, testing |
| AI | 1 | MCP server integration |
| Local Dev | 1 | Development workflow |

## Future Extension Points

- Recipe search and tagging
- Scaffold command mapping
- Static gallery experience
- Automated validation of recipe examples
- Azurite-based integration test suite
