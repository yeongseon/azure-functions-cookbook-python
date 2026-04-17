# managed_identity_servicebus

This recipe shows a Service Bus queue trigger using `connection="ServiceBusConnection"`.

## Prerequisites

- Python 3.10+
- [Azure Functions Core Tools v4](https://learn.microsoft.com/azure/azure-functions/functions-run-local)
- [Azurite](https://learn.microsoft.com/azure/storage/common/storage-use-azurite) (local Storage emulator)
- An Azure Service Bus namespace with a queue named `tasks`

## Environment Variables

| Variable | Purpose | Example |
|----------|---------|---------|
| `ServiceBusConnection` | Service Bus connection string (classic) | `Endpoint=sb://<namespace>.servicebus.windows.net/;SharedAccessKeyName=<name>;SharedAccessKey=<key>` |
| `ServiceBusConnection__fullyQualifiedNamespace` | Namespace for managed identity | `<namespace>.servicebus.windows.net` |

Use **either** `ServiceBusConnection` (connection string) **or** `ServiceBusConnection__fullyQualifiedNamespace` (managed identity), not both.

Set in `local.settings.json` under `Values`. Copy `local.settings.json.example` as a starting template.

## Connection Setting Patterns

- Connection string pattern:
  - `ServiceBusConnection="Endpoint=sb://..."`
- Managed identity pattern:
  - `ServiceBusConnection__fullyQualifiedNamespace="<ns>.servicebus.windows.net"`

The `__fullyQualifiedNamespace` suffix enables identity-based binding resolution for Service Bus.

## Run Locally

```bash
cd examples/recipes/managed_identity_servicebus
python -m venv .venv
source .venv/bin/activate
pip install -e .
cp local.settings.json.example local.settings.json
func start
```

## Expected Output

- Queue messages on `tasks` trigger the function and log processing status.
- When using managed identity, ensure the identity has **Azure Service Bus Data Receiver** role.
