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

## MVP Scope

- A clear repository README
- Five curated recipes
- A reusable recipe template
- Published documentation with navigation
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

The HTTP API Basic recipe is the cookbook's Hello World:

```python
import azure.functions as func

app = func.FunctionApp()


@app.function_name(name="hello")
@app.route(route="hello", methods=["GET"])
def hello(req: func.HttpRequest) -> func.HttpResponse:
    return func.HttpResponse("Hello, World!")
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

| Recipe | File | Pattern |
|---|---|---|
| HTTP API Basic | `recipes/http-api-basic.md` | Minimal REST endpoint |
| HTTP API with OpenAPI | `recipes/http-api-openapi.md` | OpenAPI + Swagger UI integration |
| GitHub Webhook | `recipes/github-webhook.md` | Webhook receiver with signature validation |
| Queue Worker | `recipes/queue-worker.md` | Storage Queue message processing |
| Timer Job | `recipes/timer-job.md` | Scheduled task with NCRONTAB |

All recipes follow the `recipes/_template.md` format. New recipes must include runnable
code that works out of the box without external dependencies beyond the recipe's own requirements.
