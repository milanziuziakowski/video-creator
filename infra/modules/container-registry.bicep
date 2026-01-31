// ============================================================================
// Azure Container Registry Module
// ============================================================================
// Creates an Azure Container Registry for storing Docker images
// ============================================================================

@description('Name of the Container Registry (must be globally unique)')
param registryName string

@description('Azure region for the registry')
param location string

@description('Resource tags')
param tags object = {}

@description('SKU for the registry')
@allowed(['Basic', 'Standard', 'Premium'])
param sku string = 'Basic'

@description('Enable admin user for basic authentication')
param adminUserEnabled bool = true

// ============================================================================
// Resources
// ============================================================================

resource containerRegistry 'Microsoft.ContainerRegistry/registries@2023-07-01' = {
  name: registryName
  location: location
  tags: tags
  sku: {
    name: sku
  }
  properties: {
    adminUserEnabled: adminUserEnabled
    publicNetworkAccess: 'Enabled'
    policies: {
      retentionPolicy: {
        status: 'enabled'
        days: 30
      }
    }
  }
}

// ============================================================================
// Outputs
// ============================================================================

@description('Resource ID of the Container Registry')
output registryId string = containerRegistry.id

@description('Name of the Container Registry')
output registryName string = containerRegistry.name

@description('Login server URL of the Container Registry')
output loginServer string = containerRegistry.properties.loginServer

@description('Admin username (if admin user is enabled)')
output adminUsername string = adminUserEnabled ? containerRegistry.listCredentials().username : ''

@description('Admin password (if admin user is enabled)')
@secure()
output adminPassword string = adminUserEnabled ? containerRegistry.listCredentials().passwords[0].value : ''
