# bff_facade_api

HTTP Backend-for-Frontend facade that aggregates multiple backend service calls into one client-facing response.

## What It Demonstrates

- HTTP-triggered Azure Function acting as a BFF ingress layer
- Canonical `@app.route` + `@openapi` + `@validate_http` decorator order
- Structured logging for aggregated requests
- Fan-out to profile, orders, and recommendations backends
- Response shaping into one frontend-friendly JSON payload

## Prerequisites

- Python 3.10+
- [Azure Functions Core Tools v4](https://learn.microsoft.com/azure/azure-functions/functions-run-local)
- Internet access to `httpbin.org` or replacement backend URLs

## Run Locally

```bash
cd examples/apis-and-ingress/bff_facade_api
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp local.settings.json.example local.settings.json
func start
```

## Example Request

```bash
curl "http://localhost:7071/api/dashboard?customer_id=cust-123&include_headers=true"
```

## Example Response

```json
{
  "customer_id": "cust-123",
  "profile": {
    "source": "profile",
    "path": "/anything/profile",
    "customer_id": "cust-123",
    "args": {
      "customer_id": "cust-123"
    },
    "echoed_headers": {
      "Host": "httpbin.org"
    }
  },
  "orders": {
    "source": "orders",
    "path": "/anything/orders",
    "customer_id": "cust-123",
    "args": {
      "customer_id": "cust-123"
    },
    "echoed_headers": {
      "Host": "httpbin.org"
    }
  },
  "recommendations": {
    "source": "recommendations",
    "request_id": "<uuid>",
    "customer_id": "cust-123"
  },
  "sources": ["profile", "orders", "recommendations"]
}
```
