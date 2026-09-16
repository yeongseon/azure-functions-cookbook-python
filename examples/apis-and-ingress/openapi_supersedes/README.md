# OpenAPI Validation Supersedes Inference

📖 [Full documentation](https://yeongseon.dev/azure-functions-python/cookbook/patterns/apis-and-ingress/openapi-supersedes/)

Demonstrate response-schema **precedence**: when both return-type inference and
a validation `response_model` are available, the validation model wins the
OpenAPI `200` schema.

## Toolkit Coverage

- `azure-functions-openapi-python` for endpoint metadata and schema precedence
- `azure-functions-validation-python` for the winning `response_model`
- `azure-functions-logging-python` for structured telemetry

## How It Works

The handler is annotated `-> InferredGreetingResponse` (a single `message`
field), so return-type inference alone would produce that schema. But
`@validate_http(response_model=ExplicitGreetingResponse)` supplies a richer
model (`message` + `source` + `precedence`). The OpenAPI `200` schema resolves
to `ExplicitGreetingResponse` — validation supersedes inference. Because
`response_model` also serializes the returned model, the handler stays runnable
without any manual adapter.

## Files

```text
openapi_supersedes/
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

- `GET /api/openapi/supersedes/greeting?name=Ada` — greeting whose 200 schema comes from validation

## Run Locally

```bash
cd examples/apis-and-ingress/openapi_supersedes
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
cp local.settings.json.example local.settings.json
func start
```

## Example Requests

```bash
curl "http://localhost:7071/api/openapi/supersedes/greeting?name=Ada"
```
