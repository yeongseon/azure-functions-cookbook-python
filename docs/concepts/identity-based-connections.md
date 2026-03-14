# Identity-Based Connections

This document explains how to configure Azure Functions Python apps to use managed identity instead of connection strings.

Identity-based connections improve security posture by removing long-lived secrets from app settings and enabling role-based access control (RBAC).

## Why move away from connection strings

Connection strings are simple but high risk:

- Usually grant broad account-level permissions.
- Must be rotated and distributed safely.
- Can leak through logs, exports, or misconfigured pipelines.

Managed identity with RBAC gives stronger controls:

- No embedded secrets in code or config.
- Fine-grained permissions per service.
- Revocation and auditing through Azure AD + Azure RBAC.

## Connection string vs managed identity

| Aspect | Connection string | Managed identity |
| --- | --- | --- |
| Secret material | Required | Not required |
| Rotation burden | High | Low |
| Scope control | Coarse (often account-level) | Fine-grained RBAC |
| Operational safety | Lower | Higher |
| Local dev parity | Needs local secrets | Works with Azure CLI / VS Code sign-in |

## Identity setting patterns

In decorators, you still set `connection="MyConn"`, but the actual settings differ.

### Pattern

- `MyConn` is now a prefix.
- Service-specific suffix keys under that prefix provide endpoint hints.
- The Functions runtime acquires tokens with managed identity.

## Common app setting suffixes

The table below lists commonly used suffixes for identity-based connections in Azure Functions bindings.

| Service | Prefix example | Required suffix settings |
| --- | --- | --- |
| Azure Storage Queue | `StorageConn` | `StorageConn__queueServiceUri` |
| Azure Storage Blob | `StorageConn` | `StorageConn__blobServiceUri` |
| Azure Storage Table | `StorageConn` | `StorageConn__tableServiceUri` |
| Azure Storage (multiple) | `StorageConn` | Any combination of `__queueServiceUri`, `__blobServiceUri`, `__tableServiceUri` |
| Service Bus | `ServiceBusConn` | `ServiceBusConn__fullyQualifiedNamespace` |
| Event Hubs | `EventHubConn` | `EventHubConn__fullyQualifiedNamespace` |
| Cosmos DB | `CosmosConn` | `CosmosConn__accountEndpoint` |

Notes:

- Prefix name is arbitrary but must match decorator `connection`.
- Keep naming consistent across local and cloud environments.
- Some extensions may add extra optional suffix keys; verify extension docs.

## Required RBAC roles by service

Assign roles to the function app's managed identity (system-assigned or user-assigned).

| Service scenario | Minimum role(s) typically needed | Scope recommendation |
| --- | --- | --- |
| Queue trigger reads messages | `Storage Queue Data Message Processor` | Queue or storage account scope |
| Queue output writes messages | `Storage Queue Data Message Sender` | Queue or storage account scope |
| Blob trigger/input reads blobs | `Storage Blob Data Reader` | Container or storage account scope |
| Blob output writes blobs | `Storage Blob Data Contributor` | Container or storage account scope |
| Service Bus trigger receives | `Azure Service Bus Data Receiver` | Queue/subscription scope |
| Service Bus output sends | `Azure Service Bus Data Sender` | Queue/topic scope |
| Event Hub trigger reads | `Azure Event Hubs Data Receiver` | Event Hub or namespace scope |
| Event Hub output sends | `Azure Event Hubs Data Sender` | Event Hub or namespace scope |
| Cosmos DB read/write data | `Cosmos DB Built-in Data Reader` / `Cosmos DB Built-in Data Contributor` | Database/account scope |

Operational tip:

- Start with least privilege and increase only when runtime logs show authorization failures.

## Configuration examples

### Queue trigger with identity

Decorator:

```python
import azure.functions as func

app = func.FunctionApp()

@app.function_name(name="queue_consumer")
@app.queue_trigger(arg_name="msg", queue_name="orders", connection="StorageConn")
def queue_consumer(msg: func.QueueMessage) -> None:
    _ = msg.get_body()
```

App settings:

```text
StorageConn__queueServiceUri=https://mystorage.queue.core.windows.net
```

### Blob output with identity

Decorator:

```python
import azure.functions as func

app = func.FunctionApp()

@app.function_name(name="write_report")
@app.route(route="reports/{name}", methods=["POST"])
@app.blob_output(arg_name="outblob", path="reports/{name}.txt", connection="StorageConn")
def write_report(req: func.HttpRequest, outblob: func.Out[str]) -> func.HttpResponse:
    outblob.set(req.get_body().decode("utf-8"))
    return func.HttpResponse("ok")
```

App settings:

```text
StorageConn__blobServiceUri=https://mystorage.blob.core.windows.net
```

### Service Bus trigger with identity

Decorator:

```python
import azure.functions as func

app = func.FunctionApp()

@app.function_name(name="sb_worker")
@app.service_bus_queue_trigger(
    arg_name="msg",
    queue_name="jobs",
    connection="ServiceBusConn",
)
def sb_worker(msg) -> None:
    pass
```

App settings:

```text
ServiceBusConn__fullyQualifiedNamespace=my-namespace.servicebus.windows.net
```

### Event Hubs trigger with identity

Decorator:

```python
import azure.functions as func

app = func.FunctionApp()

@app.function_name(name="eventhub_consumer")
@app.event_hub_message_trigger(
    arg_name="events",
    event_hub_name="telemetry",
    connection="EventHubConn",
)
def eventhub_consumer(events) -> None:
    pass
```

App settings:

```text
EventHubConn__fullyQualifiedNamespace=my-namespace.servicebus.windows.net
```

### Cosmos DB trigger with identity

Decorator:

```python
import azure.functions as func

app = func.FunctionApp()

@app.function_name(name="cosmos_changes")
@app.cosmos_db_trigger(
    arg_name="docs",
    database_name="appdb",
    container_name="orders",
    lease_container_name="leases",
    connection="CosmosConn",
)
def cosmos_changes(docs: list) -> None:
    pass
```

App settings:

```text
CosmosConn__accountEndpoint=https://my-account.documents.azure.com:443/
```

## Local development with `DefaultAzureCredential`

When running locally, identity-based bindings still work if you have valid local credentials.

Recommended local auth chain:

1. `az login` (Azure CLI credential).
2. VS Code Azure Account sign-in (if applicable).
3. Environment-based service principal for CI-style local runs.

For direct SDK calls in function code, use `DefaultAzureCredential`.

```python
from azure.identity import DefaultAzureCredential
from azure.storage.blob import BlobServiceClient

credential = DefaultAzureCredential()
client = BlobServiceClient(
    account_url="https://mystorage.blob.core.windows.net",
    credential=credential,
)
```

Guidance:

- Keep SDK auth and binding auth aligned where possible.
- Avoid mixing connection strings and identity in the same environment unless migration requires it.
- Use separate prefixes per service for clarity.

## Cloud setup checklist

1. Enable system-assigned or attach user-assigned managed identity.
2. Add identity-based suffix settings to app configuration.
3. Remove or deprecate old connection string settings.
4. Assign required RBAC roles at least-privilege scope.
5. Restart app after config updates.
6. Validate with smoke tests and log inspection.

## Migration strategy

Safe migration pattern from secrets to identity:

1. Introduce new prefix-based settings in non-production slot.
2. Grant identity RBAC roles.
3. Deploy app version referencing the new `connection` prefix.
4. Validate trigger intake and output behavior.
5. Swap slots after verification.
6. Remove legacy connection strings.

## Troubleshooting

If identity-based bindings fail:

- `401/403` -> check role assignment and propagation delay.
- Name resolution errors -> check suffix typo and endpoint URI.
- Works locally, fails in Azure -> verify managed identity enabled on app.
- Works in Azure, fails locally -> ensure `az login` and correct tenant/subscription context.

Useful verification commands:

```bash
az functionapp identity show --name <app> --resource-group <rg>
az role assignment list --assignee <principal-id> --all
```

## Security recommendations

- Prefer managed identity for all first-party Azure resources.
- Scope RBAC at queue/container/topic where feasible.
- Avoid broad account-owner roles for function identities.
- Use deployment slots to test identity changes before production swap.
- Audit role assignments periodically.

## Microsoft Learn references

- Azure Functions identity-based connections: https://learn.microsoft.com/azure/azure-functions/functions-reference#configure-an-identity-based-connection
- Azure Functions Python developer guide: https://learn.microsoft.com/azure/azure-functions/functions-reference-python
- Managed identities for Azure resources: https://learn.microsoft.com/azure/active-directory/managed-identities-azure-resources/overview
- Azure RBAC overview: https://learn.microsoft.com/azure/role-based-access-control/overview
- DefaultAzureCredential overview: https://learn.microsoft.com/python/api/overview/azure/identity-readme

## Related pages

- [Triggers and Bindings Overview](triggers-and-bindings-overview.md)
- [Deployment Patterns](deployment-patterns.md)
- [Python v2 Programming Model](python-v2-programming-model.md)
- [Durable Functions Overview](durable-functions-overview.md)
