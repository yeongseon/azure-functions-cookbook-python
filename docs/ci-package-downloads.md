# CI package downloads and adoption signals

Raw PyPI download counts are **downloads, not unique users**. Automation in this repository installs
Azure Functions Python DX Toolkit packages from PyPI on a schedule and after sibling releases, so
some of the downloads a toolkit package reports are attributable to CI rather than to people. This
page records what this repository does, what it deliberately keeps, and how to read the numbers.
The cookbook is not published to PyPI (see [Versions, snapshots, and verification](snapshots-and-verification.md)),
so it contributes no downloads of its own; its effect is on the six toolkit packages it consumes:
`azure-functions-db`, `azure-functions-doctor`, `azure-functions-langgraph`, `azure-functions-logging`,
`azure-functions-openapi` and `azure-functions-validation`.

## Audit of schedule-triggered workflows

Observation window: the four weeks 2026-10-15 to 2026-11-12, during which each workflow below ran
four times on its weekly (or daily) schedule. A separate `repository_dispatch` trigger re-runs
`E2E Toolkit Matrix` after a sibling release; 45 such runs are on record between 2026-08-25 and
2026-11-06. Counts are of workflow runs, not of package downloads; a hosted-runner pip cache or a
mirror can make a run fetch fewer files than it requests, and a run installs transitive dependencies
too.

| Workflow | Job | Installs toolkit packages from PyPI? | Decision |
| --- | --- | --- | --- |
| `e2e-toolkit.yml` | `E2E (latest toolkit)` | Yes, all six, through `pip install -e ".[dev]"` | **Retained.** This axis exists to check what the recipes advertise against the published releases. |
| `e2e-toolkit.yml` | `E2E (main toolkit)` | **No longer.** It used to install the published wheels and then override them with sibling `main`. | **Changed (#459).** Sibling `main` is installed first, so the published toolkit wheels are not downloaded, and `tools/verify_toolkit_source.py` fails the job if any toolkit package is not a git install. |
| `dependency-audit.yml` | `pip-audit` | Yes, through `pip install -e ".[dev]"` | **Retained.** The subject is the published dependency set, so it must be the published packages. |
| `dependency-audit.yml` | `recipe-runtime-policy` | Yes, each recipe's requirement closure is resolved by `pip-audit` | **Retained.** The subject is how the recipes' requirement ranges resolve on PyPI. |
| `maintenance.yml` | `maintenance` | Yes, through `make install` (Hatch environment with the `dev` extra) | **Retained.** Lint and type-check the cookbook against the published toolkit types a reader would install; it duplicates no download-free alternative. |
| `scheduled-trigger-smoke.yml` | `queue-blob-durable`, `worker-registration-guard` | Yes, through `pip install -e ".[dev]"` | **Retained.** These run the recipes the way a reader runs them, against the published toolkit. |
| `security.yml` | `bandit`, `paid-ai-host` | Yes, through `make install` | **Retained.** These jobs also run on pull requests and `bandit` is a required check; they are not split by event. |
| `security.yml` | `recipe-dependency-report` | Yes, resolves the generated recipe requirements | **Retained.** Reports published-dependency policy. |
| `security.yml` | `recipe-security`, `semgrep` | No: bandit or the scanner only | No change needed. |
| `sbom.yml` | `sbom` | No: it installs the locally built cookbook wheel, which declares no runtime dependencies | Already uses the local build. |
| `codeql.yml`, `snapshot-audit.yml`, `stale.yml` | all | No (CodeQL, PyYAML only, or GitHub API only) | No change needed. |

The cookbook is a consumer of the toolkit, not its source. For this repository "install the local
checkout instead of the published wheel" therefore applies in two places: the cookbook's own wheel
(already used by `sbom.yml`) and the unreleased toolkit sources used by the `main` axis. It does not
apply to jobs whose purpose is to show that the recipes work with what readers install from PyPI.

`tests/test_scheduled_install_audit.py` fails when a schedule-triggered workflow starts installing
packages but is missing from this table, or when a row names a workflow that no longer has a schedule.

## Reading PyPI statistics

- Report raw counts as **downloads**, never as users, installs by distinct people or adoption.
- Automation-attributable downloads (this audit and the sibling repositories' own schedules and
  dispatches) and estimated external interest are separate quantities. This repository can bound the
  first from the table above; it cannot measure the second from PyPI.
- Mirrors, security scanners and dependency bots also download packages and are not separable here.
- Pull-request and push CI in every repository also install the toolkit. They are outside this audit
  of schedule-triggered workflows and are likely the larger share of automation traffic; they are
  necessary and are not changed.
- Before using a download count to choose roadmap work, compare it with organic evidence such as
  external dependents, issues from people outside the project, stars and consumer reports.

## Before and after

The only change in this repository is the `main` axis: each weekly run and each post-release
dispatch of `E2E Toolkit Matrix` previously downloaded the six published toolkit wheels a second time
and discarded them. The expected difference is one fewer set of six wheel downloads per run. To
measure it, compare the cookbook's scheduled and dispatched `E2E Toolkit Matrix` runs against PyPI
statistics for a window of at least four weeks before and after the change, and treat any
difference as an estimate because of the caveats above.
