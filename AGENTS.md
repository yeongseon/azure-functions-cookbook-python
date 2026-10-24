# AGENTS.md

## Purpose
`azure-functions-cookbook-python` provides practical recipes and runnable examples for Azure Functions Python v2 applications. It is the dogfood of the Azure Functions Python DX Toolkit — every recipe should be a real, runnable Function App that uses the toolkit libraries in production-realistic scenarios.

## Repository Identity

- Project: `azure-functions-cookbook-python`
- Project type: Python examples and recipes repository
- Runtime scope: Azure Functions Python v2 programming model
- Minimum supported Python: `3.11`
- Packaging: `pyproject.toml` with Hatch

## Read First
- `README.md`
- `CONTRIBUTING.md`
- `PRD.md`
- `DESIGN.md`
- `docs/`

## Working Rules

See [SECURITY.md](SECURITY.md) for runnable-recipe classifications, expiring
exceptions, redacted evidence and the reporting-versus-tag dependency policy.
Use `make security-manifest`, `make security-static`, `make security-semgrep`,
`make security-dependencies-report`, `make security-dependencies` (blocking), and
`make security-host` (opt-in real host). `make security` includes the expanded scan.

### Test Coverage
- Maintain test coverage at **95% or above** for committed changes and PRs.
- For optional local verification, run `hatch run pytest --cov --cov-report=term-missing -q`; required GitHub CI remains authoritative.
- Any PR that drops coverage below 95% must include additional tests to compensate.
- This is an examples/recipes repository — not a runtime library.
- All recipes must be runnable and tested against the supported Python versions.
- Runtime code must remain compatible with Python 3.11+.
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

## Unified PR Review and Merge Policy

Apply the same review standards to human-authored changes and code produced
with OpenCode, Codex, Claude Code, ChatGPT, Copilot or any other agent.
There is **no required AI-specific design, code review or approval route**.

1. Submit a focused, issue-linked PR with appropriate tests, docs and risks.
2. Use **GitHub CI** required checks on the final relevant PR head as the
   authoritative validation record; local checks are useful but optional.
   Preserve coverage thresholds, documentation, security, Azure integration
   and release/publishing safeguards. Do not assume a specific CI runner.
3. Evaluate behavior, security, regressions and maintainability. Oracle,
   Copilot and `agent-review` may provide optional **advisory** observations,
   but do not substitute for human review or actual test execution.
4. Resolve or disposition findings and let the responsible maintainer
   make the merge decision after confirming final CI. High-impact
   security, credential, workflow and release changes need explicit
   independent scrutiny.

## PR Workflow

**Always issue-first.** Before opening any PR:

1. Run `gh issue list` to check whether a tracking issue already exists for the change.
2. If no issue exists, create one following the Issue Conventions below before writing any code.
3. Open the PR only after the issue exists. The PR body **must** include `Closes #N` for every
   issue it resolves — never open a PR that cannot be traced back to an issue.

**Non-negotiable:** a PR without a linked issue will be rejected at review.

## Issue Conventions

Follow these conventions when opening issues so the backlog stays consistent with sibling DX Toolkit repositories.

### Repository scope

- Explain the problem, proposed work, acceptance criteria, and priority using
  verified evidence and user impact in this repository.
- Apply reusable ideas to this repository's actual code, configuration, and
  conventions. Another project's policy or implementation is not evidence that
  the same requirement applies here.
- Remove copied project names, issue links, process labels, and release
  assumptions that are unrelated to the requested work.
- Keep relevant technical evidence and source attribution, including actual
  dependencies, integrations, upstream defects, and official documentation.
  Explain the relationship and the work owned by this repository. Apply the
  same local-evidence requirement to explicitly requested comparisons.
- Before creating or editing an issue, search for duplicates and review every
  project name and repository link in the title and body. The issue must be
  understandable without following an unrelated project's issue or policy.
- After saving, fetch the issue again and verify the saved title, body, and
  labels before reporting completion. Apply these checks to issues created
  through the API or CLI as well as through the issue forms.

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

- Apply at least one type label: `bug`, `enhancement`, `documentation`, or `chore` (`ci`, `test`, `question` where they fit).
- Every new issue gets `needs-triage` (issue forms and the `Triage new issues` workflow add it automatically; add it yourself when creating issues programmatically). **Do not remove it until validity, duplicate checks, repository scope, type, priority, and size have all been confirmed and saved.**
- Priority uses exactly one of the exact GitHub label names `priority: critical` / `priority: high` / `priority: medium` / `priority: low` (lowercase values; a space follows the colon). Never write P0/P1/P2.
  - `critical` — fix now: security issue, data loss, broken released package, or blocked release pipeline.
  - `high` — address before the next planned release; serious impact or no reasonable workaround.
  - `medium` — normal planned work; a workaround exists or scope is limited.
  - `low` — opportunistic polish or non-urgent improvement.
- Priority may be provisional while `needs-triage` is present. An external contributor without label permissions should describe urgency in the issue body.
- Give each actionable issue exactly one effort label using the **exact case-sensitive GitHub label names**: `size: XS` (up to half a working day), `size: S` (about one working day), `size: M` (about two to three working days), `size: L` (about four to five working days), or `size: XL` (more than five working days). Include implementation, tests, CI and docs in the estimate. These are estimates, not deadlines. Split independent or multi-concern work into focused repository-specific issues; retain `size: XL` only when a cohesive task cannot reasonably be split and its scope is justified. For umbrella trackers, size the tracking work itself, not the sum of child issues, and size each child independently.
- Completing triage is a deliberate maintainer/authorized-agent action: verify the issue is actionable, not a duplicate, has its appropriate type/area labels, **one `priority:*` and one `size:*` label**; then remove `needs-triage`. If any decision remains uncertain, leave `needs-triage` and record what is missing. Do not remove it merely because a priority label was assigned.
- Each triage pass must re-evaluate the **entire open-issue backlog in this repository** (not just the newest issue) for relative urgency, impact, release blockers, dependencies, duplication, and effort. Keep priorities consistent, adjust stale priority/size labels when evidence or scope changes, and state which issues should be addressed first. Reapply `needs-triage` if a material scope change invalidates a prior assessment.
- Use exactly one label from the four `priority: ...` values and one from the five `size: ...` values per actionable open issue. Priority is based on impact/urgency, not size; a small security defect may outrank a large enhancement. Do not introduce a separate ranking, project board, or shared cross-repository tracker.
- Add `area:*` labels when they exist in the repository.
- Use `blocker` only when the issue blocks a release.
- There is no work-in-progress label. Open unfinished pull requests as Draft PRs, and link the issue with `Fixes #N` so its in-progress state shows on the issue.

### Umbrella issues

When splitting a large piece of work into focused issues, keep the umbrella open as a tracker that links each child issue with a checkbox; close it once every child is closed or explicitly deferred.

### Project management model

This repository is **issue-based, not milestone-based**. Track and group work using issues plus the existing label taxonomy — do **not** introduce parallel structures.

- Plan and group multi-issue efforts with an **umbrella tracker issue** (see above) plus the existing `priority:*` labels. Do **not** create GitHub Milestones — none exist by design, and their absence is an intentional signal, not an oversight.
- Do **not** invent new label taxonomies (e.g. `epic:*`, `vNext`, release-tag labels) to group work. Reuse the approved `priority:*` and `size:*` labels, existing `area:*` labels, and umbrella issues. Propose other new labels in discussion and wait for explicit approval before creating them.
- Treat optional or tentative suggestions ("we could…", "it might be nice to…") as **discussion, not a directive**. Confirm intent before making any structural change to how work is tracked (milestones, labels, project boards, issue hierarchies).
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
- Releases are driven by **Conventional Commits** on `main`, but only **user-facing** types cut one: `fix:` → patch, `perf:`/`revert:` → patch, `feat:` → minor, `feat!:`/`fix!:`/`BREAKING CHANGE:` → breaking. While pre-1.0, `bump-minor-pre-major` keeps a breaking change on the `0.x` line.
- **`docs:`, `ci:`, `chore:`, `test:`, `build:`, `style:` and `refactor:` do not cut a release.** They are marked `"hidden": true` in `release-please-config.json`, which keeps them out of `CHANGELOG.md`; when a batch of commits contains nothing else, the release notes render empty and Release Please logs `No user facing commits found since <sha> - skipping` and opens no Release PR. Merging such a PR and seeing no version change is the intended outcome, not a broken pipeline. A breaking change still releases whatever its type is.
- There are **no release Makefile targets**; `make release-*`, `make changelog` and `make tag-release` were deleted.
- This repository is a content/examples project. A release produces a tag, a GitHub Release and a changelog entry for consumers to pin against. There is intentionally **no** PyPI publication.
- `release-please.yml` runs with `secrets.RELEASE_PLEASE_TOKEN` (a fine-grained PAT) so the required status checks run on the Release PR. **The PAT expires**; when it does, no Release PR appears. Regenerate it and update the secret before the expiry date.

### Flow
1. Merge Conventional-Commit PRs into `main`. Release Please keeps an open **Release PR** with the next version and the changelog.
2. Merging that Release PR tags the release commit and publishes the GitHub Release.

### Upstream Toolkit Release Gate
This cookbook is the dogfood verification gate for every toolkit library (`azure-functions-openapi`, `azure-functions-validation`, `azure-functions-logging`, `azure-functions-db`, `azure-functions-langgraph`, `azure-functions-scaffold`, `azure-functions-doctor`). When any of those libraries publishes a new release:
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
