# Roadmap

The Azure Functions Python Cookbook is a mission-driven project aimed at providing the most comprehensive, production-ready, and well-tested collection of patterns for Azure Functions development with Python. This roadmap outlines the direction of the project and its current status.

## Current Status

The project has reached **v0.1.2** with **31 production-ready recipes** covering all major Azure Functions trigger types, Durable Functions orchestration patterns, and cross-cutting concerns like managed identity, retry/idempotency, authentication, and performance tuning. The documentation site is live and auto-deployed via GitHub Pages.

## Phase 1: Foundation (COMPLETE)

The primary goal of this phase was to build the infrastructure required to support a long-term, high-quality documentation project.

- Repository structure and organization established using modern Python standards.
- Continuous Integration (CI/CD) with multi-version Python testing (3.10–3.14), CodeQL, SBOM, and security workflows.
- Documentation site architecture using MkDocs Material theme for a modern, searchable experience.
- Recipe template and formal contract definition to ensure all recipes are consistent and complete.
- Internationalization support with translated READMEs for Korean, Japanese, and Chinese audiences.
- Development tooling integration (Ruff, Mypy, Pytest, Bandit, Hatch, pre-commit).

## Phase 2: Recipe Content (COMPLETE)

This phase delivered comprehensive recipes across all major Azure Functions trigger types.

- ✅ **31 recipes** written with production-ready content across 11 categories.
- ✅ **31 runnable example projects** with `pyproject.toml`, `function_app.py`, and local run instructions.
- ✅ Deep-dive production notes covering performance, scaling, retries, and security.
- ✅ Mermaid architectural diagrams for pattern visualization.
- ✅ All example code passes security and quality checks (lint, type-check, tests).
- ✅ Comprehensive trigger coverage: HTTP, Timer, Queue, Blob, Service Bus, Event Hub, Cosmos DB.
- ✅ Durable Functions coverage: chaining, fan-out/fan-in, human interaction, entities, retry, determinism, testing.
- ✅ Advanced patterns: Blueprint modular apps, managed identity, host.json tuning, concurrency tuning.
- ✅ AI integration: MCP Server recipe.

## Phase 3: Production Depth (IN PROGRESS)

Now that trigger coverage is comprehensive, this phase focuses on the recipes that teams need when moving from local development to production.

- [x] **Authentication & Authorization**: HTTP auth with Entra ID / Easy Auth / JWT patterns.
- [ ] **Observability**: Application Insights integration, structured logging, and distributed tracing.
- [ ] **Deployment Recipes**: Deployment slots, app settings management, IaC with Bicep/Terraform.
- [ ] **Advanced Messaging**: Service Bus topics, dead-letter queues, sessions.
- [ ] **Event Grid Custom Events**: Beyond blob triggers — custom event publishing and subscribing.
- [ ] **End-to-end CI validation**: Run representative examples against Azurite in CI (not just import tests).
- [ ] **Per-recipe quick-start improvements**: Prerequisites matrix, required env vars, expected output for every example.

## Phase 4: Discovery & Community (PLANNED)

Make the cookbook easier to find, navigate, and contribute to.

- [ ] Recipe search and tagging system (by trigger, service, difficulty, pattern).
- [ ] "Choose by problem" and "Choose by trigger" landing pages.
- [ ] Issue templates and recipe-request forms for community intake.
- [ ] GitHub Discussions for Q&A and recipe ideas.
- [ ] PR-based documentation previews.
- [ ] SEO improvements (site_url, meta descriptions, social cards).
- [ ] Cross-referencing with official Azure scaffold templates and community resources.

## Phase 5: Tooling Integration (FUTURE)

Deeper integration into the developer workflow.

- [ ] Scaffold integration: generate projects directly from recipes.
- [ ] Recipe metadata in machine-readable format for developer tools.
- [ ] Lightweight CLI for browsing and scaffolding recipes.
- [ ] One-click deployment options for example projects.
- [ ] Automated example validation against latest SDK releases.

## Non-Goals

To maintain focus and ensure high quality, we have explicitly defined what this project is not:

- **Not a runtime library**: This is a content-first project. There is no package API to import.
- **Not a CLI** (yet): Content quality comes before tooling in the current phase.
- **Not a replacement for official docs**: This cookbook complements Microsoft documentation with opinionated, production-ready patterns.
- **No legacy support**: We exclusively focus on the Python v2 programming model and Python 3.10+.
- **Quality over quantity**: We focus on high-impact, well-documented patterns rather than exhaustive variations.

## How We Prioritize

1. Community demand and common pain points reported by developers.
2. Production-readiness gaps (auth, observability, deployment) before niche triggers.
3. Stability and longevity of the underlying Azure services and Python SDKs.
4. Completeness of the existing collection to ensure we cover the most important use cases.

The roadmap is a living document and will be updated as the project evolves and we receive more feedback from the community.
