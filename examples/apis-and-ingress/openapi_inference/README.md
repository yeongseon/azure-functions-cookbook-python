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

## When Inference Does Nothing

Inference only fires for a return annotation it can turn into a schema — in
practice a Pydantic model. Everything else is **silently skipped**: no schema is
produced, no warning is emitted, and the operation simply has no inferred `200`
body.

| Return annotation | Inferred? |
| --- | --- |
| `-> GreetingResponse` (Pydantic model) | yes |
| `-> func.HttpResponse` | no |
| `-> None` | no |
| `-> int` and other bare scalars | no |

This matters because the failure mode is invisible. A handler annotated
`-> func.HttpResponse` looks correctly decorated and produces a spec with no
response body, so the omission surfaces only when a consumer reads the
generated document. If you need a body documented for one of these handlers,
pass `responses=` explicitly rather than relying on inference.

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
