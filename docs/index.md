# Azure Functions Python Cookbook

The Azure Functions Python Cookbook is a pattern catalog for the Python v2 programming model. It is designed for engineers who need implementation-ready guidance, not just feature summaries. Each recipe captures a complete path from trigger design to production hardening.

## What This Repository Provides

- Recipe-first documentation for HTTP APIs, webhooks, queue workers, and timer jobs.
- Python v2 decorator examples built around `func.FunctionApp()`.
- Practical validation patterns using `pydantic.BaseModel`.
- Architecture notes that explain operational tradeoffs, not only syntax.

## Quick Start

The example below is a runnable minimal HTTP function using the v2 model. Put this in `function_app.py` in a standard Azure Functions Python app.

```python
import json

import azure.functions as func
from pydantic import BaseModel


class HelloRequest(BaseModel):
    name: str


class HelloResponse(BaseModel):
    message: str


app = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)


@app.route(route="hello", methods=["POST"])
def hello(req: func.HttpRequest) -> func.HttpResponse:
    try:
        payload = HelloRequest.model_validate_json(req.get_body())
    except Exception:
        return func.HttpResponse("Invalid JSON body", status_code=400)

    response = HelloResponse(message=f"Hello, {payload.name}")
    return func.HttpResponse(
        response.model_dump_json(),
        mimetype="application/json",
        status_code=200,
    )
```

Run locally:

1. Install dependencies with `pip install -r requirements.txt`.
2. Start the host with `func start`.
3. Send a request to `http://localhost:7071/api/hello`.

You can test the endpoint with a short Python script:

```python
import json
import urllib.request

import azure.functions as func
from pydantic import BaseModel


class TestRequest(BaseModel):
    name: str


payload = TestRequest(name="cookbook-user").model_dump_json().encode("utf-8")
request = urllib.request.Request(
    url="http://localhost:7071/api/hello",
    data=payload,
    method="POST",
    headers={"Content-Type": "application/json"},
)

with urllib.request.urlopen(request, timeout=30) as response:
    body = response.read().decode("utf-8")
    print(json.loads(body))
```

## Recipe Navigation

- Read the full catalog in `docs/recipes.md`.
- Start with `recipes/http-api-basic.md` for foundational HTTP patterns.
- Move to `recipes/http-api-openapi.md` when API contracts and docs matter.
- Use `recipes/github-webhook.md` for signed external event ingestion.
- Use `recipes/queue-worker.md` for asynchronous workload isolation.
- Use `recipes/timer-job.md` for periodic workflows.

## Ecosystem Projects

- `azure-functions-scaffold`: project generation from known patterns.
- `azure-functions-validation`: request and payload validation helpers.
- `azure-functions-openapi`: OpenAPI generation for function routes.
- `azure-functions-logging`: structured logs for operations and diagnostics.
- `azure-functions-doctor`: local environment and configuration checks.

## Documentation Standards

This cookbook keeps examples explicit and production-oriented:

- Prefer typed request and response models.
- Use deterministic trigger code and clear status codes.
- Keep operational concerns visible: retries, idempotency, monitoring, and security.
- Align every recipe with runnable Python v2 code paths.
