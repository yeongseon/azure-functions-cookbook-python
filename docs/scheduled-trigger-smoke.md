# Scheduled trigger smoke

The **Scheduled trigger smoke** workflow runs queue, blob, and Durable Functions
recipe checks every Tuesday and on manual dispatch. It intentionally does not
run for pull requests, keeping infrastructure-heavy host tests outside the
fast PR path.

The workflow installs Azure Functions Core Tools v4 and Azurite, then runs two
separate suites with their own marker selectors:

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
