# durable_unit_testing

Durable Functions sample focused on mock-based orchestrator unit testing.

## What It Demonstrates

- Small starter/orchestrator/activity durable app
- Unit test stepping through orchestrator generator using `next()` and `send()`
- Assertions on `call_activity` invocation order and final returned result

## Run Locally

```bash
cd examples/durable/durable_unit_testing
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp local.settings.json.example local.settings.json
func start
```

## Run Unit Test

```bash
cd examples/durable/durable_unit_testing
python -m pytest test_orchestrator.py
```
