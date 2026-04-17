# queue_consumer

Queue-triggered Azure Function that parses and processes task messages.

## Prerequisites

- Python 3.10+
- [Azure Functions Core Tools v4](https://learn.microsoft.com/azure/azure-functions/functions-run-local)
- [Azurite](https://learn.microsoft.com/azure/storage/common/storage-use-azurite) (local Storage emulator)

## What It Demonstrates

- Queue trigger binding for `outbound-tasks`
- JSON deserialization with graceful invalid payload handling
- Logging message identifiers and `dequeue_count` for retry visibility

## Run Locally

```bash
cd examples/queue/queue_consumer
python -m venv .venv
source .venv/bin/activate
pip install -e .
cp local.settings.json.example local.settings.json
func start
```

## Expected Output

- On each queue message, logs show message ID, dequeue count, and task type.
- Invalid JSON messages are logged as errors without crashing the function host.
