# Event Hub Checkpoint Replay

📖 [Full documentation](https://yeongseon.github.io/azure-functions-cookbook-python/patterns/streams-and-telemetry/eventhub-checkpoint-replay/)

Azure Functions example showing replay-aware Event Hub consumption with offset tracking and idempotent processing.

## Prerequisites

- Python 3.10+
- [Azure Functions Core Tools v4](https://learn.microsoft.com/azure/azure-functions/functions-run-local)
- [Azurite](https://learn.microsoft.com/azure/storage/common/storage-use-azurite) for `AzureWebJobsStorage`
- An Azure Event Hubs namespace with a hub named `telemetry`

## Environment Variables

| Variable | Purpose | Example |
|----------|---------|---------|
| `EventHubConnection` | Event Hub connection string with `EntityPath` | `Endpoint=sb://<namespace>.servicebus.windows.net/;SharedAccessKeyName=<name>;SharedAccessKey=<key>;EntityPath=telemetry` |
| `EVENTHUB_NAME` | Event Hub name used by the trigger | `telemetry` |

Copy `local.settings.json.example` to `local.settings.json` before running locally.

## What It Demonstrates

- `event_hub_message_trigger` bound to `telemetry`
- Logging partition, sequence, and offset metadata for replay analysis
- In-memory offset tracking per partition during local runs
- Idempotent duplicate detection using a partition-aware event ID

## Run Locally

```bash
cd examples/streams-and-telemetry/eventhub_checkpoint_replay
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
cp local.settings.json.example local.settings.json
func start
```

## Example Event

```json
{
  "device_id": "sensor-17",
  "reading": 23.4,
  "metric": "temperature"
}
```

## Expected Output

- Logs include `partition_id`, `sequence_number`, `offset`, and `previous_offset`.
- Replayed or duplicate events are logged as warnings and skipped.
- Successful events are logged with `checkpoint_status=pending-host-checkpoint` to show that checkpoint writes happen after the function returns.

## Notes

- The in-memory dictionaries are for demonstration only; production idempotency should use durable state.
- Checkpoints are managed by the Azure Functions Event Hubs extension, not by user code.
