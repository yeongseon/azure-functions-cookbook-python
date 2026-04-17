param baseName string = 'servicebus-topic-fanout-func'
param location string = resourceGroup().location

var suffix = take(uniqueString(resourceGroup().id, baseName), 6)
var storageName = take('${replace(toLower(baseName), '-', '')}${suffix}', 24)
var functionAppName = '${baseName}-${suffix}'
var serviceBusNamespaceName = '${baseName}-sb-${suffix}'

resource storage 'Microsoft.Storage/storageAccounts@2023-01-01' = {
  name: storageName
  location: location
  kind: 'StorageV2'
  sku: { name: 'Standard_LRS' }
  properties: { minimumTlsVersion: 'TLS1_2', allowBlobPublicAccess: false }
}

resource serviceBus 'Microsoft.ServiceBus/namespaces@2022-10-01-preview' = {
  name: serviceBusNamespaceName
  location: location
  sku: { name: 'Standard', tier: 'Standard' }
}

resource topic 'Microsoft.ServiceBus/namespaces/topics@2022-10-01-preview' = {
  name: '${serviceBus.name}/orders'
  properties: {}
}

resource emailSub 'Microsoft.ServiceBus/namespaces/topics/subscriptions@2022-10-01-preview' = {
  name: '${serviceBus.name}/orders/email'
  properties: {}
}

resource inventorySub 'Microsoft.ServiceBus/namespaces/topics/subscriptions@2022-10-01-preview' = {
  name: '${serviceBus.name}/orders/inventory'
  properties: {}
}

resource analyticsSub 'Microsoft.ServiceBus/namespaces/topics/subscriptions@2022-10-01-preview' = {
  name: '${serviceBus.name}/orders/analytics'
  properties: {}
}

resource serviceBusAuth 'Microsoft.ServiceBus/namespaces/AuthorizationRules@2022-10-01-preview' = {
  name: '${serviceBus.name}/RootManageSharedAccessKey'
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
        { name: 'ServiceBusConnection', value: listKeys(serviceBusAuth.id, serviceBusAuth.apiVersion).primaryConnectionString }
        { name: 'SCM_DO_BUILD_DURING_DEPLOYMENT', value: '1' }
      ]
    }
  }
}

output functionAppName string = functionApp.name
