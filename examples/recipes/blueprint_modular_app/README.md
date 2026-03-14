# blueprint_modular_app

This recipe demonstrates a modular Azure Functions app using `func.Blueprint`.

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
pip install -r requirements.txt
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
