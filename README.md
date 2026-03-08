# Azure Functions Python Cookbook

A collection of practical recipes for building real-world Azure Functions with Python.

This repository is the content entry point for the Azure Functions Python ecosystem. It focuses on runnable examples, architecture explanations, and scaffold-ready starters that help developers move from idea to implementation quickly.

## What This Repository Provides

- Practical recipes for common Azure Functions scenarios
- Runnable example projects
- Architecture explanations and production notes
- Scaffold-ready starter guidance for new projects

## Initial Recipe Scope

- HTTP API Basic
- HTTP API with OpenAPI
- GitHub Webhook Receiver
- Queue Worker
- Timer Scheduled Job

## Repository Layout

```text
recipes/
|- _template.md
|- http-api-basic.md
|- http-api-openapi.md
|- github-webhook.md
|- queue-worker.md
`- timer-job.md

examples/
`- README.md

docs/
|- index.md
|- recipes.md
|- architecture.md
`- roadmap.md
```

## Development Setup

```bash
make install
make check-all
make docs
```

## Direction

The cookbook is intentionally content-first. It is not a separate CLI tool yet. The goal is to make recipes discoverable first, and only add deeper CLI integration after the recipe catalog and example quality are stable.
