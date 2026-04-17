# durable_unit_testing

Durable Functions sample focused on mock-based orchestrator unit testing.

## Prerequisites

- Python 3.10+
- [Azure Functions Core Tools v4](https://learn.microsoft.com/azure/azure-functions/functions-run-local)
- [Azurite](https://learn.microsoft.com/azure/storage/common/storage-use-azurite) (local Storage emulator)

## What It Demonstrates

- Small starter/orchestrator/activity durable app
- Unit test stepping through orchestrator generator using `next()` and `send()`
- Assertions on `call_activity` invocation order and final returned result

## Run Locally

```bash
cd examples/durable/durable_unit_testing
python -m venv .venv
source .venv/bin/activate
pip install -e .
cp local.settings.json.example local.settings.json
func start
```

## Run Unit Test

```bash
cd examples/durable/durable_unit_testing
python -m pytest test_orchestrator.py
```
