# AGENTS.md

## Purpose
`azure-functions-cookbook-python` provides practical recipes and runnable examples for Azure Functions Python v2 applications. It is the dogfood of the Azure Functions Python DX Toolkit — every recipe should be a real, runnable Function App that uses the toolkit libraries in production-realistic scenarios.

## Repository Identity

- Project: `azure-functions-cookbook-python`
- Project type: Python examples and recipes repository
- Runtime scope: Azure Functions Python v2 programming model
- Minimum supported Python: `3.10`
- Packaging: `pyproject.toml` with Hatch

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

Titles for issues, pull requests, and commits follow the **Title Convention** in [`CONTRIBUTING.md`](CONTRIBUTING.md#title-convention), the single source of truth for the format and the allowed types.

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
- Apply exactly one priority label. The scale in use is `priority:critical` / `priority:high` / `priority:medium` / `priority:low`; `critical` is reserved for defects that reach package users, such as a broken published artifact or wrong product output.
- Labels are applied by maintainers or authorized triage automation. An external contributor without label permissions should describe urgency in the issue body and leave labelling to triage.
- Add `area:*` labels when they exist in the repository.
- Use `blocker` only when the issue blocks a release.

### Umbrella issues

When splitting a large piece of work into focused issues, keep the umbrella open as a tracker that links each child issue with a checkbox; close it once every child is closed or explicitly deferred.

### Project management model

This repository is **issue-based, not milestone-based**. Track and group work using issues plus the existing label taxonomy — do **not** introduce parallel structures.

- Plan and group multi-issue efforts with an **umbrella tracker issue** (see above) plus the existing `priority:*` labels. Do **not** create GitHub Milestones — none exist by design, and their absence is an intentional signal, not an oversight.
- Do **not** invent new label taxonomies (e.g. `epic:*`, `vNext`, release-tag labels) to group work. Reuse `priority:*`, `area:*` (only where they already exist), and the umbrella issue. Propose any new label in discussion and wait for explicit approval before creating it.
- Treat optional or tentative suggestions ("we could…", "it might be nice to…", "~해도 괜찮아") as **discussion, not a directive**. Confirm intent before making any structural change to how work is tracked (milestones, labels, project boards, issue hierarchies).
- Before adding any organizational structure, check whether the repository already has an established convention. A category being empty or unused (zero milestones, no `epic:*` labels) is evidence to follow the existing pattern, not to introduce a new one.

## Validation
- `make test`
- `make lint`
- `make typecheck`
- `make build`

## Release Process

| Tool | Owns |
|---|---|
| **Release Please** | version decision, `__version__`, `CHANGELOG.md`, Release PR, tag, GitHub Release |
| **Hatch** | the `__version__` source (`src/azure_functions_python_cookbook/__init__.py`) |

- **Do NOT manually edit version strings, `CHANGELOG.md`, `.release-please-manifest.json`, or tags.** Release Please owns all of them.
- Releases are driven by **Conventional Commits** on `main`: `fix:` → patch, `feat:` → minor, `feat!:`/`fix!:`/`BREAKING CHANGE:` → breaking. While pre-1.0, `bump-minor-pre-major` keeps a breaking change on the `0.x` line.
- There are **no release Makefile targets**; `make release-*`, `make changelog` and `make tag-release` were deleted.
- This repository is a content/examples project. A release produces a tag, a GitHub Release and a changelog entry for consumers to pin against. There is intentionally **no** PyPI publication.
- `release-please.yml` runs with `secrets.RELEASE_PLEASE_TOKEN` (a fine-grained PAT) so the required status checks run on the Release PR. **The PAT expires**; when it does, no Release PR appears. Regenerate it and update the secret before the expiry date.

### Flow
1. Merge Conventional-Commit PRs into `main`. Release Please keeps an open **Release PR** with the next version and the changelog.
2. Merging that Release PR tags the release commit and publishes the GitHub Release.

### Upstream Toolkit Release Gate
This cookbook is the dogfood verification gate for every toolkit library (`azure-functions-openapi`, `azure-functions-validation`, `azure-functions-logging`, `azure-functions-db`, `azure-functions-langgraph`, `azure-functions-knowledge`, `azure-functions-scaffold`, `azure-functions-doctor`, `azure-functions-durable-graph`). When any of those libraries publishes a new release:
1. Upgrade to the freshly published version (`hatch run pip install -U "<package>>=X.Y,<1"`) and run `make test`.
2. Treat any new `RuntimeWarning`/`DeprecationWarning` surfaced by a toolkit library during the run as a release-blocking signal — decorator-order and API-drift problems are reported as warnings, so a clean run (zero warnings from toolkit packages) is required.
3. Bump the affected lower-bound pins (`<package>>=X.Y,<1`) across `pyproject.toml` and every example that pins the package, in the same verification PR, so examples are tested against the version they advertise.
4. The upstream release is **not** considered done until this cookbook passes on the published version.

## Golden Commands

Use Makefile entry points only. Do not bypass the Makefile in CI or contributor guidance.

| Purpose | Command |
| --- | --- |
| Environment setup | `make install` |
| Format code | `make format` |
| Check formatting (`src`, `tests`) | `make format-check` |
| Lint | `make lint` |
| Type check | `make typecheck` |
| Tests | `make test` |
| Coverage | `make cov` |
| Full validation | `make check-all` |
| Docs build | `make docs` |
| Package build | `make build` |

## Commit Rules

Titles for issues, pull requests, and commits follow the **Title Convention** in [`CONTRIBUTING.md`](CONTRIBUTING.md#title-convention), the single source of truth for the format and the allowed types.

## Agent Rules

When using AI-assisted development:

- Prefer small, reviewable changes.
- Do not guess about behavior that can be verified.
- Keep repository structure aligned with sibling repositories.
- Update docs, examples, and tests together when behavior changes.

## Final Rule

If it is not automated, it will drift.
If it is not documented, it is not a stable rule.

## Merge Policy

- `main` requires a pull request, every required status check green, and all conversations resolved. It requires **zero approving reviews**: `yeongseon` is the only account with push access and GitHub forbids approving your own PR, so a required approval could only ever be met by an administrator bypass. The required checks are what guard `main`.
- **Never use `gh pr merge --admin` to skip a failing or pending required check.**
- Review is still expected, just not enforced. An AI review (`COMMENTED`) is not an approval.
- **Dependabot:** `pip` patch/minor updates auto-merge on green CI. `github-actions` updates never auto-merge — confirm each pinned SHA matches its claimed tag (`git ls-remote --tags <repo>`, compare against the dereferenced `^{}` commit) before merging. `dependabot-automerge.yml` enforces the split.
- If a second maintainer ever gets push access, raise the approval count back to 1.
