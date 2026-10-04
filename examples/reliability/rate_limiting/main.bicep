@description('Base name for all resources')
param baseName string = 'ratelimiting'

@description('Azure region')
param location string = resourceGroup().location

var uniqueSuffix = toLower(uniqueString(resourceGroup().id, baseName))
var storageAccountName = 'st${substring(uniqueSuffix, 0, 22)}'
var functionAppName = '${baseName}-${substring(uniqueSuffix, 0, 6)}'

resource storage 'Microsoft.Storage/storageAccounts@2023-01-01' = {
  name: storageAccountName
  location: location
  kind: 'StorageV2'
  sku: { name: 'Standard_LRS' }
  properties: {
    minimumTlsVersion: 'TLS1_2'
    allowBlobPublicAccess: false
  }
}

resource plan 'Microsoft.Web/serverfarms@2023-01-01' = {
  name: '${baseName}-plan'
  location: location
  kind: 'linux'
  sku: { name: 'Y1', tier: 'Dynamic' }
  properties: {}
  properties: {
    reserved: true
  }
}

resource redis 'Microsoft.Cache/redis@2023-08-01' = {
  name: '${baseName}-redis'
  location: location
  properties: {
    enableNonSslPort: false
    minimumTlsVersion: '1.2'
  }
  sku: {
    name: 'Basic'
    family: 'C'
    capacity: 0
  }
}

resource functionApp 'Microsoft.Web/sites@2023-01-01' = {
  name: functionAppName
  location: location
  kind: 'functionapp,linux'
  httpsOnly: true
  properties: {
    serverFarmId: plan.id
    reserved: true
    siteConfig: {
      linuxFxVersion: 'Python|3.11'
      appSettings: [
        { name: 'FUNCTIONS_EXTENSION_VERSION', value: '~4' }
        { name: 'FUNCTIONS_WORKER_RUNTIME', value: 'python' }
        { name: 'AzureWebJobsStorage', value: 'DefaultEndpointsProtocol=https;AccountName=${storage.name};AccountKey=${storage.listKeys().keys[0].value};EndpointSuffix=${environment().suffixes.storage}' }
        { name: 'SCM_DO_BUILD_DURING_DEPLOYMENT', value: '1' }
        { name: 'RATE_LIMIT_CAPACITY', value: '5' }
        { name: 'RATE_LIMIT_REFILL_PER_SECOND', value: '1' }
        { name: 'REDIS_URL', value: 'rediss://:${listKeys(redis.id, redis.apiVersion).primaryKey}@${redis.properties.hostName}:6380' }
      ]
    }
  }
}

output functionAppName string = functionApp.name
