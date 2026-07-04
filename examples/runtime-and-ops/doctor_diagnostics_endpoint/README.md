# Doctor Diagnostics Endpoint

📖 [Full documentation](https://yeongseon.github.io/azure-functions-cookbook-python/patterns/runtime-and-ops/doctor-diagnostics-endpoint/)

Expose [`azure-functions-doctor`](https://github.com/yeongseon/azure-functions-doctor-python)
diagnostics as authenticated HTTP endpoints so operators can query deployment
health post-deploy without shelling into the container.

## Prerequisites

- Python 3.10+
- [Azure Functions Core Tools v4](https://learn.microsoft.com/azure/azure-functions/functions-run-local)
- [Azurite](https://learn.microsoft.com/azure/storage/common/storage-use-azurite) (local Storage emulator)

## What it includes

- `function_app.py` registers `diagnostics_blueprint`
- `GET /api/health` — anonymous liveness probe (returns `{"status": "healthy"}`)
- `GET /api/diagnostics` — full `SectionResult[]` from `azure-functions-doctor` (auth level: `FUNCTION`)
- `GET /api/diagnostics/summary` — reduced pass/fail summary (auth level: `FUNCTION`)

The service layer reads the `AFD_TARGET_PATH` env var (default: `os.getcwd()`) so the
scan target is configurable in production and testable in unit tests.

## Run locally

```bash
cd examples/runtime-and-ops/doctor_diagnostics_endpoint
python -m venv .venv
source .venv/bin/activate
pip install -e .[dev]
cp local.settings.json.example local.settings.json
func start
```

## Example requests

```bash
# Anonymous liveness probe
curl http://localhost:7071/api/health

# Full diagnostics (requires function key when deployed)
curl "http://localhost:7071/api/diagnostics?code=$FUNCTION_KEY"

# Pass/fail summary
curl "http://localhost:7071/api/diagnostics/summary?code=$FUNCTION_KEY"
```

## Security note

`/api/diagnostics` and `/api/diagnostics/summary` return deployment metadata that could
help an attacker fingerprint your app. They default to `AuthLevel.FUNCTION`. In
production, prefer `AuthLevel.ADMIN` or gate them behind Azure Front Door / APIM with
IP allowlists.
