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

All cookbook examples use `pyproject.toml` (hatch/hatchling) as the canonical packaging format. This aligns with modern Python tooling and keeps dependency management in one place.

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
          python-version: "3.12"
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

## Hosting plans: Flex Consumption vs Premium vs Dedicated

| Plan | Cost model | Cold start profile | Scale behavior | Best fit |
| --- | --- | --- | --- | --- |
| **Flex Consumption** (recommended) | Pay per execution, plus any always-ready instances | Reduced; always-ready instances remove it for a baseline | Event-driven scale to zero with a configurable instance ceiling | New Python apps, including ones needing VNet |
| Consumption (classic Linux) | Pay per execution | Can be noticeable | Automatic elastic scaling | Existing apps only; retires 30 September 2028 |
| Premium | Pre-warmed + execution cost | Reduced cold starts | Elastic with pre-warmed instances | Apps needing App Service specific networking features |
| Dedicated (App Service) | Fixed instance cost | No serverless cold start pattern | Manual/auto scale by plan | Predictable steady traffic |

Selection guidance:

- Start with Flex Consumption for new apps: scale to zero, VNet integration, configurable
  per-instance memory, and current Python versions.
- Treat classic Linux Consumption as migrate-away. It receives no Python versions beyond 3.12 and
  retires on 30 September 2028. See
  [Migrate Consumption plan apps to Flex Consumption](https://learn.microsoft.com/azure/azure-functions/migration/migrate-plan-consumption-to-flex).
- Move to Premium only when you need App Service features Flex Consumption does not offer.
- Use Dedicated when workload is steady and you want full App Service control.

See [Hosting Plans and Scale](../foundations/hosting-and-scale.md) for the full comparison and
[IaC Reference Snippets](iac-snippets.md) for a deployable Flex Consumption Bicep template.

## Deployment slots

Slots provide safer releases by separating staging from production runtime.

!!! warning "Flex Consumption has no deployment slots"
    Deployment slots are not available on Flex Consumption. If you deploy there, replace the
    slot-swap release strategy below with a side-by-side app plus traffic cutover (Front Door,
    APIM, or DNS), and keep the previous app running until smoke tests pass.

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

On Flex Consumption, drop `FUNCTIONS_EXTENSION_VERSION` and `FUNCTIONS_WORKER_RUNTIME`: the
language and version live in `properties.functionAppConfig.runtime` on the site resource, and
the platform rejects the legacy settings.

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

- [ ] Hosting plan chosen deliberately (Flex Consumption unless a constraint says otherwise).
- [ ] Runtime version pinned (`~4` on classic plans, `functionAppConfig.runtime` on Flex) and Python version aligned.
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
- Flex Consumption plan: https://learn.microsoft.com/azure/azure-functions/flex-consumption-plan
- Migrate Consumption apps to Flex Consumption: https://learn.microsoft.com/azure/azure-functions/migration/migrate-plan-consumption-to-flex
- Deployment slots for Azure Functions: https://learn.microsoft.com/azure/azure-functions/functions-deployment-slots
- Azure Developer CLI docs: https://learn.microsoft.com/azure/developer/azure-developer-cli/
- GitHub Actions for Azure Functions: https://learn.microsoft.com/azure/azure-functions/functions-how-to-github-actions

## Related pages

- [Identity-Based Connections](identity-based-connections.md)
- [IaC Reference Snippets](iac-snippets.md)
- [Hosting Plans and Scale](../foundations/hosting-and-scale.md)
- [Python v2 Programming Model](../foundations/execution-model.md)
- [Triggers and Bindings Overview](../foundations/triggers-bindings-overview.md)
- [Durable Functions Overview](../reference/durable.md)
