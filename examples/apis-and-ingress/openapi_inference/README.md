# OpenAPI Return-Type Inference

📖 [Full documentation](https://yeongseon.dev/azure-functions-python/cookbook/patterns/apis-and-ingress/openapi-inference/)

Infer the OpenAPI `200` response schema directly from a handler's return-type annotation with `azure-functions-openapi` — no explicit `responses={...}` needed.

## Toolkit Coverage

- `azure-functions-openapi-python` for return-type schema inference
- `azure-functions-logging-python` for structured telemetry

## How It Works

The handler is annotated with `-> GreetingResponse`. When `@openapi` builds the
spec it reads that annotation and infers the `200` response schema from the
Pydantic model — you never spell out `responses={200: GreetingResponse}`.

Because the Azure Functions worker only serializes `str`/`bytes`, a small
`serialize` adapter turns the returned model into a JSON `HttpResponse` at
runtime. The handler keeps its model annotation (so inference works), while the
adapter makes it actually runnable under `func start`.

## Files

```text
openapi_inference/
├── function_app.py
├── host.json
├── local.settings.json.example
├── main.bicep
├── main.tf
├── README.md
├── recipe.yaml
└── pyproject.toml
```

## Endpoints

- `GET /api/openapi/inference/greeting?name=Ada` — greeting whose 200 schema is inferred

## Run Locally

```bash
cd examples/apis-and-ingress/openapi_inference
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
cp local.settings.json.example local.settings.json
func start
```

## Example Requests

```bash
curl "http://localhost:7071/api/openapi/inference/greeting?name=Ada"
```
