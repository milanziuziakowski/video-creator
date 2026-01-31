// ============================================================================
// App Service Plan Module
// ============================================================================

@description('Name of the App Service Plan')
param appServicePlanName string

@description('Azure region')
param location string

@description('SKU for the App Service Plan')
@allowed(['B1', 'B2', 'B3', 'S1', 'S2', 'S3', 'P1v3', 'P2v3', 'P3v3'])
param sku string = 'B1'

@description('Resource tags')
param tags object = {}

// SKU mapping
var skuConfig = {
  B1: { name: 'B1', tier: 'Basic', size: 'B1', capacity: 1 }
  B2: { name: 'B2', tier: 'Basic', size: 'B2', capacity: 1 }
  B3: { name: 'B3', tier: 'Basic', size: 'B3', capacity: 1 }
  S1: { name: 'S1', tier: 'Standard', size: 'S1', capacity: 1 }
  S2: { name: 'S2', tier: 'Standard', size: 'S2', capacity: 1 }
  S3: { name: 'S3', tier: 'Standard', size: 'S3', capacity: 1 }
  P1v3: { name: 'P1v3', tier: 'PremiumV3', size: 'P1v3', capacity: 1 }
  P2v3: { name: 'P2v3', tier: 'PremiumV3', size: 'P2v3', capacity: 1 }
  P3v3: { name: 'P3v3', tier: 'PremiumV3', size: 'P3v3', capacity: 1 }
}

resource appServicePlan 'Microsoft.Web/serverfarms@2023-01-01' = {
  name: appServicePlanName
  location: location
  tags: tags
  kind: 'linux'
  sku: {
    name: skuConfig[sku].name
    tier: skuConfig[sku].tier
    size: skuConfig[sku].size
    capacity: skuConfig[sku].capacity
  }
  properties: {
    reserved: true // Required for Linux
  }
}

output appServicePlanId string = appServicePlan.id
output appServicePlanName string = appServicePlan.name
