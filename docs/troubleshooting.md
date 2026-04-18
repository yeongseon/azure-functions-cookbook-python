# Troubleshooting

This page collects common local-development and runtime issues for cookbook
recipes and examples.

## Quick triage checklist

1. Confirm Python version is compatible (`3.10` to `3.14`).
2. Confirm Azure Functions Core Tools v4 is installed.
3. Confirm example-specific dependencies are installed.
4. Confirm required environment variables are set.
5. Confirm local services (for example Azurite) are running.

!!! warning
    Most startup failures in this repository are environment mismatches,
    not recipe logic defects.

## Azure Functions host issues

### `func` command not found

Install Azure Functions Core Tools v4 and restart your terminal.

### Host starts but no functions are listed

- Verify you are inside a valid example directory.
- Verify `function_app.py` exists in that directory.
- Verify dependencies in `pyproject.toml` are installed.

### Import errors at startup

- Activate your virtual environment.
- Reinstall dependencies with `pip install -e ".[dev]"`.
- For OpenAPI example, ensure `azure-functions-openapi-python` is installed.

## HTTP recipe issues

### 404 for known endpoint

- Confirm route path matches the example.
- Confirm `/api/` prefix is included in request URL.

Examples:

- `GET http://localhost:7071/api/items`
- `GET http://localhost:7071/api/products`

### 400 Invalid JSON

- Ensure `Content-Type: application/json` header is set.
- Ensure request body is valid JSON.

### Swagger UI not available (`http_api_openapi`)

- Verify endpoint path: `http://localhost:7071/api/docs`
- Verify JSON endpoint: `http://localhost:7071/api/openapi.json`
- Verify `azure-functions-openapi-python` dependency is installed.

## GitHub webhook issues

### Always getting `401 Invalid signature`

Check all of the following:

- `GITHUB_WEBHOOK_SECRET` exactly matches GitHub webhook secret.
- Signature header is `X-Hub-Signature-256`.
- Payload bytes used to sign are unchanged before verification.

### Event not handled

Current handlers in the example are for:

- `push`
- `pull_request`
- `issues`

Other events return a benign "no handler" message.

### Local webhook from GitHub not reaching machine

- Use a tunnel (for example ngrok or equivalent).
- Confirm forwarded URL points to `/api/github/webhook`.
- Confirm your function host is running when deliveries are sent.

## Queue worker issues

### Queue trigger never fires locally

- Ensure Azurite is running.
- Ensure `AzureWebJobsStorage` is configured for local storage.
- Ensure queue name is `work-items`.

### JSON parsing errors in logs

The worker expects JSON text in message body.
Send payloads like:

```json
{"id": "123", "action": "index"}
```

### Messages keep retrying

- Check message body format and handler exceptions.
- Verify logic is idempotent.
- Watch dequeue count and poison-queue behavior.

## Timer job issues

### Timer does not execute immediately

This is expected. Schedule is `0 */5 * * * *` (every five minutes).

Use manual trigger for faster validation:

```bash
curl -X POST http://localhost:7071/admin/functions/scheduled_job -H "Content-Type: application/json" -d '{"input":"test"}'
```

### Seeing past-due warning

`timer.past_due` means runtime is catching up after missing a schedule.
This is normal during restarts or downtime.

## Azurite and storage issues

### Connection string errors

Use:

```text
AzureWebJobsStorage=UseDevelopmentStorage=true
```

### Port conflicts

If queue emulation port is busy, reconfigure Azurite and update local settings
to the matching endpoint values.

## Recipe alignment issues

### Docs and example behavior differ

When this happens, trust runnable example behavior first, then update docs.
If you spot a mismatch, open an issue or PR with:

- affected recipe page
- affected example path
- expected vs actual behavior

## Still stuck?

Use this escalation path:

1. Re-run with clean virtual environment.
2. Re-check [Installation](installation.md).
3. Re-check [Getting Started](getting-started.md).
4. Open an issue with logs, steps, and environment details.
