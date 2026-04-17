@description('Base name for all resources')
param baseName string = 'secretlesskeyvault'
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
resource identity 'Microsoft.ManagedIdentity/userAssignedIdentities@2023-01-31' = {
  name: '${baseName}-id'
  location: location
}
resource keyVault 'Microsoft.KeyVault/vaults@2023-02-01' = {
  name: '${baseName}-kv'
  location: location
  properties: {
    tenantId: subscription().tenantId
    sku: { family: 'A', name: 'standard' }
    enableRbacAuthorization: true
  }
}
resource secret 'Microsoft.KeyVault/vaults/secrets@2023-02-01' = {
  parent: keyVault
  name: 'demo-api-key'
  properties: { value: 'replace-me' }
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
        { name: 'UPSTREAM_API_KEY', value: '@Microsoft.KeyVault(SecretUri=https://${baseName}-kv.vault.azure.net/secrets/demo-api-key/)' }
        { name: 'UPSTREAM_SECRET_NAME', value: 'demo-api-key' }
        { name: 'UPSTREAM_APP_NAME', value: 'sample-upstream' }
      ]
    }
  }
}
output functionAppName string = functionApp.name
