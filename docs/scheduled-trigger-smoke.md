# Scheduled trigger smoke

The **Scheduled trigger smoke** workflow runs queue, blob, Durable Functions,
and worker-registration checks every Tuesday and on manual dispatch. It
intentionally does not run for pull requests, keeping infrastructure-heavy and
network-dependent checks outside the fast PR path.

## `queue-blob-durable`

Installs Azure Functions Core Tools v4 and Azurite, then runs two separate
suites with their own marker selectors:

- `tests/e2e/test_queue_examples.py` and `tests/e2e/test_blob_examples.py`
  (`-m e2e`): live tests against Azurite-backed queue and blob storage. No
  Azure subscription, cloud credentials, or repository secrets are required.
- `tests/e2e/test_durable_examples.py` (`-m smoke`): **import-only** checks
  that each Durable recipe's `function_app.py` loads and exposes a valid
  Blueprint. Durable Functions requires the Durable Task Framework storage
  backend, which takes 90+ seconds to initialize with Azurite locally, making
  live E2E orchestration tests impractical here; this suite does not start,
  execute, or verify a real orchestration run.

A final verification step (`tools/verify_scheduled_smoke_selection.py`) runs
both selectors in collection-only mode and fails the job if either one would
select zero tests -- a single combined selector previously caused every
Durable test to be silently deselected (#177), passing the job while
executing no Durable coverage at all.

## `worker-registration-guard`

Runs `tests/test_worker_registration_guard.py` (`-m worker_registration`): a
deterministic guard that clones the official `azure-functions-python-worker`
at a pinned SHA and indexes real SDK `Function` objects from recipe handlers
through its actual `Registry.add_indexed_function()` -- the same validation
path the real worker applies when a Function App is deployed. Protocol-typed
or otherwise non-worker-compatible handler annotations (#379) fail this check
even though they import cleanly and work under mocked unit tests. Requires
network access to clone the pinned worker commit, so it runs here rather than
on every pull request.

The job installs the pinned worker's runtime requirements (`grpcio`, `protobuf`
and `python-dateutil`, mirroring its `workers/pyproject.toml` for Python 3.12) and
loads `tools.pytest_fail_on_skip`. A failed clone, a missing requirement, a
registry that cannot load or any skipped test fails the job (#437): the guard
never reports success without having indexed every handler. Re-check the pins in
the workflow whenever `WORKER_SHA` moves.
