# Roadmap

The Azure Functions Python Cookbook is a mission-driven project aimed at providing the most comprehensive, production-ready, and well-tested collection of patterns for Azure Functions development with Python. This roadmap outlines the direction of the project and its current status.

## Current Status

The project has reached **v0.6.0+** with **82 production-ready recipes** covering all major Azure Functions trigger types, Durable Functions orchestration patterns, and cross-cutting concerns like managed identity, retry/idempotency, authentication, and performance tuning. The documentation site is live and auto-deployed via GitHub Pages.

---

## Phase 1: Foundation (COMPLETE)

The primary goal of this phase was to build the infrastructure required to support a long-term, high-quality documentation project.

- Repository structure and organization established using modern Python standards.
- Continuous Integration (CI/CD) with multi-version Python testing (3.11–3.14), CodeQL, SBOM, and security workflows.
- Documentation site architecture using MkDocs Material theme for a modern, searchable experience.
- Recipe template and formal contract definition to ensure all recipes are consistent and complete.
- Internationalization support with translated READMEs for Korean, Japanese, and Chinese audiences.
- Development tooling integration (Ruff, Mypy, Pytest, Bandit, Hatch, pre-commit).

---

## Phase 2: Recipe Content (COMPLETE)

This phase delivered comprehensive recipes across all major Azure Functions trigger types.

- ✅ **82 recipes** written with production-ready content across the current catalog categories.
- ✅ **82 runnable example projects** with `pyproject.toml`, `function_app.py`, and local run instructions.
- ✅ Deep-dive production notes covering performance, scaling, retries, and security.
- ✅ Mermaid architectural diagrams for pattern visualization.
- ✅ All example code passes security and quality checks (lint, type-check, tests).
- ✅ Comprehensive trigger coverage: HTTP, Timer, Queue, Blob, Service Bus, Event Hub, Cosmos DB.
- ✅ Durable Functions coverage: chaining, fan-out/fan-in, human interaction, entities, retry, determinism, testing.
- ✅ Advanced patterns: Blueprint modular apps, managed identity, host.json tuning, concurrency tuning.
- ✅ AI integration: MCP Server recipe and LangGraph agent integration.

---

## Phase 3: Production Depth & Foundational Quality (COMPLETE)

Now that trigger coverage is comprehensive, this phase hardened recipes for production operations.

- ✅ **Authentication & Authorization**: HTTP auth with Entra ID / Easy Auth / JWT patterns.
- ✅ **Observability**: Application Insights integration, structured logging, and distributed tracing.
- ✅ **Advanced Messaging**: Service Bus topics, dead-letter queues, sessions, and replay-safe patterns.
- ✅ **Event Grid & Storage**: Blob event-grid triggers, event routers, and domain events.
- ✅ **End-to-End Validation**: Representative recipe suite and Azurite integration testing.
- ✅ **Foundational Quality**: Repaired replay-safe writes, worker context registration, and local settings preservation.

---

## Phase 4: Azure-Native & Functions-First Evolution (ACTIVE)

Tracked under umbrella issue **[#347](https://github.com/yeongseon/azure-functions-cookbook-python/issues/347)** (*chore(roadmap): make the cookbook Azure-native and Functions-first*).

The problem is discoverability and composition: a learner can find the individual pieces, but the repository must make the Azure-native execution model the primary way to choose and combine them.

### Guiding Principles
1. **Functions-first, not HTTP-first**: Choose the trigger/binding/orchestration model that best fits the workload rather than treating Functions as an HTTP web framework.
2. **Azure-native, not Azure-maximalist**: Prefer Managed Identity/Entra ID, Key Vault references, and Application Insights; avoid adding cloud services purely for diagram complexity.
3. **Composition over duplication**: Reuse existing recipes and link them directly instead of creating monolithic sample apps.
4. **Toolkit packages keep their boundaries**: `azure-functions-langgraph` is a deployment runtime adapter; agent logic lives in application recipes.
5. **Explicit production path with minimal first-run**: Credential-free local baselines with explicit production hardening paths.

### Active Child Issues

- [ ] **[#348: docs(ai): add an Azure-native agent learning path across existing recipes](https://github.com/yeongseon/azure-functions-cookbook-python/issues/348)** (`priority: medium`, `size: M`)
  - Canonical progression from HTTP completion to LangGraph agents, persistent Blob checkpoints, Azure AI Search RAG, event-driven Service Bus invocation, and Durable approval workflows.
- [ ] **[#349: feat(recipes): add an event-driven LangGraph agent with Azure Service Bus](https://github.com/yeongseon/azure-functions-cookbook-python/issues/349)** (`priority: medium`, `size: L`)
  - Integration recipe under `examples/ai-and-agents/` using Service Bus queues/sessions to trigger a compiled LangGraph agent.
- [ ] **[#350: feat(recipes): add a Durable Functions agent workflow with approval and bounded long-running work](https://github.com/yeongseon/azure-functions-cookbook-python/issues/350)** (`priority: medium`, `size: XL`)
  - Runnable Durable orchestrator coordinating model activity execution, external approval events, timeouts, and bounded lifecycle management.
- [ ] **[#351: docs(ai): compose an end-to-end Azure RAG path from Blob events to Azure AI Search and an agent](https://github.com/yeongseon/azure-functions-cookbook-python/issues/351)** (`priority: medium`, `size: M`)
  - Architecture and operational guide composing Blob ingestion, vector indexing, and agent retrieval across existing recipes.
- [ ] **[#352: docs(architecture): add a production Azure Functions reference path for identity, edge, and observability](https://github.com/yeongseon/azure-functions-cookbook-python/issues/352)** (`priority: medium`, `size: M`)
  - Comprehensive reference guide for layering APIM, EasyAuth/JWT, Managed Identity, and telemetry onto any baseline function app.

---

## Phase 5: Tooling & Community Integration (PLANNED)

- [ ] Recipe metadata in machine-readable format for developer tools (`recipes.json`).
- [ ] Scaffold integration: generate projects directly from recipes with `azure-functions-scaffold`.
- [ ] Automated example validation against latest upstream SDK releases.
- [ ] Community recipe intake and scenario request workflows.

---

## Non-Goals

To maintain focus and ensure high quality, we have explicitly defined what this project is not:

- **Not a runtime library**: This is a content-first project. There is no package API to import.
- **Not a replacement for official docs**: This cookbook complements Microsoft documentation with opinionated, production-ready patterns.
- **No legacy support**: We exclusively focus on the Python v2 programming model and Python 3.11+.
- **Quality over quantity**: We focus on high-impact, well-documented patterns rather than exhaustive variations.

---

## How We Prioritize

1. Production-readiness gaps (auth, observability, deployment) before niche triggers.
2. Stability and longevity of the underlying Azure services and Python SDKs.
3. Completeness of the existing collection to ensure we cover the most important use cases.
4. Community demand and common developer friction points.
