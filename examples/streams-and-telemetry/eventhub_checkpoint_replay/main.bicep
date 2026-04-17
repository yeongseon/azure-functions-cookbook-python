param baseName string = 'eventhub-checkpoint-replay-func'
param location string = resourceGroup().location

var suffix = take(uniqueString(resourceGroup().id, baseName), 6)
var storageName = take('${replace(toLower(baseName), '-', '')}${suffix}', 24)
var functionAppName = '${baseName}-${suffix}'
var eventHubNamespaceName = '${baseName}-eh-${suffix}'

resource storage 'Microsoft.Storage/storageAccounts@2023-01-01' = {
  name: storageName
  location: location
  kind: 'StorageV2'
  sku: { name: 'Standard_LRS' }
  properties: { minimumTlsVersion: 'TLS1_2', allowBlobPublicAccess: false }
}

resource namespace 'Microsoft.EventHub/namespaces@2022-10-01-preview' = {
  name: eventHubNamespaceName
  location: location
  sku: { name: 'Standard', tier: 'Standard' }
}

resource hub 'Microsoft.EventHub/namespaces/eventhubs@2022-10-01-preview' = {
  name: '${namespace.name}/telemetry'
  properties: { partitionCount: 2, messageRetentionInDays: 1 }
}

resource consumerGroup 'Microsoft.EventHub/namespaces/eventhubs/consumergroups@2022-10-01-preview' = {
  name: '${namespace.name}/telemetry/checkpoint-replay'
  properties: {}
}

resource auth 'Microsoft.EventHub/namespaces/AuthorizationRules@2022-10-01-preview' = {
  name: '${namespace.name}/RootManageSharedAccessKey'
  properties: { rights: ['Listen', 'Send', 'Manage'] }
}

resource plan 'Microsoft.Web/serverfarms@2023-01-01' = {
  name: '${baseName}-plan'
  location: location
  kind: 'functionapp'
  sku: { name: 'Y1', tier: 'Dynamic' }
}

resource functionApp 'Microsoft.Web/sites@2023-01-01' = {
  name: functionAppName
  location: location
  kind: 'functionapp'
  properties: {
    serverFarmId: plan.id
    siteConfig: {
      pythonVersion: '3.11'
      appSettings: [
        { name: 'FUNCTIONS_EXTENSION_VERSION', value: '~4' }
        { name: 'FUNCTIONS_WORKER_RUNTIME', value: 'python' }
        { name: 'AzureWebJobsStorage', value: 'DefaultEndpointsProtocol=https;AccountName=${storage.name};AccountKey=${storage.listKeys().keys[0].value};EndpointSuffix=${environment().suffixes.storage}' }
        { name: 'EventHubConnection', value: listKeys(auth.id, auth.apiVersion).primaryConnectionString }
        { name: 'EVENTHUB_NAME', value: 'telemetry' }
        { name: 'SCM_DO_BUILD_DURING_DEPLOYMENT', value: '1' }
      ]
    }
  }
}

output functionAppName string = functionApp.name
