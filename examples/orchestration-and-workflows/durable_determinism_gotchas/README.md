# durable_determinism_gotchas

Durable Functions orchestrator showing deterministic coding patterns.

## Prerequisites

- Python 3.10+
- [Azure Functions Core Tools v4](https://learn.microsoft.com/azure/azure-functions/functions-run-local)
- [Azurite](https://learn.microsoft.com/azure/storage/common/storage-use-azurite) (local Storage emulator)

## What It Demonstrates

- HTTP starter endpoint: `POST /api/start-determinism`
- Correct time access with `context.current_utc_datetime`
- Correct ID generation with `context.new_guid()`
- Correct orchestration of I/O through activity functions

## Run Locally

```bash
cd examples/durable/durable_determinism_gotchas
python -m venv .venv
source .venv/bin/activate
pip install -e .
cp local.settings.json.example local.settings.json
func start
```

## Start Example

```bash
curl -X POST "http://localhost:7071/api/start-determinism"
```
