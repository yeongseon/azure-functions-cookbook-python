# durable_hello_sequence

Durable Functions orchestrator chaining activities in sequence.

## Prerequisites

- Python 3.10+
- [Azure Functions Core Tools v4](https://learn.microsoft.com/azure/azure-functions/functions-run-local)
- [Azurite](https://learn.microsoft.com/azure/storage/common/storage-use-azurite) (local Storage emulator)

## What It Demonstrates

- HTTP starter endpoint: `POST /api/start-sequence`
- Orchestrator calling `say_hello` for `Tokyo`, `Seattle`, and `London` in order
- Aggregating activity outputs into a final list result

## Run Locally

```bash
cd examples/durable/durable_hello_sequence
python -m venv .venv
source .venv/bin/activate
pip install -e .
cp local.settings.json.example local.settings.json
func start
```

## Start Example

```bash
curl -X POST "http://localhost:7071/api/start-sequence"
```
