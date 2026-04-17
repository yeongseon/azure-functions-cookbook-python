# auth_multitenant

Multi-tenant access control with tenant allowlist for Azure Functions.

## Prerequisites

- Python 3.10+
- [Azure Functions Core Tools v4](https://learn.microsoft.com/azure/azure-functions/functions-run-local)
- [Azurite](https://learn.microsoft.com/azure/storage/common/storage-use-azurite) (local Storage emulator)
- App Service Authentication (EasyAuth) enabled on the Function App

## Environment Variables

| Variable | Purpose | Example |
|----------|---------|---------|
| `ALLOWED_TENANT_IDS` | Comma-separated list of allowed Azure AD tenant IDs | `tenant-id-1,tenant-id-2` |

Set in `local.settings.json` under `Values`. Copy `local.settings.json.example` as a starting template.

## What It Demonstrates

- Decoding the `X-MS-CLIENT-PRINCIPAL` header (base64-encoded JSON)
- Extracting the tenant ID (`tid` claim) from the principal
- Checking tenant ID against an allowlist from environment variable
- Returning 401 for unauthenticated requests and 403 for unauthorized tenants

## Run Locally

```bash
cd examples/http/auth_multitenant
python -m venv .venv
source .venv/bin/activate
pip install -e .
cp local.settings.json.example local.settings.json
func start
```

> **Note:** Locally, the `X-MS-CLIENT-PRINCIPAL` header is not injected by
> App Service. You can test by manually passing a base64-encoded principal
> in the header (see Expected Output below).

## Expected Output Example

```bash
# Encode a test principal with tenant ID
PRINCIPAL=$(echo -n '{"auth_typ":"aad","name_typ":"http://schemas.xmlsoap.org/ws/2005/05/identity/claims/name","role_typ":"http://schemas.microsoft.com/ws/2008/06/identity/claims/role","claims":[{"typ":"tid","val":"tenant-id-1"},{"typ":"http://schemas.xmlsoap.org/ws/2005/05/identity/claims/nameidentifier","val":"user-1"},{"typ":"name","val":"Alice"}]}' | base64)

# Access tenant-scoped data (tenant-id-1 is in the allowlist)
curl -s "http://localhost:7071/api/auth/data" \
  -H "X-MS-CLIENT-PRINCIPAL: $PRINCIPAL" | python -m json.tool
```

```json
{
    "message": "Access granted.",
    "tenant_id": "tenant-id-1",
    "user_id": "user-1",
    "identity_provider": "aad"
}
```
