# managed_identity_servicebus

This recipe shows a Service Bus queue trigger using `connection="ServiceBusConnection"`.

## Connection setting patterns

- Connection string pattern:
  - `ServiceBusConnection="Endpoint=sb://..."`
- Managed identity pattern:
  - `ServiceBusConnection__fullyQualifiedNamespace="<ns>.servicebus.windows.net"`

The `__fullyQualifiedNamespace` suffix enables identity-based binding resolution for Service Bus.

## Run locally

```bash
pip install -r requirements.txt
func start
```
