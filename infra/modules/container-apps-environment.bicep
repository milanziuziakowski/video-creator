// ============================================================================
// Azure Container Apps Environment Module
// ============================================================================
// Creates a Container Apps environment with Log Analytics workspace
// This is the shared hosting environment for container apps
// ============================================================================

@description('Name of the Container Apps environment')
param environmentName string

@description('Azure region for all resources')
param location string

@description('Resource tags')
param tags object = {}

@description('Enable zone redundancy for production')
param zoneRedundant bool = false

@description('Log Analytics workspace retention in days')
param logRetentionInDays int = 30

// ============================================================================
// Resources
// ============================================================================

// Log Analytics Workspace for container app logs
resource logAnalyticsWorkspace 'Microsoft.OperationalInsights/workspaces@2023-09-01' = {
  name: 'log-${environmentName}'
  location: location
  tags: tags
  properties: {
    sku: {
      name: 'PerGB2018'
    }
    retentionInDays: logRetentionInDays
    features: {
      enableLogAccessUsingOnlyResourcePermissions: true
    }
    workspaceCapping: {
      dailyQuotaGb: -1 // No cap
    }
  }
}

// Container Apps Environment
resource containerAppsEnvironment 'Microsoft.App/managedEnvironments@2024-03-01' = {
  name: environmentName
  location: location
  tags: tags
  properties: {
    appLogsConfiguration: {
      destination: 'log-analytics'
      logAnalyticsConfiguration: {
        customerId: logAnalyticsWorkspace.properties.customerId
        sharedKey: logAnalyticsWorkspace.listKeys().primarySharedKey
      }
    }
    zoneRedundant: zoneRedundant
    workloadProfiles: [
      {
        name: 'Consumption'
        workloadProfileType: 'Consumption'
      }
    ]
  }
}

// ============================================================================
// Outputs
// ============================================================================

@description('Resource ID of the Container Apps environment')
output environmentId string = containerAppsEnvironment.id

@description('Name of the Container Apps environment')
output environmentName string = containerAppsEnvironment.name

@description('Default domain of the Container Apps environment')
output defaultDomain string = containerAppsEnvironment.properties.defaultDomain

@description('Log Analytics Workspace ID')
output logAnalyticsWorkspaceId string = logAnalyticsWorkspace.id
