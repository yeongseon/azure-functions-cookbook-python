# Development

This guide covers the day-to-day workflow for improving recipes,
examples, and docs in this repository.

## Local setup

```bash
git clone https://github.com/yeongseon/azure-functions-cookbook-python.git
cd azure-functions-cookbook-python
python -m venv .venv
source .venv/bin/activate
make install
```

If you do not use Make:

```bash
pip install -e ".[dev,docs]"
```

## Development workflow

1. Pick a recipe-driven change.
2. Update the pattern narrative in `docs/patterns/<category>/`.
3. Update matching runnable example in `examples/<category>/`.
4. Update docs in `docs/` (overview pages and pattern pages).
5. Run checks and docs build.

!!! tip
    Keep recipe text and runnable example behavior synchronized.
    Reviewers should be able to follow docs and reproduce behavior.

## Useful make targets

| Command | Purpose |
| --- | --- |
| `make format` | Format code |
| `make lint` | Ruff + mypy checks |
| `make test` | Run test suite |
| `make security` | Run Bandit security checks |
| `make check-all` | Lint + type + test + security |
| `make docs` | Build MkDocs site |
| `make docs-serve` | Serve docs locally |

## Running examples during development

### HTTP API Basic

```bash
cd examples/http_api_basic
pip install -e ".[dev]"
func start
```

### HTTP API with OpenAPI

```bash
cd examples/http_api_openapi
pip install -e ".[dev]"
func start
```

Visit `http://localhost:7071/api/docs` for Swagger UI.

### GitHub Webhook

```bash
cd examples/github_webhook
pip install -e ".[dev]"
func start
```

Set `GITHUB_WEBHOOK_SECRET` before testing signed requests.

### Queue Worker

```bash
cd examples/queue_worker
pip install -e ".[dev]"
func start
```

Use Azurite for local queue execution.

### Timer Job

```bash
cd examples/timer_job
pip install -e ".[dev]"
func start
```

## Quality bar for pull requests

- Clear mapping between recipe and example
- Accurate local run instructions
- Explicit failure handling in code examples
- Production considerations documented
- All checks passing (`make check-all`, `make docs`)

## Documentation-specific workflow

When editing docs:

1. Keep section structure consistent across recipe pages.
2. Use code fences (`bash`, `python`, `json`, `text`) explicitly.
3. Add cross-links to related recipes.
4. Add admonitions for warnings and tips where useful.
5. Confirm links and file paths still match repository layout.

## Before opening a PR

```bash
make check-all
make docs
```

Then verify:

- New recipe pages are linked in `mkdocs.yml`
- Example paths referenced in docs are correct
- No secrets or local-only files are committed

See also: [Testing](testing.md), [Contributing Guidelines](contributing.md)
