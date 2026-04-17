# blueprint_modular_app

This recipe demonstrates a modular Azure Functions app using `func.Blueprint`.

## Prerequisites

- Python 3.10+
- [Azure Functions Core Tools v4](https://learn.microsoft.com/azure/azure-functions/functions-run-local)
- [Azurite](https://learn.microsoft.com/azure/storage/common/storage-use-azurite) (local Storage emulator)

## What it includes

- `function_app.py` registers `bp_health` and `bp_users`
- `bp_health.py` exposes `GET /api/health`
- `bp_users.py` exposes:
  - `GET /api/users`
  - `GET /api/users/{id}`
  - `POST /api/users`

The user endpoints use an in-memory dictionary for quick CRUD examples.

## Run locally

```bash
cd examples/recipes/blueprint_modular_app
python -m venv .venv
source .venv/bin/activate
pip install -e .
cp local.settings.json.example local.settings.json
func start
```

## Example requests

```bash
curl http://localhost:7071/api/health
curl http://localhost:7071/api/users
curl -X POST http://localhost:7071/api/users -H "Content-Type: application/json" \
  -d '{"id":"u1","name":"Ada"}'
curl http://localhost:7071/api/users/u1
```
