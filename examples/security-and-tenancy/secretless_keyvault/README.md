# Secretless Key Vault

📖 [Full documentation](https://yeongseon.github.io/azure-functions-cookbook-python/patterns/security-and-tenancy/secretless-keyvault/)

HTTP-triggered Azure Function that reads secrets from environment variables populated by Azure Key Vault
references. The function uses standard environment access and `azure_functions_logging` only.

## Prerequisites

- Python 3.10+
- [Azure Functions Core Tools v4](https://learn.microsoft.com/azure/azure-functions/functions-run-local)
- An Azure Function App with managed identity enabled
- An Azure Key Vault secret such as `demo-api-key`

## Integration Matrix

| Concern | Used | Notes |
|---------|------|-------|
| Logging | Yes | Structured logs via `azure_functions_logging` |
| Key Vault SDK | No | The platform resolves app settings before code runs |

## Environment Variables

| Variable | Purpose | Example |
|----------|---------|---------|
| `UPSTREAM_APP_NAME` | Friendly upstream service name for logs and response payloads | `sample-upstream` |
| `UPSTREAM_SECRET_NAME` | Secret label reported in logs and responses | `demo-api-key` |
| `UPSTREAM_API_KEY` | Secret value consumed by code | `@Microsoft.KeyVault(SecretUri=https://<vault>.vault.azure.net/secrets/demo-api-key/)` |

For local development, `UPSTREAM_API_KEY` can be a placeholder string in `local.settings.json`.
In Azure, configure the same setting as a Key Vault reference.

## Key Vault Reference Pattern

```text
UPSTREAM_API_KEY=@Microsoft.KeyVault(SecretUri=https://<vault-name>.vault.azure.net/secrets/demo-api-key/)
```

The platform resolves the reference through the Function App's managed identity before the Python code reads
`os.getenv("UPSTREAM_API_KEY")`.

This means the function stays secretless from an SDK perspective: it only reads a normal environment
variable and never requests Key Vault directly.

## Run Locally

```bash
cd examples/security-and-tenancy/secretless_keyvault
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
cp local.settings.json.example local.settings.json
func start
```

## Try It

```bash
curl "http://localhost:7071/api/secretless-keyvault?code=<function-key>"
```

## Expected Output

```json
{"app": "sample-upstream", "secretName": "demo-api-key", "secretLoaded": true, "source": "environment-variable", "usesSdk": false}
```

## Notes

- The function never logs the secret value.
- Key Vault reference resolution happens at startup or config refresh time, not per request.
- Missing or broken references appear as configuration problems, not SDK exceptions in code.
- For setup details, see [Key Vault references](https://learn.microsoft.com/en-us/azure/app-service/app-service-key-vault-references).
