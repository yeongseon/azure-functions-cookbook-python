# IaC Reference Snippets

These are minimal infrastructure-as-code reference snippets for provisioning an Azure Function App. They are **concept illustrations**, not production-ready templates — adapt them to your environment, naming conventions, and security requirements.

!!! note
    The cookbook focuses on code patterns, not infrastructure management. For full IaC lifecycle tooling, see [Azure Developer CLI](https://learn.microsoft.com/azure/developer/azure-developer-cli/) or the [azd template library](https://azure.github.io/awesome-azd/).

---

## Bicep: Flex Consumption HTTP Function App (recommended)

[Flex Consumption](https://learn.microsoft.com/azure/azure-functions/flex-consumption-plan) is the
recommended serverless plan for new Python function apps: scale to zero, per-instance memory and
concurrency control, VNet integration, and always-current Python versions. Start here unless you have
a specific reason not to.

Two things differ from the classic Consumption templates below:

- The plan SKU is `FC1` / `FlexConsumption` and the plan is always Linux (`reserved: true`).
- Runtime, scale, and deployment settings move into `properties.functionAppConfig` on the site.
  Do **not** set `FUNCTIONS_WORKER_RUNTIME`, `FUNCTIONS_EXTENSION_VERSION`, `linuxFxVersion`, or
  `WEBSITE_RUN_FROM_PACKAGE` on a Flex app; the platform rejects or ignores them.

This snippet is adapted from the official
[`Azure-Samples/functions-quickstart-python-http-azd`](https://github.com/Azure-Samples/functions-quickstart-python-http-azd)
template, with the Azure Verified Modules inlined as plain resources so it reads as one file.

```bicep
@description('Base name for all resources')
param baseName string = 'myfuncapp'

@description('Azure region that supports Flex Consumption')
param location string = resourceGroup().location

@description('Python version for the Flex Consumption runtime')
@allowed(['3.11', '3.12', '3.13', '3.14'])
param pythonVersion string = '3.12'

@description('Per-instance memory in MB')
@allowed([512, 2048, 4096])
param instanceMemoryMB int = 2048

@description('Upper bound on scale-out')
param maximumInstanceCount int = 100

var deploymentContainerName = 'app-package'

// User-assigned managed identity used for storage and deployment access
resource identity 'Microsoft.ManagedIdentity/userAssignedIdentities@2023-01-31' = {
  name: '${baseName}-id'
  location: location
}

// Storage account: runtime state plus the deployment package container
resource storage 'Microsoft.Storage/storageAccounts@2023-05-01' = {
  name: '${baseName}store'
  location: location
  kind: 'StorageV2'
  sku: { name: 'Standard_LRS' }
  properties: {
    minimumTlsVersion: 'TLS1_2'
    allowBlobPublicAccess: false
    allowSharedKeyAccess: false
  }

  resource blobServices 'blobServices' = {
    name: 'default'

    resource deploymentContainer 'containers' = {
      name: deploymentContainerName
    }
  }
}

// Storage Blob Data Owner: required so the app can read and write its deployment package
resource blobOwner 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(storage.id, identity.id, 'StorageBlobDataOwner')
  scope: storage
  properties: {
    roleDefinitionId: subscriptionResourceId(
      'Microsoft.Authorization/roleDefinitions',
      'b7e6dc6d-f1e8-4753-8033-0f276bb0955b' // Storage Blob Data Owner
    )
    principalId: identity.properties.principalId
    principalType: 'ServicePrincipal'
  }
}

resource logAnalytics 'Microsoft.OperationalInsights/workspaces@2023-09-01' = {
  name: '${baseName}-logs'
  location: location
  properties: {
    retentionInDays: 30
    sku: { name: 'PerGB2018' }
  }
}

resource appInsights 'Microsoft.Insights/components@2020-02-02' = {
  name: '${baseName}-ai'
  location: location
  kind: 'web'
  properties: {
    Application_Type: 'web'
    WorkspaceResourceId: logAnalytics.id
  }
}

// Flex Consumption plan: SKU FC1, always Linux (reserved)
resource plan 'Microsoft.Web/serverfarms@2023-12-01' = {
  name: '${baseName}-plan'
  location: location
  kind: 'functionapp'
  sku: {
    name: 'FC1'
    tier: 'FlexConsumption'
  }
  properties: {
    reserved: true
  }
}

// Flex Consumption function app: runtime and scale live in functionAppConfig,
// not in siteConfig.appSettings
resource functionApp 'Microsoft.Web/sites@2023-12-01' = {
  name: baseName
  location: location
  kind: 'functionapp,linux'
  identity: {
    type: 'UserAssigned'
    userAssignedIdentities: { '${identity.id}': {} }
  }
  properties: {
    serverFarmId: plan.id
    functionAppConfig: {
      deployment: {
        storage: {
          type: 'blobContainer'
          value: '${storage.properties.primaryEndpoints.blob}${deploymentContainerName}'
          authentication: {
            type: 'UserAssignedIdentity'
            userAssignedIdentityResourceId: identity.id
          }
        }
      }
      scaleAndConcurrency: {
        instanceMemoryMB: instanceMemoryMB
        maximumInstanceCount: maximumInstanceCount
      }
      runtime: {
        name: 'python'
        version: pythonVersion
      }
    }
    siteConfig: {
      appSettings: [
        { name: 'AzureWebJobsStorage__blobServiceUri', value: storage.properties.primaryEndpoints.blob }
        { name: 'AzureWebJobsStorage__credential', value: 'managedidentity' }
        { name: 'AzureWebJobsStorage__clientId', value: identity.properties.clientId }
        { name: 'APPLICATIONINSIGHTS_CONNECTION_STRING', value: appInsights.properties.ConnectionString }
      ]
    }
  }
  dependsOn: [blobOwner]
}

output functionAppName string = functionApp.name
output functionAppHostname string = functionApp.properties.defaultHostName
```

Deploy with:

```bash
az group create --name my-rg --location eastus
az deployment group create \
  --resource-group my-rg \
  --template-file main.bicep \
  --parameters baseName=myfuncapp pythonVersion=3.12
```

Then publish code with `func azure functionapp publish myfuncapp` or `azd deploy`.

!!! note "Region availability"
    Flex Consumption is not available in every region. Check the current list with
    `az functionapp list-flexconsumption-locations --output table` before choosing `location`.

---

## Bicep: Minimal HTTP Function App (classic Consumption)

!!! warning "Linux Consumption is retiring"
    The classic Linux Consumption plan (`Y1` / `Dynamic`) retires on **30 September 2028** and
    receives no Python versions beyond 3.12. Use it only for existing apps; prefer the Flex
    Consumption snippet above for anything new. See
    [Azure Functions supported languages](https://learn.microsoft.com/azure/azure-functions/supported-languages)
    for the current runtime support matrix.

Provisions a Storage Account, App Service Plan (classic Linux Consumption), and Function App wired for the Python v2 model.

```bicep
@description('Base name for all resources')
param baseName string = 'myfuncapp'

@description('Azure region')
param location string = resourceGroup().location

// Storage Account (required for Functions runtime)
resource storage 'Microsoft.Storage/storageAccounts@2023-01-01' = {
  name: '${baseName}store'
  location: location
  kind: 'StorageV2'
  sku: { name: 'Standard_LRS' }
  properties: {
    minimumTlsVersion: 'TLS1_2'
    allowBlobPublicAccess: false
  }
}

// Classic Linux Consumption plan
resource plan 'Microsoft.Web/serverfarms@2023-01-01' = {
  name: '${baseName}-plan'
  location: location
  kind: 'linux'
  sku: { name: 'Y1', tier: 'Dynamic' }
  properties: {
    reserved: true
  }
}

// Function App
resource functionApp 'Microsoft.Web/sites@2023-01-01' = {
  name: baseName
  location: location
  kind: 'functionapp,linux'
  properties: {
    serverFarmId: plan.id
    siteConfig: {
      linuxFxVersion: 'Python|3.12'
      appSettings: [
        { name: 'FUNCTIONS_EXTENSION_VERSION', value: '~4' }
        { name: 'FUNCTIONS_WORKER_RUNTIME', value: 'python' }
        {
          name: 'AzureWebJobsStorage'
          value: 'DefaultEndpointsProtocol=https;AccountName=${storage.name};AccountKey=${storage.listKeys().keys[0].value}'
        }
        { name: 'SCM_DO_BUILD_DURING_DEPLOYMENT', value: '1' }
      ]
    }
  }
}

output functionAppName string = functionApp.name
output functionAppHostname string = functionApp.properties.defaultHostName
```

Deploy with:

```bash
az group create --name my-rg --location eastus
az deployment group create \
  --resource-group my-rg \
  --template-file main.bicep \
  --parameters baseName=myfuncapp
```

---

## Bicep: Managed Identity variant (classic Consumption)

Removes the storage connection string. Uses a User-Assigned Managed Identity with role assignments instead.

```bicep
@description('Base name for all resources')
param baseName string = 'myfuncapp'
param location string = resourceGroup().location

// User-Assigned Managed Identity
resource identity 'Microsoft.ManagedIdentity/userAssignedIdentities@2023-01-31' = {
  name: '${baseName}-id'
  location: location
}

// Storage Account
resource storage 'Microsoft.Storage/storageAccounts@2023-01-01' = {
  name: '${baseName}store'
  location: location
  kind: 'StorageV2'
  sku: { name: 'Standard_LRS' }
  properties: {
    minimumTlsVersion: 'TLS1_2'
    allowBlobPublicAccess: false
  }
}

// Role assignment: Storage Blob Data Contributor
resource roleAssignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(storage.id, identity.id, 'StorageBlobDataContributor')
  scope: storage
  properties: {
    roleDefinitionId: subscriptionResourceId(
      'Microsoft.Authorization/roleDefinitions',
      'ba92f5b4-2d11-453d-a403-e96b0029c9fe' // Storage Blob Data Contributor
    )
    principalId: identity.properties.principalId
    principalType: 'ServicePrincipal'
  }
}

// Classic Linux Consumption plan
resource plan 'Microsoft.Web/serverfarms@2023-01-01' = {
  name: '${baseName}-plan'
  location: location
  kind: 'linux'
  sku: { name: 'Y1', tier: 'Dynamic' }
  properties: {
    reserved: true
  }
}

// Function App (identity-based storage)
resource functionApp 'Microsoft.Web/sites@2023-01-01' = {
  name: baseName
  location: location
  kind: 'functionapp,linux'
  identity: {
    type: 'UserAssigned'
    userAssignedIdentities: { '${identity.id}': {} }
  }
  properties: {
    serverFarmId: plan.id
    siteConfig: {
      linuxFxVersion: 'Python|3.12'
      appSettings: [
        { name: 'FUNCTIONS_EXTENSION_VERSION', value: '~4' }
        { name: 'FUNCTIONS_WORKER_RUNTIME', value: 'python' }
        {
          name: 'AzureWebJobsStorage__blobServiceUri'
          value: storage.properties.primaryEndpoints.blob
        }
        {
          name: 'AzureWebJobsStorage__queueServiceUri'
          value: storage.properties.primaryEndpoints.queue
        }
        {
          name: 'AzureWebJobsStorage__credential'
          value: 'managedidentity'
        }
        {
          name: 'AzureWebJobsStorage__clientId'
          value: identity.properties.clientId
        }
        { name: 'SCM_DO_BUILD_DURING_DEPLOYMENT', value: '1' }
      ]
    }
  }
  dependsOn: [roleAssignment]
}
```

!!! tip "See also"
    The [Managed Identity (Storage)](../patterns/security-and-tenancy/managed-identity-storage.md) and [Managed Identity (Service Bus)](../patterns/security-and-tenancy/managed-identity-servicebus.md) patterns explain the app-level configuration in detail.

---

## When to use IaC for Functions

| Situation | Recommendation |
|-----------|---------------|
| Personal project / prototype | Azure Portal or `az functionapp create --flexconsumption-location <region>` |
| Team project, manual infra acceptable | Azure CLI scripts in a `scripts/` directory |
| CI/CD-driven, reproducible environments | Bicep or Terraform (Flex Consumption snippet above as the starting point) |
| Multi-service app with Functions as one component | Azure Developer CLI (`azd`) with an `azure.yaml` template |

## Related pages

- [Hosting Plans and Scale](../foundations/hosting-and-scale.md)
- [Deployment Patterns](deployment-patterns.md)
- [Identity-Based Connections](identity-based-connections.md)
- [Foundations](../foundations/index.md)
