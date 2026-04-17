# hello_http_minimal

Minimal HTTP-triggered Azure Function that returns a greeting.

## Prerequisites

- Python 3.10+
- [Azure Functions Core Tools v4](https://learn.microsoft.com/azure/azure-functions/functions-run-local)
- [Azurite](https://learn.microsoft.com/azure/storage/common/storage-use-azurite) (local Storage emulator)

## What It Demonstrates

- The smallest possible `FunctionApp` setup
- A single anonymous `GET` route at `/api/hello`
- Query parameter handling with a default value

## Run Locally

```bash
cd examples/http/hello_http_minimal
python -m venv .venv
source .venv/bin/activate
pip install -e .
cp local.settings.json.example local.settings.json
func start
```

## Expected Output Example

```bash
curl "http://localhost:7071/api/hello?name=Ada"
```

```text
Hello, Ada!
```
