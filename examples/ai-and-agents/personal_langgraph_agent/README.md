# Personal LangGraph Agent

This runnable recipe executes the real `LangGraphApp` route, a compiled model → tool →
model graph, and per-thread checkpoints. The checked-in settings use a deterministic,
state-aware fake model; the graph and adapter are never faked.

## Run

```bash
uv venv
uv pip install --python .venv/bin/python -r requirements.txt
cp local.settings.json.example local.settings.json
func start
```

Invoke `POST /api/graphs/personal_agent/invoke`:

```json
{
  "input": {"messages": [{"role": "human", "content": "What is planned for Project Atlas?"}]},
  "config": {"configurable": {"thread_id": "demo-thread"}}
}
```

Reuse `demo-thread` for a follow-up; another ID has separate state. Thread IDs separate
checkpoints, not authenticated users.

## Customize

- Edit `app/services/notes.py` to replace the labelled, read-only sample data with an
  authorized API. Keep tools harmless and read-only.
- Edit `SYSTEM_PROMPT` in `app/services/graph.py`.
- If the tool name changes, update `PERSONAL_AGENT_FAKE_TOOL_NAME`; startup fails with a
  useful mismatch error rather than hiding stale fake behavior.

## Azure OpenAI

Set `AGENT_MODEL_MODE=azure_openai`, `AZURE_OPENAI_ENDPOINT`, and
`AZURE_OPENAI_DEPLOYMENT`. For local key auth set `AZURE_OPENAI_API_KEY`. For production,
prefer `AZURE_OPENAI_USE_ENTRA_ID=true` and grant the Function identity **Cognitive Services
OpenAI User**. Missing real-mode settings are listed by name before routes are served; the
app never downgrades to fake mode.

## Persistent Blob memory

The default `AGENT_MEMORY_MODE=memory` uses process-local `InMemorySaver`. To preserve the
same graph and tools across restarts, run Azurite and set:

```text
AGENT_MEMORY_MODE=blob
AZURE_STORAGE_CONNECTION_STRING=UseDevelopmentStorage=true
LANGGRAPH_AUTO_CREATE_STORAGE=true
AZFUNC_LANGGRAPH_LOCK_BACKEND=distributed
```

Blob mode uses the adapter's `AzureBlobCheckpointSaver` and
`AzureBlobLeaseThreadLock`. The lock serializes same-thread writes across instances, but it
does not promise exactly-once tool effects. This recipe's tool is read-only. Protect the
storage account, apply retention, and remove test containers after use.

The opt-in lane `AZURITE_CONNECTION_STRING=... hatch run pytest -m e2e
tests/test_personal_langgraph_agent.py --no-cov` recreates the app/checkpointer and proves
state survives. It skips only when Azurite is unavailable.

## Safety and operations

The graph permits at most two tool rounds per request and applies model/tool timeouts.
These limits are application-owned and cannot be raised by request configuration. The
adapter's `LoggingRunObserver` records only correlation, graph, timing, lock, and outcome
fields—not messages, tool arguments, checkpoint data, or credentials. Deployed routes use
Function authentication; keep function keys out of browsers and logs. Azure OpenAI and
Storage incur usage costs; delete test resources when finished.
