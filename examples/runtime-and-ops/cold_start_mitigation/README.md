# cold_start_mitigation

This recipe demonstrates practical cold-start mitigation for Azure Functions Python:

- lazy imports so the worker starts with less work
- module-level connection caching with a reusable `requests.Session()`
- a warmup trigger that preloads the same dependency path used by the HTTP route
- structured logs via `azure-functions-logging-python`
- deployment diagnostics guidance via `azure-functions-doctor-python`

## Prerequisites

- Python 3.10+
- [Azure Functions Core Tools v4](https://learn.microsoft.com/azure/azure-functions/functions-run-local)
- [Azurite](https://learn.microsoft.com/azure/storage/common/storage-use-azurite) for local storage emulation

## Files

- `function_app.py`: HTTP endpoint plus warmup trigger
- `host.json`: standard runtime host configuration
- `local.settings.json.example`: local app settings and optional upstream probe target
- `pyproject.toml`: runtime dependencies

## How it works

1. Startup only configures the app and logging.
2. The first request or warmup trigger lazily imports `requests`.
3. A module-level `requests.Session()` is created once per worker.
4. Later requests reuse the same session instead of rebuilding sockets and adapters.

## Run locally

```bash
cd examples/runtime-and-ops/cold_start_mitigation
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
cp local.settings.json.example local.settings.json
func start
```

Warm the instance locally:

```bash
curl -i http://localhost:7071/admin/warmup
```

Call the demo route:

```bash
curl -s "http://localhost:7071/api/cold-start-demo?ping=0" | python -m json.tool
```

Optionally set `UPSTREAM_URL` in `local.settings.json` and call `?ping=1` to exercise the cached session on an
outbound request.

## Example response

```json
{
  "message": "Cold-start mitigation demo",
  "dependencyLoaded": true,
  "sessionReused": true,
  "sessionCached": true,
  "probe": {
    "enabled": false
  }
}
```

## Diagnostics

Use [`azure-functions-doctor-python`](https://github.com/yeongseon/azure-functions-doctor-python) before deployment to validate app
settings, storage connectivity, and extension health when you are investigating cold-start regressions:

```bash
python -m azure_functions_doctor
```

## Production notes

- Prefer the [Premium plan](https://learn.microsoft.com/en-us/azure/azure-functions/functions-premium-plan) when you need pre-warmed instances.
- Keep warmup logic focused on the modules and clients that materially affect first-request latency.
- Treat module-level caches as best-effort; a worker recycle clears them.
