# durable_human_interaction

Durable Functions workflow waiting for an external approval event with timeout.

## Prerequisites

- Python 3.10+
- [Azure Functions Core Tools v4](https://learn.microsoft.com/azure/azure-functions/functions-run-local)
- [Azurite](https://learn.microsoft.com/azure/storage/common/storage-use-azurite) (local Storage emulator)

## What It Demonstrates

- HTTP starter endpoint: `POST /api/start-approval`
- Event endpoint: `POST /api/approve/{instance_id}`
- Orchestrator waiting for `ApprovalEvent` or a 5-minute timer, whichever happens first

## Run Locally

```bash
cd examples/durable/durable_human_interaction
python -m venv .venv
source .venv/bin/activate
pip install -e .
cp local.settings.json.example local.settings.json
func start
```

## Start Example

```bash
curl -X POST "http://localhost:7071/api/start-approval"
```

Use the returned `instanceId` to raise approval:

```bash
curl -X POST "http://localhost:7071/api/approve/<instance_id>"
```
