# Testing

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
| `make lint` | Ruff + mypy correctness |
| `make test` | Full suite: library and repository infrastructure tests |
| `make test-library` | Library lane: shipped-library and recipe behavior only |
| `make test-infra` | Infrastructure lane (`repo_infra` marker): tools, scripts, workflows, Makefile, packaging |
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
