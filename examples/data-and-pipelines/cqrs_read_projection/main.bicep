param baseName string = 'cqrs-read-projection-func'
param location string = resourceGroup().location
param sqlAdminLogin string = 'sqladminuser'
@secure()
param sqlAdminPassword string = 'ChangeM3Now!'

var suffix = take(uniqueString(resourceGroup().id, baseName), 6)
var storageName = take('${replace(toLower(baseName), '-', '')}${suffix}', 24)
var functionAppName = '${baseName}-${suffix}'
var cosmosAccountName = '${replace(toLower(baseName), '-', '')}-cosmos-${suffix}'
var sqlServerName = '${baseName}-sql-${suffix}'
var sqlDatabaseName = 'appdb'
var readDbUrl = 'mssql+pyodbc://${sqlAdminLogin}:${sqlAdminPassword}@${sqlServer.properties.fullyQualifiedDomainName}:1433/${sqlDatabaseName}?driver=ODBC+Driver+18+for+SQL+Server&Encrypt=yes&TrustServerCertificate=no&Connection+Timeout=30'

resource storage 'Microsoft.Storage/storageAccounts@2023-01-01' = {
  name: storageName
  location: location
  kind: 'StorageV2'
  sku: { name: 'Standard_LRS' }
  properties: { minimumTlsVersion: 'TLS1_2', allowBlobPublicAccess: false }
}

resource cosmos 'Microsoft.DocumentDB/databaseAccounts@2023-04-15' = {
  name: cosmosAccountName
  location: location
  kind: 'GlobalDocumentDB'
  properties: {
    databaseAccountOfferType: 'Standard'
    locations: [{ locationName: location, failoverPriority: 0 }]
    consistencyPolicy: { defaultConsistencyLevel: 'Session' }
  }
}

resource database 'Microsoft.DocumentDB/databaseAccounts/sqlDatabases@2023-04-15' = {
  name: '${cosmos.name}/ordersdb'
  properties: { resource: { id: 'ordersdb' } }
}

resource orders 'Microsoft.DocumentDB/databaseAccounts/sqlDatabases/containers@2023-04-15' = {
  name: '${cosmos.name}/ordersdb/orders'
  properties: { resource: { id: 'orders', partitionKey: { paths: ['/id'], kind: 'Hash' } } }
}

resource leases 'Microsoft.DocumentDB/databaseAccounts/sqlDatabases/containers@2023-04-15' = {
  name: '${cosmos.name}/ordersdb/leases'
  properties: { resource: { id: 'leases', partitionKey: { paths: ['/id'], kind: 'Hash' } } }
}

resource sqlServer 'Microsoft.Sql/servers@2022-05-01-preview' = {
  name: sqlServerName
  location: location
  properties: { administratorLogin: sqlAdminLogin, administratorLoginPassword: sqlAdminPassword, publicNetworkAccess: 'Enabled' }
}

resource sqlDatabase 'Microsoft.Sql/servers/databases@2022-05-01-preview' = {
  name: '${sqlServer.name}/${sqlDatabaseName}'
  location: location
  sku: { name: 'Basic', tier: 'Basic' }
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
        { name: 'CosmosDBConnection', value: listConnectionStrings(cosmos.id, cosmos.apiVersion).connectionStrings[0].connectionString }
        { name: 'READ_DB_URL', value: readDbUrl }
        { name: 'SCM_DO_BUILD_DURING_DEPLOYMENT', value: '1' }
      ]
    }
  }
}

output functionAppName string = functionApp.name
