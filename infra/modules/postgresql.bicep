// ============================================================================
// PostgreSQL Flexible Server Module
// ============================================================================

@description('Name of the PostgreSQL server')
param serverName string

@description('Azure region')
param location string

@description('Administrator login name')
param administratorLogin string

@description('Administrator password')
@secure()
param administratorPassword string

@description('Database name to create')
param databaseName string = 'video_creator'

@description('PostgreSQL version')
@allowed(['13', '14', '15', '16'])
param postgresVersion string = '15'

@description('SKU tier')
@allowed(['Burstable', 'GeneralPurpose', 'MemoryOptimized'])
param skuTier string = 'Burstable'

@description('SKU name')
param skuName string = 'Standard_B1ms'

@description('Storage size in GB')
@minValue(32)
@maxValue(16384)
param storageSizeGB int = 32

@description('Backup retention days')
@minValue(7)
@maxValue(35)
param backupRetentionDays int = 7

@description('Enable geo-redundant backup')
param geoRedundantBackup bool = false

@description('Resource tags')
param tags object = {}

resource postgresServer 'Microsoft.DBforPostgreSQL/flexibleServers@2023-03-01-preview' = {
  name: serverName
  location: location
  tags: tags
  sku: {
    name: skuName
    tier: skuTier
  }
  properties: {
    version: postgresVersion
    administratorLogin: administratorLogin
    administratorLoginPassword: administratorPassword
    storage: {
      storageSizeGB: storageSizeGB
    }
    backup: {
      backupRetentionDays: backupRetentionDays
      geoRedundantBackup: geoRedundantBackup ? 'Enabled' : 'Disabled'
    }
    highAvailability: {
      mode: 'Disabled'
    }
    authConfig: {
      activeDirectoryAuth: 'Disabled'
      passwordAuth: 'Enabled'
    }
  }
}

// Create the database
resource database 'Microsoft.DBforPostgreSQL/flexibleServers/databases@2023-03-01-preview' = {
  parent: postgresServer
  name: databaseName
  properties: {
    charset: 'UTF8'
    collation: 'en_US.utf8'
  }
}

// Firewall rule: Allow Azure services
resource firewallAzureServices 'Microsoft.DBforPostgreSQL/flexibleServers/firewallRules@2023-03-01-preview' = {
  parent: postgresServer
  name: 'AllowAzureServices'
  properties: {
    startIpAddress: '0.0.0.0'
    endIpAddress: '0.0.0.0'
  }
}

// Firewall rule: Allow all (for development only - remove in production!)
resource firewallAllowAll 'Microsoft.DBforPostgreSQL/flexibleServers/firewallRules@2023-03-01-preview' = {
  parent: postgresServer
  name: 'AllowAll-Dev'
  properties: {
    startIpAddress: '0.0.0.0'
    endIpAddress: '255.255.255.255'
  }
}

// PostgreSQL configurations for better performance
resource configLogConnections 'Microsoft.DBforPostgreSQL/flexibleServers/configurations@2023-03-01-preview' = {
  parent: postgresServer
  name: 'log_connections'
  properties: {
    value: 'ON'
    source: 'user-override'
  }
}

resource configRequireSecureTransport 'Microsoft.DBforPostgreSQL/flexibleServers/configurations@2023-03-01-preview' = {
  parent: postgresServer
  name: 'require_secure_transport'
  properties: {
    value: 'ON'
    source: 'user-override'
  }
}

output serverId string = postgresServer.id
output serverName string = postgresServer.name
output serverFqdn string = postgresServer.properties.fullyQualifiedDomainName
output databaseName string = database.name
output connectionString string = 'postgresql+asyncpg://${administratorLogin}:${administratorPassword}@${postgresServer.properties.fullyQualifiedDomainName}:5432/${databaseName}?sslmode=require'
