# Durable Agent Approval

An agent request that becomes a **durable workflow** instead of a long HTTP call: an HTTP starter
returns `202`, a Durable orchestrator runs a LangGraph draft in an activity, waits for a human
approval event or a timeout, and only then runs a final, idempotent completion activity. Status,
approval and cancel are narrow HTTP routes. Full explanation:
[pattern page](https://yeongseon.dev/azure-functions-python/cookbook/patterns/ai-and-agents/durable-agent-approval/).

Related recipes (generic explanations live there, not here):
[Durable Human Interaction](../../orchestration-and-workflows/durable_human_interaction/),
[Durable AI Pipeline](../durable_ai_pipeline/),
[Async Job Lifecycle](../../orchestration-and-workflows/async_job_lifecycle/).

## Flow

```text
POST /api/agent-runs                    -> 202 {run_id, status_url, approval_url, cancel_url}
  orchestrator: run_agent_draft (activity, LangGraph, retried, read-only)
  orchestrator: wait ApprovalDecision event  OR  timer   (task_any)
GET  /api/agent-runs/{id}               -> running | awaiting_approval (+draft) | completed | rejected
                                           | timed_out | failed | cancelled
POST /api/agent-runs/{id}/approval      -> {"approved": true|false}; 409 unless awaiting approval
  approved only -> publish_approved_result (activity, idempotent per run_id)
POST /api/agent-runs/{id}/cancel        -> 202 cancel_requested (terminates the orchestration)
```

Timeout, rejection, malformed or missing decisions all end **without** the final action.

## Bounds

All in `app/core/limits.py`: prompt 2,000 chars, request body 8 KiB, draft 2,000 chars, model output
256 tokens, model timeout 30 s with no hidden SDK retries, graph recursion limit 6, draft retries
3 attempts, approval timeout 60 s to 5 days (default 24 h; Python Durable timers are limited to six
days). Durable is not unlimited execution: activities are still subject to the Function timeout
(`functionTimeout` in `host.json`).

## Run the tests (offline)

```bash
pip install -e ".[dev]"
pytest
```

No Azure, network, Azurite, Core Tools or Durable host. Tests cover: the orchestrator driven by a
fake context, the **real** `azure-functions-durable` replay engine driven from synthetic history,
the HTTP routes with a fake Durable client, and the activities with fake models and sinks.

## Run on a host (not verified by this repository)

```bash
cp local.settings.json.example local.settings.json
# start Azurite, then:
func start
curl -X POST localhost:7071/api/agent-runs -H 'x-functions-key: <key>' -d '{"prompt":"hello"}'
```

`AGENT_MODEL_MODE=fake` (default) needs no credentials. `azure_openai` uses
`DefaultAzureCredential`; set `AZURE_OPENAI_ENDPOINT` and grant the identity
*Cognitive Services OpenAI User*. The publish sink is an in-memory demo; replace it with a store
whose write is atomic per key before relying on idempotency across instances.
