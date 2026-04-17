# IaC Reference Snippets

These are minimal infrastructure-as-code reference snippets for provisioning an Azure Function App. They are **concept illustrations**, not production-ready templates — adapt them to your environment, naming conventions, and security requirements.

!!! note
    The cookbook focuses on code patterns, not infrastructure management. For full IaC lifecycle tooling, see [Azure Developer CLI](https://learn.microsoft.com/azure/developer/azure-developer-cli/) or the [azd template library](https://azure.github.io/awesome-azd/).

---

## Bicep: Minimal HTTP Function App

Provisions a Storage Account, App Service Plan (Consumption), and Function App wired for Python 3.11 v2 model.

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

// Consumption plan
resource plan 'Microsoft.Web/serverfarms@2023-01-01' = {
  name: '${baseName}-plan'
  location: location
  kind: 'functionapp'
  sku: { name: 'Y1', tier: 'Dynamic' }
  properties: {}
}

// Function App
resource functionApp 'Microsoft.Web/sites@2023-01-01' = {
  name: baseName
  location: location
  kind: 'functionapp'
  properties: {
    serverFarmId: plan.id
    siteConfig: {
      pythonVersion: '3.11'
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

## Bicep: Managed Identity variant

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

// Consumption plan
resource plan 'Microsoft.Web/serverfarms@2023-01-01' = {
  name: '${baseName}-plan'
  location: location
  kind: 'functionapp'
  sku: { name: 'Y1', tier: 'Dynamic' }
  properties: {}
}

// Function App (identity-based storage)
resource functionApp 'Microsoft.Web/sites@2023-01-01' = {
  name: baseName
  location: location
  kind: 'functionapp'
  identity: {
    type: 'UserAssigned'
    userAssignedIdentities: { '${identity.id}': {} }
  }
  properties: {
    serverFarmId: plan.id
    siteConfig: {
      pythonVersion: '3.11'
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
| Personal project / prototype | Azure Portal or `az functionapp create` one-liner |
| Team project, manual infra acceptable | Azure CLI scripts in a `scripts/` directory |
| CI/CD-driven, reproducible environments | Bicep or Terraform (snippets above as starting point) |
| Multi-service app with Functions as one component | Azure Developer CLI (`azd`) with an `azure.yaml` template |

## Related pages

- [Deployment Patterns](deployment-patterns.md)
- [Identity-Based Connections](identity-based-connections.md)
- [Foundations](../foundations/index.md)
