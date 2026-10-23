# Contributing Guide

We welcome contributions to the `azure-functions-cookbook-python` project.

## Branch Strategy

Use GitHub Flow and branch from `main`.

Recommended branch prefixes:

- `feat/` for new features
- `fix/` for bug fixes
- `docs/` for documentation-only changes
- `chore/` for tooling and maintenance
- `ci/` for workflow updates

## Development Workflow

1. Create a branch from `main`.
   ```bash
   git checkout main
   git pull origin main
   git checkout -b feat/your-feature-name
   ```
2. Write code and tests.
3. Run the local quality gate.
   ```bash
   make check-all
   ```
4. Push and create a pull request.
   ```bash
   git push origin feat/your-feature-name
   ```

## Opening an Issue

Before creating or editing an issue (through the forms, API, or CLI), see
[AGENTS.md "Issue Conventions"](AGENTS.md#issue-conventions) — in particular the
"Repository scope" subsection: ground the issue in verified evidence from this
repository, search for duplicates, review every project name and link in the
title and body, and fetch the saved issue afterward to verify its title, body,
and labels.

## Local development quickstart

Local development requires Python 3.11 through 3.14, as declared by
`requires-python` in `pyproject.toml`, plus GNU Make. No Azure subscription,
Azure Functions Core Tools, Azurite, Docker, or other cloud credentials are
required for the standard contributor checks.

Install Hatch once in an isolated tool environment. From a fresh clone, create
the Hatch environment with the Makefile target:

```bash
make install
```

Then run the standard verification commands:

```bash
make test
make lint
make typecheck
make build
```

## Project Commands

| Command | Contract |
| --- | --- |
| `make install` | Idempotent Hatch environment setup and local hooks; install Hatch once first |
| `make install-ci` | Install dev/docs extras into the selected interpreter; accepts INSTALL_FLAGS for constraints |
| `make doctor` | Read-only Python >=3.11, Hatch/venv, Ruff, mypy, pytest, Bandit diagnostics; missing required tools return nonzero |
| `make lint` | Ruff only, including existing example/script import-modernization policy |
| `make format-check` / `make format` | Read-only formatting check / explicit formatting mutation |
| `make typecheck` / `make security` | Strict mypy / Bandit on the existing runtime surface |
| `make check` | Formatting, lint, types once, security, workflow policy, generated metadata/requirements CHECK modes |
| `make test` | Offline repository unit/mocked and recipe-contract suites, coverage >=95%, per-suite counts |
| `make integration` | Owned local Azurite/Functions hosts: HTTP, queue, blob, toolkit runtime, agent storage and separate import smoke |
| `make verify` | Check, offline tests, isolated per-recipe suites, Bicep, worker registration, integration, build, strict docs |
| `make e2e-azure` | Explicit deployed-Azure preflight/applicability; no provisioning and no local fallback |
| `make report` | Read saved evidence without running tests |
| `make clean` | Remove generated evidence/build/cache/docs artifacts; preserve tracked files, environments and shared resources |

`make check-all` is an exact alias of `make verify`. `make clean-all` retains its
historical deep cleanup, including `.venv` and bytecode. Individual tasks and
focused test selections are **PARTIAL**, never full verification. Local execution
uses Hatch Python 3.11; CI uses its selected interpreter directly, including every
3.11–3.14 matrix cell and the `constraints-min.txt` lane.

### Prerequisites and lane boundaries

Check/test require no Functions host, emulator, Azure subscription or Bicep CLI.
All three generators support `--check`; verification never regenerates tracked
`recipes.json`, README tables or recipe requirements. Bicep compilation is a
separate required verify lane: install `bicep` (or `az bicep install`, or set
`BICEP_CLI`). Missing Bicep produces INCOMPLETE/nonzero, not a skipped PASS.
Worker registration uses the existing pinned official-worker guard and requires
Git/network; inability to clone/load it is INCOMPLETE. Per-recipe environments use
uv and temporary copies, allowing their declared dependency sets without writing
lockfiles or environments into examples. New recipes automatically join metadata
inventory and repository contracts; standalone tests are discovered when present.

Integration requires `func` and `azurite` on PATH. It uses unique loopback ports,
temporary emulator storage and copied recipe apps. Readiness checks host state,
not merely a listening socket. Only run-owned process groups are stopped, including
on timeout/interruption. HTTP/queue/blob/toolkit execution, agent persistence,
Durable import-only smoke and non-emulatable imports remain separate proofs.
Import success is not live trigger execution; the existing blob suite is host-load
evidence, not proof of Event Grid delivery. Toolkit warnings remain errors.

### Evidence and Azure applicability

Gitignored `test-results/` holds test JUnit/coverage/summary, integration per-family
JUnit/logs, recipe results, verify summary/environment/lanes, and azure-e2e evidence.
Schema-versioned JSON records command, lane, required flag, scope, selected/passed/
failed/skipped counts by suite/family, artifact paths and source/package/Python
metadata. Console and Actions Job Summary show the same saved outcomes. Credentials,
tokens and connection strings are redacted; CI uploads available artifacts with
`if: always()`, including failures.

Statuses: **PASS**, **FAIL**, **INCOMPLETE**, **NOT_APPLICABLE**. Required zero tests,
all-skipped, unexpected skips, missing prerequisites/results never PASS. Process
failure retains its exit status. Unsupported recipes alone are NOT_APPLICABLE.
There is currently **no deployed-Azure test suite** in this repository: toolkit E2E
uses local hosts/Azurite. Every recipe's Azure applicability is explicitly false
in the inventory. `make e2e-azure` requires `E2E_BASE_URL` before tests; even with it
set, no remote proof exists, so certification remains INCOMPLETE/nonzero rather
than relabeling emulator results. Adding supported recipes requires actual remote
tests and deployment/candidate identity evidence. No command provisions Azure.

Before opening a PR, run `ruff format --check <changed-python-files>` (or
`ruff format <changed-python-files>` to fix them). `make format-check` checks
`src` and `tests` without changing files. CI checks those same trees and also
reports formatting failures on changed Python files in a dedicated step.

## GitHub Actions Pinning

All external `uses:` references in `.github/workflows/` MUST pin to a
full 40-character commit SHA with a trailing comment documenting the
released version or channel. Example:

```yaml
- uses: actions/checkout@de0fac2e4500dabe0009e67214ff5f5447ce83dd # v6
```

This applies to first-party (`actions/*`, `github/*`, `azure/*`) and
third-party Actions alike.

**Rationale.** Mutable tags (including immutable-looking version tags
like `@v6.0.1`) can be retroactively moved by an attacker who gains
write access to the upstream repository. The
[`tj-actions/changed-files` compromise (CVE-2025-30066, March 2025)](https://www.cisa.gov/news-events/alerts/2025/03/18/supply-chain-compromise-third-party-tj-actionschanged-files-cve-2025-30066)
demonstrated this exact failure mode: ~23,000 repositories had their CI
secrets exfiltrated, and only workflows that pinned to a commit SHA were
safe. GitHub's own guidance now identifies SHA pinning as
[the only way to use an Action as an immutable release](https://docs.github.com/en/actions/security-for-github-actions/security-guides/security-hardening-for-github-actions#using-third-party-actions),
and OpenSSF Scorecard's
[`Pinned-Dependencies` check](https://github.com/ossf/scorecard/blob/main/docs/checks.md#pinned-dependencies)
flags anything weaker as Medium-risk.

Dependabot updates SHA-pinned references on the configured schedule and
keeps the trailing version comment in sync, so the human-readable
context never drifts from the pinned commit.

**Approved exceptions.** The following mutable refs are the only ones
permitted in this repository and are flagged with an inline comment at
the call site:

- `pypa/gh-action-pypi-publish@release/v1` — PyPA-maintained stable
  release channel; this pinning style is explicitly recommended upstream.
- Local composite actions (`uses: ./...`) — versioned with the repo.

When adding a new external Action, resolve the SHA with
`git ls-remote <repo-url> 'refs/tags/<tag>^{}'`. The trailing `^{}`
**dereferences** the ref to its target commit; without it, an
*annotated* tag returns the tag-object SHA instead of the commit SHA,
and the tag-object SHA is **not** a valid `uses:` target.

```bash
# Annotated tag — the two forms return *different* SHAs:
git ls-remote https://github.com/Azure/login 'refs/tags/v3.0.0' 'refs/tags/v3.0.0^{}'
# 93381592...   refs/tags/v3.0.0       <- tag object, do NOT pin to this
# 532459ea...   refs/tags/v3.0.0^{}    <- commit, pin to this one

# Lightweight tag — only the non-deref form returns a row, and it is
# already the commit SHA. Always include the `^{}` form anyway so the
# same command works for both tag types:
git ls-remote https://github.com/actions/setup-python 'refs/tags/v6' 'refs/tags/v6^{}'
```

Single-quote the `refs/...^{}` argument so the `{}` and `^` are not
interpreted by your shell (notably zsh with `EXTENDED_GLOB`).

## Example Coverage Policy

Examples are part of the supported API experience and should stay verified.

- Keep one representative example for each recipe category (HTTP, Blob, Cosmos DB, etc.).
- Keep one complex example for advanced integration patterns.
- Add or update smoke tests whenever an example changes.
- Prefer lightweight smoke coverage over infrastructure-heavy end-to-end tests.

## Example Layout: Flat vs App-Layout

Examples use one of two directory layouts. Pick the layout that matches the
amount of business logic the recipe demonstrates:

- **Flat layout** — a single `function_app.py` at the example root. Use this
  when the recipe has **at most one file of business logic** and exists mainly
  to show a trigger, binding, or configuration in isolation.
- **App-layout** — an `app/` package (`app/functions`, `app/services`,
  `app/core`, …) alongside `function_app.py`. Use this when the recipe
  **demonstrates service separation** or spans **more than two modules**, so
  the structure itself is part of what the recipe teaches.

When in doubt, prefer the flat layout: it keeps the copy-paste surface small.
Reach for app-layout only when the separation is the point of the recipe.

### Scaffolding a new flat recipe

Use the `new-recipe` target to generate a ready-to-run flat example that
already passes the auto-discovery and `recipe.yaml` metadata guards:

```bash
make new-recipe CAT=apis-and-ingress NAME=my_recipe DIFFICULTY=Beginner
```

`DIFFICULTY` must be one of `Beginner`, `Intermediate`, or `Advanced` — the
README recipe table requires every recipe to declare one.

This creates `examples/<CAT>/<NAME>/` with `function_app.py`, `README.md`,
`recipe.yaml`, `host.json`, `local.settings.json.example`, and `pyproject.toml`.
The generated `recipe.yaml` has no `docs_url` yet, since no matching
`docs/patterns/<CAT>/<slug>.md` page exists; add one only after writing that
page. Then implement the trigger logic and refine the description before
committing.


## Title Convention

This section is the single source of truth for issue, pull request, and commit titles in this repository. `AGENTS.md`, the pull request template, the issue forms, and the documentation site point here instead of restating the rules.

Issues, pull requests, and the final squash commit on the default branch all use:

```text
type: description
type(scope): description
```

- Write titles in English.
- `type` and `scope` are lowercase. Put exactly one space after the colon.
- `scope` is optional. Add it only when it narrows the area; do not add one just for uniformity.
- `description` states what changes and why, concisely. Start with a lowercase word, but keep the spelling of API names, acronyms, error codes, and proper nouns.
- No trailing period.
- No priority, size, status, or owner markers, and no bracket prefixes such as `[Bug]`, `[Feature]`, or `[WIP]`. Use labels and Draft pull requests instead.
- An issue title may describe the problem; the pull request title describes the change that resolves it. Keep them aligned when they cover the same work, without forcing identical wording when the scope differs.
- Do not put issue numbers in pull request titles. Link issues in the pull request body with `Closes #123` or `Refs #123`.

| type | use for |
|---|---|
| `feat` | a user-facing feature or capability |
| `fix` | a bug fix in product behavior |
| `docs` | documentation only |
| `test` | adding or changing tests |
| `perf` | a performance improvement |
| `refactor` | internal restructuring that keeps external behavior |
| `ci` | CI and automation workflows |
| `build` | build, packaging, and dependency changes |
| `chore` | maintenance that fits none of the above |
| `style` | formatting only, no behavior change |
| `revert` | reverting an earlier change |

A breaking change adds `!` before the colon: `type!: description` or `type(scope)!: description`. Whether a change is breaking, and how it is released, is decided by the Release Process in [AGENTS.md](AGENTS.md), not by the title alone. Release Please reads these titles from the squash commits on `main`: `fix` and `feat` drive the version bump, and the other types only shape the changelog.

Examples:

```text
fix(blob-and-file-triggers): decode blob URL paths before constructing storage clients
feat(recipe): add a Durable Functions fan-out/fan-in example
docs(readme): clarify the local setup steps
refactor!: rename the public configuration keys
```

Not accepted: `[Bug] crash on save` (bracket prefix, no type), `Fix: crash on save` (uppercase type), `feature: add export` (type not in the table), `fix: crash on save.` (trailing period), `fix: decode blob paths (#503)` (the pull request number belongs in the body).

Pull requests are squash-merged and the pull request title becomes the final commit title. GitHub appends the pull request number by itself, so `fix: decode nonempty NULL-only collection results` lands on `main` as `fix: decode nonempty NULL-only collection results (#503)`. Do not write that number into the title yourself — the check rejects a title ending in `(#123)`, because it would be doubled. Link the issue from the pull request body instead, for example `Closes #503`. The **PR title** check validates the format whenever a pull request is opened, edited, reopened, or updated. Individual commits on a branch are not checked.

Issue titles are not enforced. Anyone can open an issue without knowing this convention; maintainers adjust the title during triage.

## Releases

Merging to `main` does not publish anything. This repository is a collection of
runnable examples; it is not packaged or published to PyPI, and no workflow is
triggered by a tag.

Contributors never need to bump a version or create a tag. Release Please cuts a
versioned snapshot when its Release PR is merged, tagging the repository
for reference only -- no artifact is produced or uploaded.

## Code of Conduct

Be respectful and inclusive. See our [Code of Conduct](CODE_OF_CONDUCT.md) for details.
