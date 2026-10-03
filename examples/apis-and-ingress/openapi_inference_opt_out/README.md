# OpenAPI Return-Type Inference Opt-Out

📖 [Full documentation](https://yeongseon.dev/azure-functions-python/cookbook/patterns/apis-and-ingress/openapi-inference-opt-out/)

Contrast default return-type inference with the per-handler
`infer_return_types=False` opt-out in `azure-functions-openapi`.

## Toolkit Coverage

- `azure-functions-openapi-python` 0.27.1 or later for the inference switch
- `azure-functions-logging-python` for structured telemetry

## How It Works

Both handlers return the same Pydantic `GreetingResponse` model. The default
handler lets `@openapi` infer a `200` response schema from that annotation. The
second handler passes `infer_return_types=False`, so its annotation produces no
typed OpenAPI `200` schema; the generated operation retains only the library's
generic object response.

Use the opt-out when a return annotation represents an internal or transport
type that should not become part of the public API contract. The flag suppresses
only inference; add `responses=` when you want to publish a different explicit
response contract.

## Files

```text
openapi_inference_opt_out/
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

- `GET /api/openapi/inference/default?name=Ada` — inferred `200` schema
- `GET /api/openapi/inference/opt-out?name=Ada` — generic, non-inferred `200` schema

## Run Locally

```bash
cd examples/apis-and-ingress/openapi_inference_opt_out
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
cp local.settings.json.example local.settings.json
func start
```

## Example Requests

```bash
curl "http://localhost:7071/api/openapi/inference/default?name=Ada"
curl "http://localhost:7071/api/openapi/inference/opt-out?name=Ada"
```
