// ============================================================================
// Azure Static Web App Module (Frontend)
// ============================================================================

@description('Name of the Static Web App')
param staticWebAppName string

@description('Azure region')
param location string

@description('SKU tier')
@allowed(['Free', 'Standard'])
param sku string = 'Free'

@description('Backend API URL')
param apiBackendUrl string = ''

@description('Resource tags')
param tags object = {}

resource staticWebApp 'Microsoft.Web/staticSites@2023-01-01' = {
  name: staticWebAppName
  location: location
  tags: tags
  sku: {
    name: sku
    tier: sku
  }
  properties: {
    stagingEnvironmentPolicy: 'Enabled'
    allowConfigFileUpdates: true
    buildProperties: {
      appLocation: '/frontend'
      apiLocation: ''
      outputLocation: 'dist'
      appBuildCommand: 'npm run build'
    }
  }
}

// Link backend API (if provided)
resource linkedBackend 'Microsoft.Web/staticSites/linkedBackends@2023-01-01' = if (!empty(apiBackendUrl)) {
  parent: staticWebApp
  name: 'backend'
  properties: {
    backendResourceId: ''
    region: location
  }
}

// App settings for the static web app
resource staticWebAppSettings 'Microsoft.Web/staticSites/config@2023-01-01' = {
  parent: staticWebApp
  name: 'appsettings'
  properties: {
    VITE_API_URL: '${apiBackendUrl}/api/v1'
  }
}

output staticWebAppId string = staticWebApp.id
output staticWebAppName string = staticWebApp.name
output staticWebAppUrl string = 'https://${staticWebApp.properties.defaultHostname}'
output deploymentToken string = listSecrets(staticWebApp.id, staticWebApp.apiVersion).properties.apiKey
