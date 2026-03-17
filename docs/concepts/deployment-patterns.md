# Deployment Patterns

This page describes practical deployment patterns for Azure Functions Python v2 apps, including Azure CLI, GitHub Actions, Azure Developer CLI (`azd`), hosting plan choices, slots, and configuration management.

## Deployment goals

A reliable deployment process should provide:

- Repeatability across environments.
- Clear separation of code and configuration.
- Safe rollback path.
- Minimal manual steps.
- Fast feedback on failures.

## Build artifact strategy

The cookbook examples use `pyproject.toml` (hatch/hatchling) as the canonical packaging format. This aligns with modern Python tooling and avoids the dual-maintenance overhead of keeping `requirements.txt` in sync with `pyproject.toml`.

**Recommended path: `pyproject.toml` + remote build**

1. Define dependencies in `pyproject.toml` under `[project] dependencies`.
2. Let Azure Functions remote build resolve them during deployment (no manual pip step needed).
3. Deploy via zip package to the target Function App.

Important files:

- `host.json`
- `function_app.py` and Python modules
- `pyproject.toml` (dependency declaration)
- Optional `local.settings.json` only for local dev (never deploy secrets from local file)

## Pattern 1: Azure CLI deployment

Azure CLI is ideal for direct, scriptable deployments from terminal or simple CI jobs.

### Typical flow

```bash
az login
az account set --subscription <subscription-id>

az functionapp deployment source config-zip \
  --resource-group <rg> \
  --name <function-app-name> \
  --src <artifact.zip>
```

### Pros

- Quick setup.
- Easy to script in Bash/PowerShell.
- Good for operational runbooks.

### Cons

- Requires your own artifact/versioning discipline.
- Less opinionated pipeline governance.

## Pattern 2: GitHub Actions CI/CD

GitHub Actions is the most common production CI/CD path for repository-hosted apps.

### Recommended workflow stages

1. Trigger on pull request and push to protected branches.
2. Run lint/tests.
3. Build/dependency restore.
4. Publish artifact.
5. Deploy to staging slot.
6. Run smoke checks.
7. Swap slot for production release.

### Minimal workflow sketch

```yaml
name: deploy-functions

on:
  push:
    branches: [main]

jobs:
  build-and-deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - run: pip install -e .
      - run: pytest -q
      - uses: Azure/functions-action@v1
        with:
          app-name: ${{ secrets.AZURE_FUNCTIONAPP_NAME }}
          package: .
          publish-profile: ${{ secrets.AZURE_FUNCTIONAPP_PUBLISH_PROFILE }}
```

Production hardening recommendations:

- Use OpenID Connect (OIDC) + federated credentials instead of publish profiles.
- Restrict environment approvals for production deployment.
- Require successful checks before merge.

## Pattern 3: Azure Developer CLI (`azd`)

`azd` is useful when you want environment provisioning and app deployment managed together using infrastructure-as-code templates.

### Typical flow

```bash
azd auth login
azd init
azd up
```

What `azd up` usually handles:

- Provision resource group and services.
- Deploy function app code.
- Apply environment variables from `azd` environment.

When to choose `azd`:

- Greenfield projects.
- Teams standardizing app + infra lifecycle.
- Multi-service solutions where Functions is one component.

## Hosting plans: Consumption vs Premium vs Dedicated

| Plan | Cost model | Cold start profile | Scale behavior | Best fit |
| --- | --- | --- | --- | --- |
| Consumption | Pay per execution | Can be noticeable | Automatic elastic scaling | Event-driven, spiky workloads |
| Premium | Pre-warmed + execution cost | Reduced cold starts | Elastic with pre-warmed instances | Latency-sensitive and bursty workloads |
| Dedicated (App Service) | Fixed instance cost | No serverless cold start pattern | Manual/auto scale by plan | Predictable steady traffic |

Selection guidance:

- Start with Consumption for low/medium traffic asynchronous patterns.
- Move to Premium when startup latency matters or VNET/performance needs increase.
- Use Dedicated when workload is steady and you want full App Service control.

## Deployment slots

Slots provide safer releases by separating staging from production runtime.

### Recommended slot workflow

1. Deploy build artifact to `staging` slot.
2. Run smoke tests against staging endpoint.
3. Validate app settings and managed identity behavior.
4. Swap `staging` -> `production`.
5. Monitor immediately after swap.

### Slot considerations

- Mark truly environment-specific settings as slot settings.
- Validate trigger behavior after swap (especially queue/service bus consumers).
- Keep rollback simple by swapping back if needed.

## Configuration management patterns

Treat configuration as versioned, reviewed deployment input.

### Principles

- Keep secrets out of source control.
- Use Key Vault references or managed identity where possible.
- Separate per-environment values (`dev`, `test`, `prod`).
- Validate required settings on startup.

### Typical categories

- Runtime settings (`FUNCTIONS_EXTENSION_VERSION`, worker settings).
- Binding connection prefixes and identity URI suffixes.
- Business toggles and feature flags.
- Observability settings (`APPLICATIONINSIGHTS_CONNECTION_STRING`).

### Example app settings model

```text
FUNCTIONS_EXTENSION_VERSION=~4
AzureWebJobsStorage__blobServiceUri=https://mystorage.blob.core.windows.net
AzureWebJobsStorage__queueServiceUri=https://mystorage.queue.core.windows.net
ServiceBusConn__fullyQualifiedNamespace=my-namespace.servicebus.windows.net
APP_ENV=production
```

## Zero-downtime and rollback strategy

- Prefer slot-based blue/green style releases.
- Keep previous known-good artifact for quick redeploy.
- Use health checks before and after swap.
- Automate rollback trigger on critical smoke-test failure.

## Observability after deployment

Monitor first minutes after release for:

- Trigger listener startup errors.
- Authorization failures (RBAC/identity).
- Dependency import/runtime mismatches.
- Elevated retries, dead-letters, or poison queues.

Key telemetry signals:

- Function invocation failure rate.
- End-to-end latency for HTTP and workflow completion.
- Queue backlog growth and age.
- Host restart frequency.

## CI/CD security recommendations

- Use OIDC to Azure instead of long-lived deployment secrets.
- Scope service principals to minimum required resources.
- Protect main branch with required reviews/checks.
- Pin GitHub Action versions where possible.
- Scan dependencies and container/base images if used.

## Reference architecture patterns

### Pattern A: Simple production pipeline

- PR checks (lint + tests)
- Merge to main
- Build and deploy to staging slot
- Smoke test
- Swap to production

### Pattern B: Environment promotion

- Deploy same artifact to `dev`
- Promote unchanged artifact to `test`
- Promote unchanged artifact to `prod`

This reduces "works in dev but not in prod" differences.

## Common deployment pitfalls

- Deploying from local machine without immutable artifact trail.
- Missing app settings in production.
- Using connection strings where identity was intended.
- Not validating extension/runtime compatibility.
- Swapping slots with incorrect slot-sticky settings.

## Practical checklist

- [ ] Runtime version pinned (`~4`) and Python version aligned.
- [ ] Tests pass before deployment.
- [ ] Artifact is immutable and traceable to commit.
- [ ] Identity and RBAC verified for all triggers/bindings.
- [ ] Deployment to staging slot completed.
- [ ] Smoke tests pass before swap.
- [ ] Rollback procedure documented and rehearsed.

## Microsoft Learn references

- Deploy Azure Functions from package: https://learn.microsoft.com/azure/azure-functions/run-functions-from-deployment-package
- Continuous deployment for Azure Functions: https://learn.microsoft.com/azure/azure-functions/functions-continuous-deployment
- Azure Functions hosting options: https://learn.microsoft.com/azure/azure-functions/functions-scale
- Deployment slots for Azure Functions: https://learn.microsoft.com/azure/azure-functions/functions-deployment-slots
- Azure Developer CLI docs: https://learn.microsoft.com/azure/developer/azure-developer-cli/
- GitHub Actions for Azure Functions: https://learn.microsoft.com/azure/azure-functions/functions-how-to-github-actions

## Related pages

- [Identity-Based Connections](identity-based-connections.md)
- [Python v2 Programming Model](python-v2-programming-model.md)
- [Triggers and Bindings Overview](triggers-and-bindings-overview.md)
- [Durable Functions Overview](durable-functions-overview.md)
