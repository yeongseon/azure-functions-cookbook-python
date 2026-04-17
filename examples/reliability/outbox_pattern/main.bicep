@description('Base name for all resources')
param baseName string = 'outboxpattern'
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
  kind: 'functionapp'
  sku: { name: 'Y1', tier: 'Dynamic' }
  properties: {}
}
resource cosmos 'Microsoft.DocumentDB/databaseAccounts@2023-04-15' = {
  name: '${baseName}-cosmos'
  location: location
  kind: 'GlobalDocumentDB'
  properties: {
    databaseAccountOfferType: 'Standard'
    locations: [ { locationName: location, failoverPriority: 0 } ]
    consistencyPolicy: { defaultConsistencyLevel: 'Session' }
  }
}
resource cosmosDb 'Microsoft.DocumentDB/databaseAccounts/sqlDatabases@2023-04-15' = {
  parent: cosmos
  name: 'outboxdb'
  properties: { resource: { id: 'outboxdb' } }
}
resource cosmosOrders 'Microsoft.DocumentDB/databaseAccounts/sqlDatabases/containers@2023-04-15' = {
  parent: cosmosDb
  name: 'orders'
  properties: { resource: { id: 'orders', partitionKey: { paths: ['/partitionKey'], kind: 'Hash' } } }
}
resource cosmosLeases 'Microsoft.DocumentDB/databaseAccounts/sqlDatabases/containers@2023-04-15' = {
  parent: cosmosDb
  name: 'leases'
  properties: { resource: { id: 'leases', partitionKey: { paths: ['/id'], kind: 'Hash' } } }
}
resource functionApp 'Microsoft.Web/sites@2023-01-01' = {
  name: functionAppName
  location: location
  kind: 'functionapp,linux'
  properties: {
    serverFarmId: plan.id
    reserved: true
    httpsOnly: true
    siteConfig: {
      linuxFxVersion: 'Python|3.11'
      appSettings: [
        { name: 'FUNCTIONS_EXTENSION_VERSION', value: '~4' }
        { name: 'FUNCTIONS_WORKER_RUNTIME', value: 'python' }
        { name: 'AzureWebJobsStorage', value: 'DefaultEndpointsProtocol=https;AccountName=${storage.name};AccountKey=${storage.listKeys().keys[0].value};EndpointSuffix=${environment().suffixes.storage}' }
        { name: 'SCM_DO_BUILD_DURING_DEPLOYMENT', value: '1' }
        { name: 'COSMOS_DB_ENDPOINT', value: cosmos.properties.documentEndpoint }
        { name: 'COSMOS_DB_KEY', value: 'replace-me' }
        { name: 'COSMOS_DB_DATABASE_NAME', value: 'outboxdb' }
        { name: 'COSMOS_DB_CONTAINER_NAME', value: 'orders' }
        { name: 'CosmosDBConnection', value: 'AccountEndpoint=${cosmos.properties.documentEndpoint};AccountKey=replace-me;' }
      ]
    }
  }
}
output functionAppName string = functionApp.name
