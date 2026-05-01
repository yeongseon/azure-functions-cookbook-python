# Observability Tracing

📖 [Full documentation](https://yeongseon.github.io/azure-functions-cookbook-python/patterns/runtime-and-ops/observability-tracing/)

HTTP-triggered tracing recipe showing correlation ID propagation,
structured logging,
and Application Insights-friendly trace context.

## Prerequisites

- Python 3.10+
- [Azure Functions Core Tools v4](https://learn.microsoft.com/azure/azure-functions/functions-run-local)
- [Azurite](https://learn.microsoft.com/azure/storage/common/storage-use-azurite) (local Storage emulator)
- Optional: Application Insights connection string for Azure-side telemetry validation

## What It Demonstrates

- Reuse of inbound `traceparent` when an upstream caller already started a trace
- Fallback generation of `traceparent` and `x-correlation-id` when headers are missing
- Structured logging with `correlation_id`, `trace_id`, `span_id`, and telemetry markers
- Response header propagation so downstream hops can continue the same correlation chain

## Run Locally

```bash
cd examples/runtime-and-ops/observability_tracing
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
cp local.settings.json.example local.settings.json
func start
```

## Expected Output Example

```bash
curl -i \
  -H "traceparent: 00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01" \
  -H "x-correlation-id: checkout-req-42" \
  "http://localhost:7071/api/trace-demo"
```

```text
HTTP/1.1 200 OK
x-correlation-id: checkout-req-42
traceparent: 00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01

{"message": "Tracing metadata attached to logs and response.", "correlation_id": "checkout-req-42", ...}
```

## Notes

- Locally, you mainly validate propagation behavior and structured logs.
- In Azure, Application Insights correlates request telemetry with emitted logs.
- Forward `traceparent`, `tracestate`, and `x-correlation-id` when this function calls downstream APIs.
