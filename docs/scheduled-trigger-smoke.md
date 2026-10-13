# Scheduled trigger smoke

The **Scheduled trigger smoke** workflow runs queue, blob, and Durable Functions
recipes every Tuesday and on manual dispatch. It intentionally does not run for
pull requests, keeping infrastructure-heavy host tests outside the fast PR path.

The workflow installs Azure Functions Core Tools v4 and Azurite, then executes:

- `tests/e2e/test_queue_examples.py`
- `tests/e2e/test_blob_examples.py`
- `tests/e2e/test_durable_examples.py`

These suites use Azurite for local blob, queue, and Durable task-hub storage. No
Azure subscription, cloud credentials, or repository secrets are required.
