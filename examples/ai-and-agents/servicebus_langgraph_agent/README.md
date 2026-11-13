# Service Bus LangGraph Agent

A Service Bus **queue-triggered** Function that runs a compiled LangGraph graph through
`azure-functions-langgraph`'s `LangGraphApp.register_service_bus(...)`. A message is one
work item; there is no HTTP request to hold open. The checked-in settings use a
deterministic fake model; the graph, the adapter and the generated Service Bus handler are
never faked.

Verification level: **unit** (offline tests call the real handler with synthetic messages).
No Functions host run, Service Bus namespace or Azure deployment has verified this recipe.

## Message contract

```json
{"request_id": "req-1001", "question": "Where is order A-1001?", "conversation_id": "conv-7"}
```

`request_id` and `question` are required; `conversation_id` is optional. Invalid bodies raise
before the graph runs (names fields, never echoes values).

| Mode | Thread ID used for checkpoints |
| --- | --- |
| Queue (`SERVICEBUS_SESSIONS=false`, default) | `sb:conversation:<conversation_id>`, or `sb:request:<request_id>` when absent |
| Session queue (`SERVICEBUS_SESSIONS=true`) | the message `session_id` (required) |

A thread ID selects a checkpoint partition. It is **not** authorization: who may send is
decided by Service Bus RBAC on the queue.

## Run offline

```bash
uv venv
uv pip install --python .venv/bin/python -e ".[dev]"
.venv/bin/python -m pytest
```

The tests build real `azure.functions` Service Bus messages and call the registered handler.

## Run locally with Core Tools

Needs [Azure Functions Core Tools](https://learn.microsoft.com/azure/azure-functions/functions-run-local),
[Azurite](https://learn.microsoft.com/azure/storage/common/storage-use-azurite) for
`AzureWebJobsStorage`, and a Service Bus namespace with a queue (the Service Bus emulator is
not covered here).

```bash
cp local.settings.json.example local.settings.json
# set ServiceBusConnection and, if needed, SERVICEBUS_QUEUE_NAME
func start
```

Send `{"request_id": "req-1", "question": "Where is order A-1001?"}` to the queue. For session
mode create the queue with sessions enabled, set `SERVICEBUS_SESSIONS=true` and set a
`session_id` on each message.

## Azure OpenAI (live mode)

Set `AGENT_MODEL_MODE=azure_openai`, `AZURE_OPENAI_ENDPOINT`, `AZURE_OPENAI_DEPLOYMENT` and
either `AZURE_OPENAI_API_KEY` (local) or `AZURE_OPENAI_USE_ENTRA_ID=true` (grant the Function
identity **Cognitive Services OpenAI User**). Missing settings fail at startup; there is no
fallback to fake mode. Live calls were not run for this recipe.

## Production path

- **Identity**: use `ServiceBusConnection__fullyQualifiedNamespace` with the Function's
  managed identity instead of a connection string. See
  [Managed Identity Service Bus](../../security-and-tenancy/managed_identity_servicebus/).
- **Delivery is at-least-once.** The same message can run again. Message IDs derive from
  `request_id`, so a redelivery rewrites its own turn instead of appending a duplicate, and the
  sink is an upsert keyed by `request_id`. The sample tool is read-only.
- **Retries and dead-letter** belong to Service Bus and the Functions host. An exception
  (bad body, model timeout, sink failure, thread contention) abandons the message; after
  `MaxDeliveryCount` Service Bus dead-letters it. See [Service Bus Worker](../../messaging-and-pubsub/servicebus_worker/),
  [DLQ Replay](../../messaging-and-pubsub/servicebus_dlq_replay/) and
  [Poison Message Handling](../../reliability/poison_message_handling/).
- **Lock budget**: `lock_timeout` + graph run + sink must fit inside the message lock, the host's
  `maxAutoLockRenewalDuration` and `functionTimeout` (`host.json` sets 5 minutes each).
- **Checkpoints** here are `InMemorySaver`: per instance, lost on restart. Use a durable
  checkpointer and a distributed thread lock before scaling out; see
  [Personal LangGraph Agent](../personal_langgraph_agent/).
- **Telemetry** carries `request_id`, Service Bus `message_id`, thread ID, delivery count and
  answer length. The question, the answer and the body are not logged. See
  [Observability Tracing](../../runtime-and-ops/observability_tracing/).

Full walkthrough: [pattern page](../../../docs/patterns/ai-and-agents/servicebus-langgraph-agent.md).
