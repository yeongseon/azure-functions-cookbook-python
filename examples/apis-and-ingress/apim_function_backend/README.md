# apim_function_backend

HTTP-triggered Azure Functions backend intended to sit behind Azure API Management policies for auth, rate limiting, and caching.

## Prerequisites

- Python 3.10+
- Azure Functions Core Tools v4
- Optional Azure API Management instance for front-door policy enforcement

## Run Locally

```bash
cd examples/apis-and-ingress/apim_function_backend
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
cp local.settings.json.example local.settings.json
func start
```

## Expected Output

- `GET /api/catalog/{item_id}` returns backend metadata plus APIM forwarding headers.
- `GET /api/catalog/health` provides a simple probe for APIM backend health checks.
