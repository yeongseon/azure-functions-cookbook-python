# Azure-Native AI & Agent Learning Path

This guided path traces the progression of building AI assistants and autonomous agents on Azure Functions using Python v2. It teaches how to choose the right execution model—from direct HTTP chat completions to stateful LangGraph agents, event-driven message consumers, and Durable human-in-the-loop workflows.

---

## Architectural Progression

Rather than treating AI applications as generic web servers or building monolithic showcases, compose focused, production-proven patterns across seven distinct stages:

```mermaid
flowchart TD
    S1["1. Direct Chat<br><i>HTTP Trigger</i><br>Single-turn completion"]
    --> S2["2. LangGraph Agent<br><i>LangGraphApp Route</i><br>Multi-step tool routing"]
    --> S3["3. Persistent Memory<br><i>Blob Checkpoints</i><br>Restart-safe conversations"]
    --> S4["4. Grounded RAG<br><i>Azure AI Search</i><br>Vector + semantic retrieval"]
    --> S5["5. Event-Driven Agent<br><i>Service Bus Trigger</i><br>Asynchronous decoupling"]
    --> S6["6. Durable Workflow<br><i>Durable Functions</i><br>Human approval & timeout"]
    --> S7["7. Production Hardening<br><i>APIM + Managed ID</i><br>Edge security & tracing"]

    style S1 fill:#e1f5fe,stroke:#0288d1
    style S2 fill:#e8eaf6,stroke:#3f51b5
    style S3 fill:#ede7f6,stroke:#673ab7
    style S4 fill:#f3e5f5,stroke:#8e24aa
    style S5 fill:#e0f2f1,stroke:#00897b
    style S6 fill:#fbe9e7,stroke:#d84315
    style S7 fill:#eceff1,stroke:#455a64
```

---

## The 7 Progression Stages

### Stage 1: Synchronous Model Invocation (HTTP Trigger + Azure OpenAI)

* **Trigger**: HTTP (`@app.route`)
* **Underlying Service**: Azure OpenAI Service (`chat/completions`)
* **When appropriate**: Low-latency single-turn prompts, text summarization, or classification where the client waits interactively and responses return in under 5 seconds.
* **Execution shape**:
  ```python
  @app.route(route="chat", methods=["POST"])
  def chat(req: func.HttpRequest) -> func.HttpResponse:
      prompt = req.get_json().get("prompt")
      response = client.chat.completions.create(model="gpt-4o-mini", messages=[{"role": "user", "content": prompt}])
      return func.HttpResponse(response.choices[0].message.content)
  ```
* **Required for capability**: Azure OpenAI Python client, HTTP trigger.
* **Production upgrades**:
  - Use `DefaultAzureCredential` with Managed Identity instead of static API keys.
  - Stream tokens via Server-Sent Events (SSE) to lower time-to-first-token (TTFT).
* **Reference recipes**:
  - [Azure OpenAI Direct Chat](openai-direct-chat.md) — clean client baseline.
  - [Streaming AI Response](streaming-ai-response.md) — chunked token streaming.

---

### Stage 2: Graph-Driven Routing & Tools (`LangGraphApp`)

* **Trigger**: HTTP via `azure-functions-langgraph` (`LangGraphApp`)
* **Underlying Service**: Compiled `StateGraph` + Azure OpenAI
* **When appropriate**: Dynamic reasoning, multi-turn tool calling, or branching workflows where the model decides which tools to invoke before producing an answer.
* **Why this model fits**: `LangGraphApp` mounts the compiled graph directly onto the Azure Functions routing infrastructure (`POST /api/graphs/{name}/invoke`), providing automatic request parsing, context injection, and error formatting.
* **Execution boundary**: Application logic, prompt engineering, and tool functions remain owned by your recipe; `azure-functions-langgraph` acts solely as the runtime deployment adapter.
* **Required for capability**: Compiled LangGraph graph, `azure-functions-langgraph`.
* **Production upgrades**: Enforce explicit tool timeouts, validate tool input arguments using Pydantic, and keep tools strictly read-only or idempotent.
* **Reference recipes**:
  - [LangGraph Agent](langgraph-agent.md) — compiled graph deployment.
  - [LangGraph Tool Use](langgraph-tool-use.md) — typed tool-calling pattern.

---

### Stage 3: Per-Thread Memory & Persistent Blob Checkpoints

* **Trigger**: HTTP (`LangGraphApp`) + Azure Blob Storage
* **Underlying Service**: Azure Blob Storage Container (`checkpoints`)
* **When appropriate**: Multi-turn conversational assistants where users refer to previous context across sessions, surviving Function App restarts and cold starts.
* **State distinction**:
  - *In-Memory Saver*: Fast, zero-dependency local dev; checkpoints are lost when the function worker process recycles.
  - *Blob Checkpointer*: Durable state stored as blobs keyed by `thread_id`; survives horizontal scaling and worker restarts.
* **Security boundary (Critical)**:
  > [!WARNING]
  > A `thread_id` is an execution state partition key at `config.configurable.thread_id`. **It is not an authenticated user identity or security boundary.**
  > Never allow clients to supply an arbitrary `thread_id` without verifying that the authenticated caller owns that conversation thread. Always enforce caller identity before invoking the graph.
* **Required for capability**: Azure Blob Storage container, checkpointer package.
* **Production upgrades**: Use identity-based storage connections (`AzureWebJobsStorage__blobServiceUri`) and configure blob lifecycle policies to expire stale threads.
* **Reference recipe**:
  - [Personal LangGraph Agent](personal-langgraph-agent.md) — complete single-user personal notes assistant with memory.

---

### Stage 4: Grounded Knowledge Retrieval (Azure AI Search RAG)

* **Trigger**: HTTP (`LangGraphApp` or search endpoint)
* **Underlying Service**: Azure AI Search + Azure OpenAI Embeddings
* **When appropriate**: Answering questions against private internal documents, manuals, or catalogs without fine-tuning models.
* **Architecture flow**:
  1. Input query is converted to a vector embedding using `text-embedding-3-small`.
  2. Query is submitted to Azure AI Search for hybrid vector + semantic BM25 retrieval.
  3. Top matching passages are injected into the agent's prompt context.
* **Why use the SDK instead of a binding**: Azure AI Search lacks a native Python v2 binding; calling `azure.search.documents` via the official SDK provides full access to vector query filters, semantic rerankers, and score thresholds.
* **Required for capability**: Azure AI Search index, embedding model deployment.
* **Production upgrades**: Limit retrieved chunk count and payload size to avoid blowing model context windows; sanitize document metadata to prevent prompt injection.
* **Reference recipes**:
  - [RAG Knowledge API](rag-knowledge-api.md) — vector search knowledge endpoint.
  - [Embedding Vector Search](embedding-vector-search.md) — direct embedding generation and query.
  - [LangGraph RAG Agent](langgraph-rag-agent.md) — agent graph with search tool integration.

---

### Stage 5: Event-Driven Agent Invocation (Service Bus Decoupling)

* **Trigger**: Service Bus Queue or Topic Trigger (`@app.service_bus_queue_trigger`)
* **Underlying Service**: Azure Service Bus
* **When appropriate**:
  - Agent execution takes longer than 15–20 seconds (e.g. multi-step tool loops or web searches).
  - Upstream webhooks or backend events trigger agent tasks asynchronously.
  - Requests must not fail due to transient HTTP connection timeouts or gateway limits.
* **Execution shape**:
  1. Client sends a request to an HTTP ingest endpoint; endpoint validates and enqueues a work message onto Service Bus, immediately returning `202 Accepted` with a correlation ID.
  2. A Service Bus-triggered function consumes the message, invokes the compiled LangGraph agent, and writes results to a database or notifies a webhook.
* **Why this model fits**:
  - Prevents caller timeouts while preserving at-least-once processing guarantees.
  - Provides automatic retry and dead-letter queue (DLQ) isolation for poison inputs.
  - Service Bus Sessions (`is_sessions_enabled=True`) can enforce strict FIFO ordering per `session_id` (e.g., ensuring messages for the same user or ticket process sequentially).
* **Required for capability**: Service Bus namespace, Queue/Topic trigger handler.
* **Production upgrades**: Configure `maxDeliveryCount` and monitor dead-letter queues; ensure agent tool side effects are idempotent.
* **Reference recipes**:
  - [Service Bus Worker](../messaging-and-pubsub/servicebus-worker.md) — reliable queue processing.
  - [Service Bus Sessions](../messaging-and-pubsub/servicebus-sessions.md) — ordered per-session execution.
  - [Service Bus DLQ Replay](../messaging-and-pubsub/servicebus-dlq-replay.md) — dead-letter message triage.

---

### Stage 6: Long-Running Workflows & Human Approval (Durable Functions)

* **Trigger**: Durable Orchestrator Trigger (`@bp.orchestration_trigger`)
* **Underlying Service**: Durable Task Framework + Storage Provider
* **When appropriate**:
  - Multi-step AI pipelines requiring human-in-the-loop review (e.g., approving a high-value tool action or draft before publication).
  - Long delays (waiting hours or days for user input via email or portal).
  - Parallel agent task fan-out and aggregation (e.g., analyzing 10 documents concurrently).
* **Orchestration rules**:
  > [!IMPORTANT]
  > **Durable Orchestrator Determinism**: Orchestrator functions must be deterministic because they replay history to reconstruct state.
  > **Never call LLMs, make network requests, or invoke tools directly inside orchestrator code.** Always wrap agent executions and external calls in **Durable Activity functions** (`@bp.activity_trigger`).
* **Execution flow**:
  ```
  HTTP Client ──► Starter (202 Accepted)
                     │
                     ▼
             Durable Orchestrator
                     │
                     ├─► Activity: Prepare Agent Prompt & Context
                     │
                     ├─► Activity: Run LangGraph Agent Round 1
                     │
                     ├─► waitForExternalEvent("ManagerApproval", timeout=24h)
                     │         │
                     │         ▼ (Approval received or timeout)
                     │
                     └─► Activity: Execute Final Tool Action & Publish
  ```
* **Required for capability**: `azure-functions-durable`, Durable Task Hub.
* **Reference recipes**:
  - [Durable AI Pipeline](durable-ai-pipeline.md) — multi-activity LLM orchestration.
  - [Durable Human Interaction](../orchestration-and-workflows/durable-human-interaction.md) — human approval pattern.
  - [Async Job Lifecycle](../orchestration-and-workflows/async-job-lifecycle.md) — status query and lifecycle management.

---

### Stage 7: Production Hardening (Edge, Identity & Observability)

Layer enterprise operational controls onto the working agent app:

```
[ Incoming Client Request ]
             │
             ▼
[ 1. API Management (APIM) ] ─────────► Ingress rate-limiting, token usage quotas, CORS
             │
             ▼
[ 2. EasyAuth / JWT Bearer ] ────────► Authenticate caller principal & tenant ID
             │
             ▼
[ 3. Function App (Agent Graph) ]
             │
             ├─► Managed Identity ────► Keyless auth to Azure OpenAI, Storage, Search
             ├─► Key Vault References ─► Third-party API keys (@Microsoft.KeyVault)
             └─► App Insights Tracing ─► Trace ID propagation & model latency telemetry
```

1. **Edge Gateway (APIM)**: Protect functions against abuse with rate limiting, subscription keys, and IP allowlists ([APIM Function Backend](../apis-and-ingress/apim-function-backend.md)).
2. **Caller Authentication**: Extract caller identity from EasyAuth headers (`X-MS-CLIENT-PRINCIPAL-NAME`) or validate bearer JWTs before allowing access to conversation checkpoints ([EasyAuth Claims Extraction](../apis-and-ingress/auth-easyauth-claims.md), [JWT Bearer Validation](../apis-and-ingress/auth-jwt-validation.md)).
3. **Keyless Resource Identity**: Connect to Azure OpenAI, Storage, and Service Bus via Managed Identity (`DefaultAzureCredential`), eliminating credential leaks ([Managed Identity Storage](../security-and-tenancy/managed-identity-storage.md)).
4. **Secretless Key Vault**: Store external third-party tool tokens in Azure Key Vault and reference them directly in application settings ([Secretless Key Vault](../security-and-tenancy/secretless-keyvault.md)).
5. **Observability & Distributed Tracing**: Correlate frontend requests with backend function invocations and model tokens using Application Insights ([Observability Tracing](../runtime-and-ops/observability-tracing.md)). Avoid logging full prompt payloads containing PII.

---

## When to Transition Between Stages

| Current Stage | Move to Next Stage When... | Next Trigger / Model |
| --- | --- | --- |
| **1. Direct Chat** | You need multi-step reasoning, external tool execution, or dynamic branching. | `LangGraphApp` route ([Stage 2](#stage-2-graph-driven-routing-tools-langgraphapp)) |
| **2. LangGraph Agent** | Conversations span multiple turns and must survive worker restarts or scaling. | Blob checkpointer ([Stage 3](#stage-3-per-thread-memory-persistent-blob-checkpoints)) |
| **3. Memory / Checkpoints** | The agent requires external corporate knowledge, manuals, or document search. | Azure AI Search RAG ([Stage 4](#stage-4-grounded-knowledge-retrieval-azure-ai-search-rag)) |
| **4. Grounded RAG** | Agent execution exceeds 15s or requests originate from asynchronous events. | Service Bus queue ([Stage 5](#stage-5-event-driven-agent-invocation-service-bus-decoupling)) |
| **5. Event-Driven Agent** | Operations require human sign-off, multi-day waits, or complex compensation logic. | Durable Functions ([Stage 6](#stage-6-long-running-workflows-human-approval-durable-functions)) |
| **6. Durable Workflows** | Moving into production multi-tenant environments with strict compliance. | Production hardening ([Stage 7](#stage-7-production-hardening-edge-identity-observability)) |

---

## Related Foundation Documents

- [Pattern Chooser](../../foundations/pattern-chooser.md) — visual decision flow for all 14 categories.
- [Execution Model](../../foundations/execution-model.md) — Python v2 programming model and Blueprints.
- [Delivery Guarantees](../../foundations/delivery-guarantees.md) — at-least-once message processing rules.
