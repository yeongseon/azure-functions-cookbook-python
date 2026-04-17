# durable_fan_out_fan_in

Durable Functions fan-out/fan-in orchestration with parallel activities.

## Prerequisites

- Python 3.10+
- [Azure Functions Core Tools v4](https://learn.microsoft.com/azure/azure-functions/functions-run-local)
- [Azurite](https://learn.microsoft.com/azure/storage/common/storage-use-azurite) (local Storage emulator)

## What It Demonstrates

- HTTP starter endpoint: `POST /api/start-fanout`
- Orchestrator scheduling five activity tasks in parallel
- Waiting for all parallel tasks via `context.task_all(tasks)`

## Run Locally

```bash
cd examples/durable/durable_fan_out_fan_in
python -m venv .venv
source .venv/bin/activate
pip install -e .
cp local.settings.json.example local.settings.json
func start
```

## Start Example

```bash
curl -X POST "http://localhost:7071/api/start-fanout"
```
