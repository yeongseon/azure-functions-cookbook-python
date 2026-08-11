# AGENTS.md

## Purpose
`azure-functions-cookbook-python` provides practical recipes and runnable examples for Azure Functions Python v2 applications. It is the dogfood of the Azure Functions Python DX Toolkit — every recipe should be a real, runnable Function App that uses the toolkit libraries in production-realistic scenarios.

## Read First
- `README.md`
- `CONTRIBUTING.md`
- `PRD.md`
- `DESIGN.md`
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

### Documentation & Translations
- When a change touches `README.md` or any English documentation, update the translated READMEs (`README.ko.md`, `README.ja.md`, `README.zh-CN.md`) **in the same PR** so translations never drift from the English source.
- This applies to any code change that alters documented behavior, CLI output, or the ecosystem/package table — not just direct edits to prose.
- If a full translation cannot land in the same PR, add a short "translation pending" note to the affected translated file and open a tracking issue before merging.

### Recipe Quality Bar
- Treat recipe quality as the primary product surface.
- Prefer reusable patterns over one-off demos.
- Example code should stay simple enough to read, but realistic enough to be useful.
- New recipe work should include production considerations and local run instructions.
- Keep root planning documents in the repository root.
- Keep user-facing documentation in `docs/`.
- Keep pattern source material in `docs/patterns/`.
- Keep runnable sample code in `examples/`.
- `make check-all` must pass before merge.
- `make docs` must build successfully before merge.

### Action Pinning
- Pin every external GitHub Action `uses:` reference in `.github/workflows/` to a full commit SHA with a `# vX.Y.Z` comment.
- Only local composite actions (`uses: ./...`) may skip SHA pinning; document any exception with an inline comment at the call site.
- Dependabot updates SHA-pinned references on the configured schedule and opens PRs when new versions are available.

## PR Workflow

**Always issue-first.** Before opening any PR:

1. Run `gh issue list` to check whether a tracking issue already exists for the change.
2. If no issue exists, create one following the Issue Conventions below before writing any code.
3. Open the PR only after the issue exists. The PR body **must** include `Closes #N` for every
   issue it resolves — never open a PR that cannot be traced back to an issue.

**Non-negotiable:** a PR without a linked issue will be rejected at review.

## Issue Conventions

Follow these conventions when opening issues so the backlog stays consistent with sibling DX Toolkit repositories.

### Title

- Use Conventional Commit prefixes: `feat:`, `fix:`, `docs:`, `refactor:`, `test:`, `chore:`, `ci:`, `build:`, `perf:`.
- Add a scope qualifier when it narrows the area: `feat(examples):`, `docs(recipe):`, `refactor(pattern):`.
- Keep the title imperative, under ~80 characters, no trailing period.
- Do **not** put `[P0]` / `[P1]` / `[P2]` (or any priority marker) in the title — priority is tracked with a `priority:p0` / `priority:p1` / `priority:p2` label.

### Body

Use the following sections, in order, omitting any that do not apply:

```
## Context
What problem this issue addresses and why now. Note the target release (e.g. vX.Y.Z) here if known.

## Acceptance Checklist
- [ ] Concrete, verifiable items.

## Out of scope
- Items intentionally excluded, with links to the issues that track them.

## References
- PRs, ADRs, sibling issues, external docs.
```

### Labels

- Apply at least one of `bug`, `enhancement`, `documentation`, `chore`.
- Apply exactly one `priority:p0` / `priority:p1` / `priority:p2` label to record priority (replaces the old `## Priority` body line).
- Add `area:*` labels when they exist in the repository.
- Use `blocker` only when the issue blocks a release.

### Umbrella issues

When splitting a large piece of work into focused issues, keep the umbrella open as a tracker that links each child issue with a checkbox; close it once every child is closed or explicitly deferred.

## Validation
- `make test`
- `make lint`
- `make typecheck`
- `make build`

## Release Process
- Version is managed via `hatch` (dynamic from `src/azure_functions_python_cookbook/__init__.py`).
- **Do NOT manually edit version strings.** Use the Makefile targets below.

### Commands
- `make release-patch` — bump patch version, update changelog, tag, and push
- `make release-minor` — bump minor version, update changelog, tag, and push
- `make release-major` — bump major version, update changelog, tag, and push
- `make release VERSION=x.y.z` — set explicit version, update changelog, tag, and push
- `make tag-release VERSION=x.y.z` — create and push an annotated tag (used internally by release targets)

### Flow
1. `make release-patch` (or `-minor` / `-major`) on `main`
2. This runs: `hatch version` → `git commit` → `make changelog` → `git commit` → `git tag` → `git push`
3. This repository is a content/examples project — the release cycle produces a tag and updated changelog for consumers to pin against. There is intentionally **no** automated `publish-pypi.yml` workflow.

### Upstream Toolkit Release Gate
This cookbook is the dogfood verification gate for every toolkit library (`azure-functions-openapi`, `azure-functions-validation`, `azure-functions-logging`, `azure-functions-db`, `azure-functions-langgraph`, `azure-functions-knowledge`, `azure-functions-scaffold`, `azure-functions-doctor`, `azure-functions-durable-graph`). When any of those libraries publishes a new release:
1. Upgrade to the freshly published version (`hatch run pip install -U "<package>>=X.Y,<1"`) and run `make test`.
2. Treat any new `RuntimeWarning`/`DeprecationWarning` surfaced by a toolkit library during the run as a release-blocking signal — decorator-order and API-drift problems are reported as warnings, so a clean run (zero warnings from toolkit packages) is required.
3. Bump the affected lower-bound pins (`<package>>=X.Y,<1`) across `pyproject.toml` and every example that pins the package, in the same verification PR, so examples are tested against the version they advertise.
4. The upstream release is **not** considered done until this cookbook passes on the published version.
