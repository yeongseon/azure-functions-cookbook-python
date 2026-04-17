# durable_retry_pattern

Durable Functions orchestration retrying a flaky activity.

## Prerequisites

- Python 3.10+
- [Azure Functions Core Tools v4](https://learn.microsoft.com/azure/azure-functions/functions-run-local)
- [Azurite](https://learn.microsoft.com/azure/storage/common/storage-use-azurite) (local Storage emulator)

## What It Demonstrates

- HTTP starter endpoint: `POST /api/start-retry`
- Orchestrator using `RetryOptions` with 5-second interval and 3 attempts
- Activity that intermittently fails to simulate transient errors

## Run Locally

```bash
cd examples/durable/durable_retry_pattern
python -m venv .venv
source .venv/bin/activate
pip install -e .
cp local.settings.json.example local.settings.json
func start
```

## Start Example

```bash
curl -X POST "http://localhost:7071/api/start-retry"
```
