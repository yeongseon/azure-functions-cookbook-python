# Tenant Isolation

> **Trigger**: HTTP | **State**: stateless | **Guarantee**: request-response | **Difficulty**: advanced

## Overview

This recipe demonstrates per-request tenant isolation in an Azure Functions Python v2 app.
The function resolves a tenant ID from an explicit request header or a JWT claim,
maps that tenant to isolated infrastructure, and executes the request against the tenant's own database.

The example combines the `db`, `validation`, `openapi`, and `logging` integrations so the handler stays declarative while tenant routing remains visible and auditable.

## When to Use

- You run a shared control plane with tenant-dedicated data stores.
- You need to route each request to tenant-specific resources at runtime.
- You want a single HTTP endpoint that can serve multiple tenants without mixing data.
- You need structured logs and validated inputs around tenant resolution.

## When NOT to Use

- Your workload is truly single-tenant and can bind to one fixed database.
- Tenant boundaries are enforced upstream and the function never needs tenant context.
- You need cross-tenant analytics or fan-out queries in the request path.
- Your isolation model is row-level security in one shared database rather than tenant-specific resources.

## Architecture

```mermaid
flowchart LR
    request[HTTP request] --> resolver[Tenant resolver\nheader or JWT]
    resolver --> policy[Validate tenant mapping]
    policy --> db1[(Tenant A DB)]
    policy --> db2[(Tenant B DB)]
    policy --> dbn[(Tenant N DB)]
    db1 --> response[HTTP response]
    db2 --> response
    dbn --> response
```

## Behavior

```mermaid
sequenceDiagram
    participant Client
    participant Function as HTTP function
    participant Resolver as Tenant resolver
    participant Config as App settings
    participant DB as Tenant database

    Client->>Function: POST /api/tenant/invoices/query
    Function->>Resolver: Read X-Tenant-ID or JWT tid
    Resolver-->>Function: tenant-a
    Function->>Config: Resolve TENANT_TENANT_A_DB_URL
    Config-->>Function: SQLAlchemy URL
    Function->>DB: Query tenant-local invoices
    DB-->>Function: tenant-scoped rows
    Function-->>Client: 200 JSON response
```

## Prerequisites

- Python 3.10+
- Azure Functions Core Tools v4
- `azure-functions-db-python`
- `azure-functions-validation-python`
- `azure-functions-openapi-python`
- `azure-functions-logging-python`
- One database per tenant with a compatible `invoices` table

## Project Structure

```text
examples/security-and-tenancy/tenant_isolation/
|-- function_app.py
|-- host.json
|-- local.settings.json.example
|-- pyproject.toml
`-- README.md
```

## Implementation

The tenant resolver follows a simple precedence order:

1. Use `X-Tenant-ID` when an upstream gateway already resolved the tenant.
2. Otherwise inspect the bearer token payload and read `tid` or `tenant_id`.
3. Convert the tenant ID into a tenant-specific app setting name such as `TENANT_TENANT_A_DB_URL`.
4. Pass that database URL into `azure-functions-db-python` so the injected reader targets the correct store.

```python
def resolve_tenant_id(req: func.HttpRequest) -> str:
    tenant_id = req.headers.get("X-Tenant-ID", "").strip()
    if tenant_id:
        return tenant_id

    authorization = req.headers.get("Authorization", "")
    if authorization.lower().startswith("bearer "):
        claims = decode_jwt_without_validation(authorization.split(" ", 1)[1])
        tenant_id = str(claims.get("tid") or claims.get("tenant_id") or "").strip()
        if tenant_id:
            return tenant_id

    raise ValueError("Missing tenant context.")


def resolve_tenant_db_url(req: func.HttpRequest) -> str:
    tenant_id = resolve_tenant_id(req)
    setting_name = f"TENANT_{normalize_tenant_key(tenant_id)}_DB_URL"
    db_url = os.getenv(setting_name, "").strip()
    if not db_url:
        raise ValueError(f"No database mapping configured for tenant '{tenant_id}'.")
    return db_url
```

The HTTP handler validates the JSON body, emits structured logs, and returns tenant-scoped rows from the isolated database.

## Run Locally

```bash
cd examples/security-and-tenancy/tenant_isolation
pip install -e ".[dev]"
cp local.settings.json.example local.settings.json
func start
```

Configure one setting per tenant:

```json
{
  "Values": {
    "TENANT_TENANT_A_DB_URL": "postgresql+psycopg://user:pass@localhost:5432/tenant_a",
    "TENANT_TENANT_B_DB_URL": "postgresql+psycopg://user:pass@localhost:5432/tenant_b"
  }
}
```

## Expected Output

```text
POST /api/tenant/invoices/query
X-Tenant-ID: tenant-a

-> 200 {
     "tenant_id": "tenant-a",
     "count": 2,
     "items": [
       {"invoice_id": "inv-100", "customer_id": "cust-7", "status": "open", "amount": 125.0},
       {"invoice_id": "inv-101", "customer_id": "cust-7", "status": "paid", "amount": 90.0}
     ]
   }
```

## Production Considerations

- **Isolation model**: tenant-specific databases provide stronger blast-radius reduction than shared tables, but increase provisioning and migration overhead.
- **Tenant registry**: move tenant-to-resource mapping to App Configuration, Key Vault, or a control-plane database when static app settings become hard to manage.
- **JWT handling**: the sample only decodes claims for routing. In production, validate signature, issuer, audience, and tenant policy before trusting the token.
- **Observability**: log tenant ID, request correlation, and selected resource without logging secrets or raw tokens.
- **Fail closed**: return an error when tenant context is missing or unmapped; never fall back to a default shared database.

## Related Links

- [Multi-tenant SaaS](https://learn.microsoft.com/en-us/azure/architecture/guide/multitenant/overview)
- [DB Input and Output Bindings](../data-and-pipelines/db-input-output.md)
- [JWT Bearer Validation](../apis-and-ingress/auth-jwt-validation.md)
