# Architecture

## Overview

The cookbook is a documentation-focused repository that standardizes how Azure Functions Python v2 patterns are explained. The architecture is intentionally simple: recipe source documents define the contract, published docs curate the reader journey, and runnable examples demonstrate execution behavior.

## Ecosystem Overview

The cookbook is part of a broader three-project ecosystem. Each project has a distinct role, and they are designed to compose together.

```mermaid
graph TD
    DEV(["👨‍💻 Developer"])

    subgraph Ecosystem["Azure Functions Python Ecosystem"]
        CB["📚 azure-functions-python-cookbook\nRecipe catalog & examples"]
        SC["🔧 azure-functions-scaffold\nafs new · afs add"]
        VAL["✅ azure-functions-validation\n@validate_http decorator"]
    end

    PROJ["🗂️ Generated Project\nfunction_app.py\napp/functions/\ntests/"]

    DEV -- "1. learn patterns" --> CB
    CB -- "template reference" --> SC
    DEV -- "2. afs new my-api\n   --template http\n   --with-validation" --> SC
    SC -- "3. scaffold project" --> PROJ
    SC -- "--with-validation" --> VAL
    VAL -- "runtime integration" --> PROJ
    DEV -- "4. func start / publish" --> PROJ
```

### Project Roles

| Project | Role | Key API |
|---------|------|---------|
| **cookbook** | Recipe catalog — shows *what* to build and *why* | `docs/`, `examples/`, `recipes/` |
| **scaffold** | CLI that generates projects from cookbook-aligned templates | `afs new`, `afs add` |
| **validation** | Runtime decorator that enforces HTTP input contracts | `@validate_http` |

### Developer Flow

```mermaid
sequenceDiagram
    participant Dev as Developer
    participant CB as Cookbook
    participant SC as Scaffold CLI
    participant VAL as Validation
    participant AZ as Azure Functions

    Dev->>CB: browse recipes (e.g. HTTP API)
    CB-->>Dev: example code + architecture guidance
    Dev->>SC: afs new my-api --template http --with-validation
    SC-->>Dev: project generated
    Dev->>VAL: apply @validate_http to handlers
    Dev->>AZ: func start  /  func publish
    AZ-->>Dev: function running
```


## Layer Model

The architecture has three layers with clear responsibilities:

- `recipes/`: canonical implementation narratives and trigger-specific guidance.
- `docs/`: reader-friendly pages that aggregate patterns and provide onboarding.
- `examples/`: runnable projects that validate recipe claims in code.

This separation allows recipe depth to grow without making onboarding pages noisy.

## Repository Structure

Each recipe maps to exactly one example. This one-to-one mapping keeps documentation discoverable and validation tractable.

```mermaid
flowchart TD
    subgraph Cookbook["azure-functions-python-cookbook"]
        R["recipes/\n*.md"]
        D["docs/\n*.md"]
        E["examples/\n*/"]
    end

    R -- "1:1 mapping" --> E
    D -- "aggregates" --> R
    E -- "validates claims in" --> R
```

## Function App Composition

Start with a single `FunctionApp` entry point. Split into Blueprints only when modules grow beyond a manageable size.

```mermaid
flowchart LR
    FA["function_app.py\nFunctionApp()"]
    B1["Blueprint\nhttp.py"]
    B2["Blueprint\nqueue.py"]
    B3["Blueprint\ntimer.py"]

    FA -- "register_blueprint" --> B1
    FA -- "register_blueprint" --> B2
    FA -- "register_blueprint" --> B3
```

A minimal single-file app:

```python
import azure.functions as func

app = func.FunctionApp(http_auth_level=func.AuthLevel.FUNCTION)


@app.route(route="health", methods=["GET"])
def health(_: func.HttpRequest) -> func.HttpResponse:
    return func.HttpResponse('{"status": "ok"}', mimetype="application/json", status_code=200)
```

## Module Layout

A production recipe separates trigger wiring, business logic, schemas, and observability.

```mermaid
flowchart TD
    FunctionApp["function_app.py"]

    subgraph app/
        F["functions/\ntrigger handlers"]
        S["services/\nbusiness logic"]
        SC["schemas/\nPydantic models"]
        C["core/\nlogging · config"]
    end

    FunctionApp --> F
    F --> S
    F --> SC
    S --> C
```

## Trigger Isolation Pattern

Each trigger owns one handler and one payload model. Keeps validation local and limits blast radius.

```mermaid
flowchart LR
    QT["Queue Trigger"]
    TT["Timer Trigger"]
    QP["QueuePayload\n(Pydantic)"]
    TP["TimerPayload\n(Pydantic)"]
    PJ["process_job()"]
    RT["run_timer()"]

    QT --> PJ
    TT --> RT
    PJ -- "validates" --> QP
    RT -- "builds" --> TP
```

Queue trigger example:

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

## Reference Production Shapes

These are common deployment topologies for Azure Functions Python apps. They are not prescriptive — choose based on scale, latency, and team complexity.

### Shape A: Single Function App (HTTP + async triggers)

The simplest production shape. One Function App handles HTTP routes and async triggers. Suitable for most teams getting started or running moderate traffic.

```mermaid
graph TD
    Client(["Client / External System"])
    APIM["Azure API Management\n(optional)"]
    FA["Function App\nfunction_app.py"]
    ST["Azure Storage\n(Queue + Blob)"]
    SB["Service Bus\n(optional)"]
    DB["Cosmos DB / SQL\n(optional)"]
    AI["Application Insights"]

    Client --> APIM
    APIM --> FA
    FA -- "queue trigger" --> ST
    FA -- "blob trigger" --> ST
    FA -- "servicebus trigger" --> SB
    FA -- "read / write" --> DB
    FA -- "telemetry" --> AI
```

**When to use**: Single-team apps, event-driven workloads, moderate traffic.

### Shape B: Multi-App with Event Bus

Split functions by domain into separate Function Apps. Use Service Bus or Event Hubs as the event bus between them. Suitable when teams own separate domains or retry/DLQ isolation matters.

```mermaid
graph TD
    Ingest["Ingestion App\nHTTP + Blob triggers"]
    Bus["Service Bus / Event Hubs\n(event bus)"]
    Worker["Worker App\nQueue + SB triggers"]
    Notifier["Notifier App\nTimer + SB triggers"]
    DB["Shared Datastore"]
    AI["Application Insights"]

    Ingest -- "publish" --> Bus
    Bus -- "consume" --> Worker
    Bus -- "consume" --> Notifier
    Worker --> DB
    Notifier --> DB
    Ingest --> AI
    Worker --> AI
    Notifier --> AI
```

**When to move from A → B**: Independent deployability becomes necessary, DLQ isolation per domain is required, or different scaling profiles are needed per domain.

### Shape C: Container Apps + Functions Hybrid

Long-running or compute-heavy logic moves to Container Apps. Azure Functions handles event ingestion and lightweight triggers. Use when cold starts or timeout limits become a constraint.

```mermaid
graph TD
    EH["Event Hubs / Queue"]
    FA["Function App\nevent ingestion"]
    CA["Container Apps\nlong-running workers"]
    FA2["Function App\nresult callbacks"]
    DB["Datastore"]
    AI["Application Insights"]

    EH -- "trigger" --> FA
    FA -- "enqueue job" --> CA
    CA -- "write result" --> DB
    CA -- "callback" --> FA2
    FA2 --> DB
    FA --> AI
    CA --> AI
```

**When to move from B → C**: Functions hit 10-minute timeout limits, workers need persistent connections or stateful streaming, or GPU/memory requirements exceed Function App limits.

### Shape progression summary

```mermaid
flowchart LR
    A["Shape A\nSingle App"] --> B["Shape B\nMulti-App + Event Bus"]
    B --> C["Shape C\nContainer Apps Hybrid"]

    A -. "trigger: team/domain split" .-> B
    B -. "trigger: timeout / memory limits" .-> C
```
