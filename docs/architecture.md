# Architecture

## Overview

The cookbook is a documentation-focused repository that standardizes how Azure Functions Python v2 patterns are explained. The architecture is intentionally simple: recipe source documents define the contract, published docs curate the reader journey, and runnable examples demonstrate execution behavior.

## Layer Model

The architecture has three layers with clear responsibilities:

- `recipes/`: canonical implementation narratives and trigger-specific guidance.
- `docs/`: reader-friendly pages that aggregate patterns and provide onboarding.
- `examples/`: runnable projects that validate recipe claims in code.

This separation allows recipe depth to grow without making onboarding pages noisy.

## Repository Structure Example

Use a structure that preserves one recipe-to-example mapping and keeps documentation discoverable.

```python
from pathlib import Path

import azure.functions as func
from pydantic import BaseModel


class RepositoryLayout(BaseModel):
    root: str
    docs: list[str]
    recipes: list[str]
    examples: list[str]


layout = RepositoryLayout(
    root=str(Path(".")),
    docs=["index.md", "recipes.md", "architecture.md", "contributing.md"],
    recipes=[
        "http-api-basic.md",
        "http-api-openapi.md",
        "github-webhook.md",
        "queue-worker.md",
        "timer-job.md",
    ],
    examples=["http-api-basic/", "http-api-openapi/", "github-webhook/", "queue-worker/", "timer-job/"],
)

app = func.FunctionApp()
_ = app
print(layout.model_dump())
```

## Function App Composition

A recipe should present code in composition units that can be split later with Blueprints, while still starting from a single `FunctionApp` entry point.

```python
import azure.functions as func
from pydantic import BaseModel


class AppMetadata(BaseModel):
    service: str
    version: str


metadata = AppMetadata(service="cookbook-sample", version="1.0.0")
app = func.FunctionApp(http_auth_level=func.AuthLevel.FUNCTION)


@app.route(route="health", methods=["GET"])
def health(_: func.HttpRequest) -> func.HttpResponse:
    return func.HttpResponse(metadata.model_dump_json(), mimetype="application/json", status_code=200)
```

## Module Layout Example

A production recipe can scale from one file to multiple modules while preserving the v2 decorator model.

```python
from dataclasses import dataclass

import azure.functions as func
from pydantic import BaseModel


class HttpContract(BaseModel):
    route: str
    methods: list[str]


@dataclass(slots=True)
class ModulePlan:
    entrypoint: str
    modules: list[str]
    contract: HttpContract


plan = ModulePlan(
    entrypoint="function_app.py",
    modules=["handlers/http.py", "handlers/queue.py", "handlers/timer.py"],
    contract=HttpContract(route="jobs", methods=["POST"]),
)

app = func.FunctionApp()
_ = (app, plan)
```

## Trigger Isolation Pattern

Each trigger should have one focused function and one payload model. This keeps validation local and limits blast radius during changes.

```python
import json

import azure.functions as func
from pydantic import BaseModel


class QueuePayload(BaseModel):
    task_id: str
    kind: str


app = func.FunctionApp()


@app.queue_trigger(arg_name="msg", queue_name="jobs", connection="AzureWebJobsStorage")
def process_job(msg: func.QueueMessage) -> None:
    payload = QueuePayload.model_validate(json.loads(msg.get_body().decode("utf-8")))
    print(payload.task_id, payload.kind)
```

```python
import datetime

import azure.functions as func
from pydantic import BaseModel


class TimerPayload(BaseModel):
    name: str
    fired_at: str


app = func.FunctionApp()


@app.timer_trigger(schedule="0 */15 * * * *", arg_name="timer", run_on_startup=False, use_monitor=True)
def run_timer(timer: func.TimerRequest) -> None:
    _ = timer
    payload = TimerPayload(name="refresh-cache", fired_at=datetime.datetime.now(datetime.UTC).isoformat())
    print(payload.model_dump_json())
```

## Operational Contracts

Recipe architecture should always expose operational assumptions in code examples:

- Validation path: parse request payloads with explicit models.
- Failure path: return deterministic status codes or raise for retry semantics.
- Idempotency path: include a stable operation key for webhook and queue flows.
- Observability path: include log fields that make retries and latency traceable.

## Evolution Strategy

As recipes expand, keep compatibility by evolving contracts rather than replacing them:

- Add fields as optional first, then enforce in a later version.
- Keep existing route names stable unless migration guidance is documented.
- Add new trigger recipes as additive pages to avoid breaking reader workflows.
- Keep code examples executable and parseable with Python 3.10+ syntax.
