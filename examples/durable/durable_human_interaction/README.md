# durable_human_interaction

Durable Functions workflow waiting for an external approval event with timeout.

## What It Demonstrates

- HTTP starter endpoint: `POST /api/start-approval`
- Event endpoint: `POST /api/approve/{instance_id}`
- Orchestrator waiting for `ApprovalEvent` or a 5-minute timer, whichever happens first

## Run Locally

```bash
cd examples/durable/durable_human_interaction
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
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
