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

## Pre-merge toolkit compatibility gate

Pull requests that touch integration-sensitive paths run the `toolkit-compat` job in
`.github/workflows/ci-test.yml`. It is aggregated by the `ci-required` check like every other job, so
a failed, cancelled, empty or unexpectedly skipped run blocks the merge.

| Question | Answer |
| --- | --- |
| Which paths trigger it? | `tests/e2e/**`, the convergence tests, the `full_stack_crud_api` and `personal_langgraph_agent` recipes, `pyproject.toml`, `constraints-min.txt`, the skip/report tooling and the CI workflows themselves. The list lives in `tools/ci_classify_compat.sh`. Docs-only and unrelated recipe changes do not run it. |
| What does it test? | The pull-request checkout (the merge result GitHub builds) on a real Functions Core Tools host, with the exact dependency pins in `constraints-min.txt` (`pip install -c constraints-min.txt -e ".[dev]"`, then `pip check`). |
| Which scenarios? | The tests marked `compat`: validation, OpenAPI and logging metadata and a DB round trip through `full_stack_crud_api`, and LangGraph agent endpoint registration through `personal_langgraph_agent`. Run them with `pytest -m compat tests/e2e`; Core Tools is required. |
| What fails the gate? | A failing test, fewer than the minimum selected tests (zero included), any skipped test, or an installed version that differs from its pin (`tools/compat_report.py`, fed by `tools/pytest_outcome_json.py`). |
| What evidence is kept? | The `toolkit-compat-evidence` artifact (`report.md`, `report.json`): tested commit and PR head, Python and Core Tools versions, pinned versus installed versions, pass/fail/skip counts and skip reasons. The same summary appears in the job summary. |
| Secrets? | None. It runs on `pull_request` with read-only `contents`, so fork pull requests run it unchanged and never see credentials. |
| What stays scheduled-only? | The latest-release and sibling-`main` toolkit matrix (`E2E Toolkit Matrix`, `e2e-toolkit.yml`: weekly, manual and after sibling releases), the other recipes' host tests, Python versions other than 3.11 for the host, and everything that needs real Azure. The pinned set is the supported floor, so it does not show breakage from newer releases. |

This is local-host evidence. It does not show that a recipe works in Azure.

## What to test when editing docs

When documentation changes include command examples or paths:

- Confirm every path exists
- Confirm commands are still valid for current repo layout
- Confirm route names match real handlers in `examples/*/function_app.py`
- Confirm recipe page cross-links resolve

## Test comments and docstrings

- Leave simple, self-explanatory tests without comments; do not add `# Given` / `# When` /
  `# Then` headings by default.
- When a test's failure mode or evidence level is not obvious (catalog and index drift guards,
  dependency or verification-level checks, host-level probes), add a one-line English docstring that
  states the contract and the claim level: offline, host (Core Tools/Azurite), or Azure-only.
- Keep a short inline comment where setup or a host limitation would surprise a reader, for example
  that local Core Tools skips function-key checks.
- A host-boot or import-only smoke test must not suggest it validates optional companion libraries
  it does not import or exercise.
- Comments in runnable recipes follow [CONTRIBUTING.md](https://github.com/yeongseon/azure-functions-cookbook-python/blob/main/CONTRIBUTING.md#comments-and-docstrings-in-recipes) instead.

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
