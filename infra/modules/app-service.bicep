// ============================================================================
// App Service Module (Backend API)
// ============================================================================

@description('Name of the App Service')
param appServiceName string

@description('Azure region')
param location string

@description('App Service Plan resource ID')
param appServicePlanId string

@description('Python version')
@allowed(['3.9', '3.10', '3.11', '3.12'])
param pythonVersion string = '3.11'

@description('Application settings (environment variables)')
param appSettings object = {}

@description('Resource tags')
param tags object = {}

// Convert app settings object to array format
var appSettingsArray = [for item in items(appSettings): {
  name: item.key
  value: item.value
}]

resource appService 'Microsoft.Web/sites@2023-01-01' = {
  name: appServiceName
  location: location
  tags: tags
  kind: 'app,linux'
  identity: {
    type: 'SystemAssigned'
  }
  properties: {
    serverFarmId: appServicePlanId
    httpsOnly: true
    siteConfig: {
      linuxFxVersion: 'PYTHON|${pythonVersion}'
      alwaysOn: true
      ftpsState: 'Disabled'
      minTlsVersion: '1.2'
      http20Enabled: true
      appCommandLine: 'gunicorn -w 4 -k uvicorn.workers.UvicornWorker app.main:app'
      appSettings: concat(appSettingsArray, [
        {
          name: 'SCM_DO_BUILD_DURING_DEPLOYMENT'
          value: 'true'
        }
        {
          name: 'ENABLE_ORYX_BUILD'
          value: 'true'
        }
        {
          name: 'WEBSITES_ENABLE_APP_SERVICE_STORAGE'
          value: 'true'
        }
      ])
    }
  }
}

// Configure CORS
resource appServiceCors 'Microsoft.Web/sites/config@2023-01-01' = {
  parent: appService
  name: 'web'
  properties: {
    cors: {
      allowedOrigins: [
        'http://localhost:5173'
        'http://localhost:3000'
      ]
      supportCredentials: true
    }
  }
}

// Logging configuration
resource appServiceLogs 'Microsoft.Web/sites/config@2023-01-01' = {
  parent: appService
  name: 'logs'
  properties: {
    applicationLogs: {
      fileSystem: {
        level: 'Information'
      }
    }
    httpLogs: {
      fileSystem: {
        enabled: true
        retentionInDays: 7
        retentionInMb: 35
      }
    }
    detailedErrorMessages: {
      enabled: true
    }
  }
}

output appServiceId string = appService.id
output appServiceName string = appService.name
output appServiceUrl string = 'https://${appService.properties.defaultHostName}'
output principalId string = appService.identity.principalId
