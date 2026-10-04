@description('Base name for Web PubSub proxy resources')
param baseName string = 'websocketproxy'
param location string = resourceGroup().location

var storageName = 'st${substring(toLower(uniqueString(resourceGroup().id, baseName)), 0, 22)}'

resource storage 'Microsoft.Storage/storageAccounts@2023-01-01' = {
  name: storageName
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
  properties: {
    reserved: true
  }
}

resource webpubsub 'Microsoft.SignalRService/webPubSub@2024-03-01' = {
  name: '${baseName}-wps'
  location: location
  sku: { name: 'Free_F1', capacity: 1 }
}

resource functionApp 'Microsoft.Web/sites@2023-01-01' = {
  name: '${baseName}-${substring(uniqueString(resourceGroup().id), 0, 6)}'
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
        { name: 'WebPubSubConnectionString', value: 'Endpoint=https://${webpubsub.name}.webpubsub.azure.com;AccessKey=replace-me;Version=1.0;' }
        { name: 'WEBPUBSUB_HUB_NAME', value: 'realtime-proxy' }
      ]
    }
  }
}
