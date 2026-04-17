# tenant_isolation

HTTP recipe for resolving tenant context from `X-Tenant-ID` or a bearer token claim,
then querying a tenant-specific database with `azure-functions-db`.

## Integrations

- `azure-functions-db`
- `azure-functions-validation`
- `azure-functions-openapi`
- `azure-functions-logging`

## Environment Variables

| Variable | Purpose | Example |
|----------|---------|---------|
| `TENANT_TENANT_A_DB_URL` | Tenant A SQLAlchemy connection string | `postgresql+psycopg://user:pass@localhost:5432/tenant_a` |
| `TENANT_TENANT_B_DB_URL` | Tenant B SQLAlchemy connection string | `postgresql+psycopg://user:pass@localhost:5432/tenant_b` |

The function converts `tenant-a` into `TENANT_TENANT_A_DB_URL`.

## Run Locally

```bash
cd examples/security-and-tenancy/tenant_isolation
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp local.settings.json.example local.settings.json
func start
```

## Request Example

```bash
curl -s -X POST "http://localhost:7071/api/tenant/invoices/query" \
  -H "Content-Type: application/json" \
  -H "X-Tenant-ID: tenant-a" \
  -d '{"customer_id":"cust-7","limit":2}' | python -m json.tool
```

## Expected Response

```json
{
  "tenant_id": "tenant-a",
  "count": 2,
  "items": [
    {
      "invoice_id": "inv-100",
      "customer_id": "cust-7",
      "status": "open",
      "amount": 125.0
    },
    {
      "invoice_id": "inv-101",
      "customer_id": "cust-7",
      "status": "paid",
      "amount": 90.0
    }
  ]
}
```

## Notes

- The sample decodes JWT claims only to extract tenant context; production apps should validate token signature, issuer, and audience.
- Keep a separate database per tenant to avoid accidental cross-tenant reads.
- Return an error when tenant mapping is missing instead of falling back to a shared default.
