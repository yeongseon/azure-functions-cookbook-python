# Testing

## Canonical verification

`make doctor` diagnoses the environment without tests or installation.
`make check` runs non-mutating quality and generator `--check` modes, types once.
`make test` is offline with coverage >=95%. `make integration` starts run-owned
Azurite/Functions hosts on unique ports and removes only its own processes/storage.
`make verify` adds isolated recipe suites, required Bicep compilation, pinned-worker
registration, build and strict docs; `make check-all` is an exact alias.

Required missing/zero/all-skipped/unexpected-skipped lanes are INCOMPLETE/nonzero,
never PASS. Individual selections are PARTIAL. `make report` displays saved
`test-results/` JUnit/coverage/logs and schema-versioned per-family summaries with
redacted environment metadata. `make clean` preserves tracked files and venvs;
`make clean-all` retains deep-clean semantics.

No current recipe has deployed-Azure certification: toolkit E2E runs locally.
`make e2e-azure` fails before tests when E2E_BASE_URL is absent and remains
INCOMPLETE until real remote support exists; unsupported recipe applicability is
NOT_APPLICABLE. It never provisions Azure or substitutes emulator success.

Testing in this cookbook has two goals:

1. Validate repository quality checks.
2. Validate that each runnable example behaves as documented.

## Repository-level checks

Run the full quality suite:

```bash
make check-all
```

This includes:

- Linting and type checks
- Unit tests
- Security scan

For docs integrity:

```bash
make docs
```

## Individual commands

| Command | What it validates |
| --- | --- |
| `make format` | Formatting conventions |
| `make lint` | Ruff correctness; types are a separate task |
| `make test` | Automated tests |
| `make cov` | Coverage report generation |
| `make security` | Bandit static security checks |
| `make docs` | MkDocs build and link rendering |

## Testing recipe examples locally

### Hello HTTP Minimal

```bash
cd examples/apis-and-ingress/hello_http_minimal
pip install -e .
func start
```

Smoke checks:

```bash
curl http://localhost:7071/api/hello
curl "http://localhost:7071/api/hello?name=Azure"
```

### GitHub Webhook

```bash
cd examples/apis-and-ingress/webhook_github
pip install -e .
func start
```

Set `GITHUB_WEBHOOK_SECRET`, then send signed and unsigned test payloads.
Expected behavior: unsigned or invalid signatures return `401`.

### Queue Consumer

```bash
cd examples/messaging-and-pubsub/queue_consumer
pip install -e .
func start
```

Run Azurite and enqueue JSON messages into `work-items`.
Verify logs show dequeue count, JSON parsing, and task completion.

### Timer Cron Job

```bash
cd examples/scheduled-and-background/timer_cron_job
pip install -e .
func start
```

Verify scheduled runs in logs, then manually trigger with:

```bash
curl -X POST http://localhost:7071/admin/functions/scheduled_job -H "Content-Type: application/json" -d '{"input":"test"}'
```

## What to test when editing docs

When documentation changes include command examples or paths:

- Confirm every path exists
- Confirm commands are still valid for current repo layout
- Confirm route names match real handlers in `examples/*/function_app.py`
- Confirm recipe page cross-links resolve

## CI alignment

Local validation should mirror CI as closely as possible.
Before PR submission, run at minimum:

```bash
make check-all
make docs
```

If your change touches trigger behavior, also run the relevant example app and
manually verify expected responses or logs.

See also: [Development](development.md), [Troubleshooting](troubleshooting.md)
