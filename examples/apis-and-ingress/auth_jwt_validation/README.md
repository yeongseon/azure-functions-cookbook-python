# auth_jwt_validation

JWT Bearer token validation with claim-based access control for Azure Functions.

## Prerequisites

- Python 3.10+
- [Azure Functions Core Tools v4](https://learn.microsoft.com/azure/azure-functions/functions-run-local)
- [Azurite](https://learn.microsoft.com/azure/storage/common/storage-use-azurite) (local Storage emulator)
- An Azure AD (Entra ID) app registration

## Environment Variables

| Variable | Purpose | Example |
|----------|---------|---------|
| `AZURE_TENANT_ID` | Azure AD tenant ID for JWKS discovery | `00000000-0000-0000-0000-000000000000` |
| `AZURE_CLIENT_ID` | Application (client) ID used as JWT audience | `11111111-1111-1111-1111-111111111111` |

Set in `local.settings.json` under `Values`. Copy `local.settings.json.example` as a starting template.

## What It Demonstrates

- Extracting Bearer tokens from the `Authorization` header
- Validating JWTs against Azure AD JWKS endpoint using RS256
- Claim-based access control (checking `roles` claim for `api.read`)
- Returning 401 for missing/invalid tokens and 403 for insufficient claims

## Run Locally

```bash
cd examples/http/auth_jwt_validation
python -m venv .venv
source .venv/bin/activate
pip install -e .
cp local.settings.json.example local.settings.json
# Edit local.settings.json with your Azure AD tenant and client IDs
func start
```

## Expected Output Example

```bash
# With a valid Azure AD token:
curl -s "http://localhost:7071/api/auth/profile" \
  -H "Authorization: Bearer <your-jwt-token>" | python -m json.tool
```

```json
{
    "subject": "abc123",
    "name": "Alice",
    "email": "alice@example.com",
    "claims": {
        "sub": "abc123",
        "name": "Alice",
        "email": "alice@example.com",
        "roles": "api.read"
    }
}
```
