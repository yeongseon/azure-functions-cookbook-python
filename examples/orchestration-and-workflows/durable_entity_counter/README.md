# durable_entity_counter

Durable Entity example managing counter state.

## Prerequisites

- Python 3.10+
- [Azure Functions Core Tools v4](https://learn.microsoft.com/azure/azure-functions/functions-run-local)
- [Azurite](https://learn.microsoft.com/azure/storage/common/storage-use-azurite) (local Storage emulator)

## What It Demonstrates

- Entity trigger with `add`, `reset`, and `get` operations
- HTTP signal endpoint: `POST /api/counter/{operation}`
- HTTP read endpoint: `GET /api/counter`

## Run Locally

```bash
cd examples/durable/durable_entity_counter
python -m venv .venv
source .venv/bin/activate
pip install -e .
cp local.settings.json.example local.settings.json
func start
```

## Use Example

```bash
curl -X POST "http://localhost:7071/api/counter/add?value=3"
curl -X GET "http://localhost:7071/api/counter"
curl -X POST "http://localhost:7071/api/counter/reset"
```
