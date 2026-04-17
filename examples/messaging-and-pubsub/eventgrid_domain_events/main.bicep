param baseName string = 'eventgrid-domain-events-func'
param location string = resourceGroup().location

var suffix = take(uniqueString(resourceGroup().id, baseName), 6)
var storageName = take('${replace(toLower(baseName), '-', '')}${suffix}', 24)
var functionAppName = '${baseName}-${suffix}'
var topicName = '${baseName}-topic-${suffix}'

resource storage 'Microsoft.Storage/storageAccounts@2023-01-01' = {
  name: storageName
  location: location
  kind: 'StorageV2'
  sku: { name: 'Standard_LRS' }
  properties: { minimumTlsVersion: 'TLS1_2', allowBlobPublicAccess: false }
}

resource topic 'Microsoft.EventGrid/topics@2022-06-15' = {
  name: topicName
  location: location
  sku: { name: 'Basic' }
  properties: { inputSchema: 'EventGridSchema' }
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
        { name: 'MyEventGridTopicUriSetting', value: topic.properties.endpoint }
        { name: 'MyEventGridTopicKeySetting', value: listKeys(topic.id, topic.apiVersion).key1 }
        { name: 'SCM_DO_BUILD_DURING_DEPLOYMENT', value: '1' }
      ]
    }
  }
}

resource subscription 'Microsoft.EventGrid/topics/eventSubscriptions@2022-06-15' = {
  name: '${topic.name}/handle-order-domain-event'
  properties: {
    destination: {
      endpointType: 'AzureFunction'
      properties: {
        resourceId: resourceId('Microsoft.Web/sites/functions', functionApp.name, 'handle_order_domain_event')
      }
    }
    eventDeliverySchema: 'EventGridSchema'
  }
}

output functionAppName string = functionApp.name
