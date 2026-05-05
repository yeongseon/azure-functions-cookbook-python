# AGENTS.md

## Purpose
`azure-functions-cookbook-python` provides practical recipes and examples for Azure Functions Python v2 applications.

## Read First
- `README.md`
- `CONTRIBUTING.md`
- `docs/`

## Working Rules

### Test Coverage
- Maintain test coverage at **95% or above** for committed changes and PRs.
- Run `hatch run pytest --cov --cov-report=term-missing -q` to verify before submitting changes.
- Any PR that drops coverage below 95% must include additional tests to compensate.
- This is an examples/recipes repository — not a runtime library.
- All recipes must be runnable and tested against the supported Python versions.
- Runtime code must remain compatible with Python 3.10+.
- Keep recipe examples, documentation, and tests synchronized.
- When adding a new recipe, add a corresponding test and documentation entry.

## Validation
- `make test`
- `make lint`
- `make typecheck`
- `make build`
