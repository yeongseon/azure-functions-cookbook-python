# circuit_breaker

This recipe shows an HTTP-triggered Azure Function protecting a downstream API with a simple
in-memory circuit breaker.

## Prerequisites

- Python 3.10+
- [Azure Functions Core Tools v4](https://learn.microsoft.com/azure/azure-functions/functions-run-local)
- Internet access to `https://httpstat.us`, or another endpoint set in `DOWNSTREAM_API_BASE_URL`

## Behavior

- consecutive downstream failures increment the breaker counter
- when failures reach `CIRCUIT_BREAKER_FAILURE_THRESHOLD`, the circuit moves to `open`
- while open, requests are rejected until `CIRCUIT_BREAKER_COOLDOWN_SECONDS` elapses
- after cooldown, one half-open probe is allowed; success closes the circuit, failure reopens it

## Run locally

```bash
cd examples/reliability/circuit_breaker
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp local.settings.json.example local.settings.json
func start
```

## Try it

Successful downstream call:

```bash
curl "http://localhost:7071/api/circuit-breaker?status=200"
```

Trip the breaker with repeated failures:

```bash
curl "http://localhost:7071/api/circuit-breaker?status=503"
curl "http://localhost:7071/api/circuit-breaker?status=503"
curl "http://localhost:7071/api/circuit-breaker?status=503"
```

See open-circuit rejection:

```bash
curl "http://localhost:7071/api/circuit-breaker?status=200"
```

Wait for cooldown, then probe recovery:

```bash
sleep 15
curl "http://localhost:7071/api/circuit-breaker?status=200"
```

## Notes

- This sample uses process-local memory, so circuit state is not shared across instances.
- For production, store breaker state in a durable/shared system such as Durable Entities or Redis.
- For Azure Functions reliability guidance, see [Reliable event processing](https://learn.microsoft.com/en-us/azure/azure-functions/functions-reliable-event-processing).
