# Recipes

This page maps each cookbook recipe to a concrete Azure Functions Python v2 implementation pattern. Every example uses decorator-based bindings with `func.FunctionApp()` and focuses on production concerns: validation, explicit response contracts, idempotency, and clear trigger semantics.

## Recipe Catalog

| Recipe | Trigger | Primary Use Case |
|--------|---------|------------------|
| HTTP API Basic | HTTP | CRUD-style endpoints with lightweight validation |
| HTTP API with OpenAPI | HTTP | Documented APIs with generated contracts |
| GitHub Webhook Receiver | HTTP | Signed event ingestion and event dispatch |
| Queue Worker | Queue | Asynchronous background processing |
| Timer Scheduled Job | Timer | Scheduled maintenance and synchronization |

## HTTP API Basic

Use this pattern for simple REST endpoints when you need predictable request handling and typed payload validation without introducing extra framework layers.

```python
import json

import azure.functions as func
from pydantic import BaseModel


class ItemCreateRequest(BaseModel):
    name: str
    quantity: int


app = func.FunctionApp(http_auth_level=func.AuthLevel.FUNCTION)


@app.route(route="items", methods=["POST"])
def create_item(req: func.HttpRequest) -> func.HttpResponse:
    try:
        payload = ItemCreateRequest.model_validate_json(req.get_body())
    except Exception:
        return func.HttpResponse("Invalid request body", status_code=400)

    response = {"id": "item-001", "name": payload.name, "quantity": payload.quantity}
    return func.HttpResponse(json.dumps(response), mimetype="application/json", status_code=201)
```

```python
import json

import azure.functions as func
from pydantic import BaseModel


class ItemResponse(BaseModel):
    id: str
    name: str
    quantity: int


app = func.FunctionApp(http_auth_level=func.AuthLevel.FUNCTION)


@app.route(route="items/{item_id}", methods=["GET"])
def get_item(req: func.HttpRequest) -> func.HttpResponse:
    item_id = req.route_params.get("item_id", "")
    result = ItemResponse(id=item_id, name="sample", quantity=1)
    return func.HttpResponse(result.model_dump_json(), mimetype="application/json", status_code=200)
```

Reference: [recipes/http-api-basic.md](https://github.com/yeongseonchoe/azure-functions-python-cookbook/blob/main/recipes/http-api-basic.md)

## HTTP API with OpenAPI

Use this pattern when your API requires a browsable contract and stable schemas for consumers. Keep schema models near handler code so docs evolve with behavior.

```python
import azure.functions as func
from azure_functions_openapi import OpenAPI
from pydantic import BaseModel


class ProductResponse(BaseModel):
    id: str
    name: str
    price: float


app = func.FunctionApp(http_auth_level=func.AuthLevel.FUNCTION)
openapi = OpenAPI(app=app)


@app.route(route="products/{product_id}", methods=["GET"])
@openapi.doc(
    summary="Get a product",
    params={"product_id": "Product identifier"},
    responses={200: {"description": "Product details"}},
)
def get_product(req: func.HttpRequest) -> func.HttpResponse:
    product_id = req.route_params.get("product_id", "")
    payload = ProductResponse(id=product_id, name="starter", price=9.99)
    return func.HttpResponse(payload.model_dump_json(), mimetype="application/json", status_code=200)
```

```python
import azure.functions as func
from azure_functions_openapi import OpenAPI
from pydantic import BaseModel


class ProductCreateRequest(BaseModel):
    name: str
    price: float


app = func.FunctionApp(http_auth_level=func.AuthLevel.FUNCTION)
openapi = OpenAPI(app=app)


@app.route(route="products", methods=["POST"])
@openapi.doc(
    summary="Create a product",
    request_body={"description": "Product payload"},
    responses={201: {"description": "Created"}},
)
def create_product(req: func.HttpRequest) -> func.HttpResponse:
    payload = ProductCreateRequest.model_validate_json(req.get_body())
    body = {"id": "generated-id", "name": payload.name, "price": payload.price}
    return func.HttpResponse(str(body).replace("'", '"'), mimetype="application/json", status_code=201)
```

Reference: [recipes/http-api-openapi.md](https://github.com/yeongseonchoe/azure-functions-python-cookbook/blob/main/recipes/http-api-openapi.md)

## GitHub Webhook Receiver

Use this pattern for event-driven automation from GitHub. The core requirements are signature validation, event routing, and safe repeated processing.

```python
import hashlib
import hmac
import json
import os

import azure.functions as func
from pydantic import BaseModel


class PullRequestEvent(BaseModel):
    action: str
    number: int


app = func.FunctionApp(http_auth_level=func.AuthLevel.FUNCTION)


def is_valid_signature(payload: bytes, header_signature: str | None) -> bool:
    if not header_signature:
        return False
    secret = os.getenv("GITHUB_WEBHOOK_SECRET", "").encode("utf-8")
    digest = hmac.new(secret, payload, hashlib.sha256).hexdigest()
    expected = f"sha256={digest}"
    return hmac.compare_digest(expected, header_signature)


@app.route(route="github/webhook", methods=["POST"])
def github_webhook(req: func.HttpRequest) -> func.HttpResponse:
    payload = req.get_body()
    signature = req.headers.get("X-Hub-Signature-256")
    if not is_valid_signature(payload, signature):
        return func.HttpResponse("Invalid signature", status_code=401)

    event_name = req.headers.get("X-GitHub-Event", "unknown")
    body = json.loads(payload.decode("utf-8"))
    if event_name == "pull_request":
        event = PullRequestEvent.model_validate(body)
        return func.HttpResponse(f"Handled pull request #{event.number}", status_code=200)

    return func.HttpResponse("Event ignored", status_code=202)
```

```python
import azure.functions as func
from pydantic import BaseModel


class DeliveryRecord(BaseModel):
    delivery_id: str
    event: str


app = func.FunctionApp(http_auth_level=func.AuthLevel.FUNCTION)


def record_delivery(record: DeliveryRecord) -> None:
    _ = record


@app.route(route="github/webhook/ingest", methods=["POST"])
def ingest_webhook(req: func.HttpRequest) -> func.HttpResponse:
    delivery_id = req.headers.get("X-GitHub-Delivery", "")
    event = req.headers.get("X-GitHub-Event", "")
    record_delivery(DeliveryRecord(delivery_id=delivery_id, event=event))
    return func.HttpResponse("Accepted", status_code=202)
```

Reference: [recipes/github-webhook.md](https://github.com/yeongseonchoe/azure-functions-python-cookbook/blob/main/recipes/github-webhook.md)

## Queue Worker

Use this pattern to decouple user-facing requests from expensive background work. Messages should carry minimal, validated payloads and handlers should be idempotent.

```python
import json
import logging

import azure.functions as func
from pydantic import BaseModel


class WorkItem(BaseModel):
    job_id: str
    operation: str


app = func.FunctionApp()


@app.queue_trigger(arg_name="msg", queue_name="work-items", connection="AzureWebJobsStorage")
def process_queue_message(msg: func.QueueMessage) -> None:
    raw = msg.get_body().decode("utf-8")
    payload = WorkItem.model_validate(json.loads(raw))
    logging.info("Processing job_id=%s operation=%s", payload.job_id, payload.operation)
```

```python
import azure.functions as func
from pydantic import BaseModel


class RetryPolicy(BaseModel):
    max_attempts: int
    delay_seconds: int


app = func.FunctionApp()


def should_retry(dequeue_count: int, policy: RetryPolicy) -> bool:
    return dequeue_count < policy.max_attempts


@app.queue_trigger(arg_name="msg", queue_name="work-items", connection="AzureWebJobsStorage")
def queue_with_retry(msg: func.QueueMessage) -> None:
    policy = RetryPolicy(max_attempts=5, delay_seconds=30)
    dequeue_count = int(msg.dequeue_count)
    if not should_retry(dequeue_count, policy):
        raise RuntimeError("Exceeded retry policy")
```

Reference: [recipes/queue-worker.md](https://github.com/yeongseonchoe/azure-functions-python-cookbook/blob/main/recipes/queue-worker.md)

## Timer Scheduled Job

Use this pattern for periodic workloads such as cleanup, synchronization, and reconciliation. Keep timer handlers deterministic and safe to re-run.

```python
import datetime
import logging

import azure.functions as func
from pydantic import BaseModel


class JobContext(BaseModel):
    job_name: str
    started_at_utc: str


app = func.FunctionApp()


@app.timer_trigger(schedule="0 */10 * * * *", arg_name="timer", run_on_startup=False, use_monitor=True)
def run_scheduled_job(timer: func.TimerRequest) -> None:
    if timer.past_due:
        logging.warning("Timer is past due")
    context = JobContext(
        job_name="sync-catalog",
        started_at_utc=datetime.datetime.now(datetime.UTC).isoformat(),
    )
    logging.info("Running %s at %s", context.job_name, context.started_at_utc)
```

```python
import azure.functions as func
from pydantic import BaseModel


class MaintenanceTask(BaseModel):
    name: str
    enabled: bool


app = func.FunctionApp()


def execute(task: MaintenanceTask) -> None:
    if not task.enabled:
        return


@app.timer_trigger(schedule="0 0 2 * * *", arg_name="timer", run_on_startup=False, use_monitor=True)
def nightly_maintenance(timer: func.TimerRequest) -> None:
    _ = timer
    execute(MaintenanceTask(name="cleanup-expired-records", enabled=True))
```

Reference: [recipes/timer-job.md](https://github.com/yeongseonchoe/azure-functions-python-cookbook/blob/main/recipes/timer-job.md)

## Recipe Contract

Every recipe should keep the same section contract so readers can move quickly between patterns:

- Overview
- When to Use
- Architecture
- Project Structure
- Run Locally
- Production Considerations
- Scaffold Starter

For a new recipe, start from `recipes/_template.md`, add at least one runnable Python v2 example, and keep models explicit with `BaseModel` when payload validation is part of the flow.
