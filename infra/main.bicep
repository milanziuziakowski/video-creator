// ============================================================================
// AI Video Creator - Main Infrastructure Deployment
// ============================================================================
// This Bicep file orchestrates the deployment of all Azure resources
// Run: az deployment sub create --location <region> --template-file main.bicep --parameters main.parameters.json
// ============================================================================

targetScope = 'subscription'

// ============================================================================
// Parameters
// ============================================================================

@description('Environment name (dev, staging, prod)')
@allowed(['dev', 'staging', 'prod'])
param environment string = 'dev'

@description('Azure region for all resources')
param location string = 'westeurope'

@description('Project name used for naming resources')
param projectName string = 'aivideocreator'

@description('PostgreSQL administrator login')
param postgresAdminLogin string = 'pgadmin'

@description('PostgreSQL administrator password')
@secure()
param postgresAdminPassword string

@description('OpenAI API Key')
@secure()
param openaiApiKey string

@description('MiniMax API Key')
@secure()
param minimaxApiKey string

@description('Azure Entra ID Tenant ID')
param azureTenantId string

@description('Azure Entra ID Client ID (App Registration)')
param azureClientId string

@description('Frontend deployment type: staticWebApp or containerApp')
@allowed(['staticWebApp', 'containerApp'])
param frontendDeploymentType string = 'staticWebApp'

@description('Container image for frontend (required if frontendDeploymentType is containerApp)')
param frontendContainerImage string = ''

@description('Tags for all resources')
param tags object = {
  project: 'ai-video-creator'
  environment: environment
  managedBy: 'bicep'
}

// ============================================================================
// Variables
// ============================================================================

var resourceGroupName = 'rg-${projectName}-${environment}'
var appServicePlanName = 'asp-${projectName}-${environment}'
var appServiceName = 'app-${projectName}-api-${environment}'
var staticWebAppName = 'swa-${projectName}-${environment}'
var postgresServerName = 'psql-${projectName}-${environment}'
var storageAccountName = 'st${projectName}${environment}'
var databaseName = 'video_creator'

// Container Apps variables (used when frontendDeploymentType is containerApp)
var containerRegistryName = 'cr${projectName}${environment}'
var containerAppsEnvName = 'cae-${projectName}-${environment}'
var frontendContainerAppName = 'ca-${projectName}-frontend-${environment}'

// ============================================================================
// Resource Group
// ============================================================================

resource resourceGroup 'Microsoft.Resources/resourceGroups@2023-07-01' = {
  name: resourceGroupName
  location: location
  tags: tags
}

// ============================================================================
// Modules
// ============================================================================

// Storage Account for uploads and generated content
module storageAccount 'modules/storage-account.bicep' = {
  name: 'storage-account-deployment'
  scope: resourceGroup
  params: {
    storageAccountName: storageAccountName
    location: location
    tags: tags
  }
}

// PostgreSQL Flexible Server
module postgres 'modules/postgresql.bicep' = {
  name: 'postgresql-deployment'
  scope: resourceGroup
  params: {
    serverName: postgresServerName
    location: location
    administratorLogin: postgresAdminLogin
    administratorPassword: postgresAdminPassword
    databaseName: databaseName
    tags: tags
  }
}

// App Service Plan (Linux)
module appServicePlan 'modules/app-service-plan.bicep' = {
  name: 'app-service-plan-deployment'
  scope: resourceGroup
  params: {
    appServicePlanName: appServicePlanName
    location: location
    sku: environment == 'prod' ? 'P1v3' : 'B1'
    tags: tags
  }
}

// App Service (Backend API)
module appService 'modules/app-service.bicep' = {
  name: 'app-service-deployment'
  scope: resourceGroup
  params: {
    appServiceName: appServiceName
    location: location
    appServicePlanId: appServicePlan.outputs.appServicePlanId
    pythonVersion: '3.11'
    appSettings: {
      APP_NAME: 'AI-Video-Creator'
      APP_ENV: environment
      DEBUG: environment == 'dev' ? 'true' : 'false'
      LOG_LEVEL: environment == 'prod' ? 'WARNING' : 'INFO'
      OPENAI_API_KEY: openaiApiKey
      MINIMAX_API_KEY: minimaxApiKey
      AZURE_TENANT_ID: azureTenantId
      AZURE_CLIENT_ID: azureClientId
      DATABASE_URL: 'postgresql+asyncpg://${postgresAdminLogin}:${postgresAdminPassword}@${postgresServerName}.postgres.database.azure.com:5432/${databaseName}?sslmode=require'
      STORAGE_CONNECTION_STRING: storageAccount.outputs.connectionString
      STORAGE_CONTAINER_NAME: 'media'
      CORS_ORIGINS: 'https://${staticWebAppName}.azurestaticapps.net'
    }
    tags: tags
  }
  dependsOn: [
    postgres
    storageAccount
  ]
}

// Static Web App (Frontend) - used when frontendDeploymentType is 'staticWebApp'
module staticWebApp 'modules/static-web-app.bicep' = if (frontendDeploymentType == 'staticWebApp') {
  name: 'static-web-app-deployment'
  scope: resourceGroup
  params: {
    staticWebAppName: staticWebAppName
    location: location
    sku: environment == 'prod' ? 'Standard' : 'Free'
    apiBackendUrl: 'https://${appServiceName}.azurewebsites.net'
    tags: tags
  }
}

// ============================================================================
// Container Apps Resources (Alternative Frontend Deployment)
// ============================================================================
// Used when frontendDeploymentType is 'containerApp'
// Provides more control over scaling, custom domains, and container configuration

// Azure Container Registry
module containerRegistry 'modules/container-registry.bicep' = if (frontendDeploymentType == 'containerApp') {
  name: 'container-registry-deployment'
  scope: resourceGroup
  params: {
    registryName: containerRegistryName
    location: location
    sku: environment == 'prod' ? 'Standard' : 'Basic'
    tags: tags
  }
}

// Container Apps Environment
module containerAppsEnvironment 'modules/container-apps-environment.bicep' = if (frontendDeploymentType == 'containerApp') {
  name: 'container-apps-env-deployment'
  scope: resourceGroup
  params: {
    environmentName: containerAppsEnvName
    location: location
    zoneRedundant: environment == 'prod'
    logRetentionInDays: environment == 'prod' ? 90 : 30
    tags: tags
  }
}

// Frontend Container App
module frontendContainerApp 'modules/container-app-frontend.bicep' = if (frontendDeploymentType == 'containerApp') {
  name: 'frontend-container-app-deployment'
  scope: resourceGroup
  params: {
    containerAppName: frontendContainerAppName
    location: location
    containerAppsEnvironmentId: containerAppsEnvironment.outputs.environmentId
    containerImage: !empty(frontendContainerImage) ? frontendContainerImage : '${containerRegistry.outputs.loginServer}/frontend:latest'
    containerRegistryServer: containerRegistry.outputs.loginServer
    useManagedIdentityForAcr: true
    backendApiUrl: 'https://${appServiceName}.azurewebsites.net'
    minReplicas: environment == 'prod' ? 1 : 0
    maxReplicas: environment == 'prod' ? 10 : 3
    cpu: environment == 'prod' ? '0.5' : '0.25'
    memory: environment == 'prod' ? '1Gi' : '0.5Gi'
    tags: tags
  }
  dependsOn: [
    containerRegistry
    containerAppsEnvironment
  ]
}

// ============================================================================
// Outputs
// ============================================================================
// ⚠️ SECURITY: Never output secrets like connection strings or tokens here!
// Retrieve sensitive values using: az webapp config appsettings list
// or: az staticwebapp secrets list

output resourceGroupName string = resourceGroup.name
output appServiceUrl string = appService.outputs.appServiceUrl
output postgresServerFqdn string = postgres.outputs.serverFqdn
output storageAccountName string = storageAccount.outputs.storageAccountName

// Frontend URL (conditional based on deployment type)
output frontendUrl string = frontendDeploymentType == 'staticWebApp' ? staticWebApp.outputs.staticWebAppUrl : frontendContainerApp.outputs.url

// Static Web App outputs (when using Static Web App)
output staticWebAppUrl string = frontendDeploymentType == 'staticWebApp' ? staticWebApp.outputs.staticWebAppUrl : ''

// Container Apps outputs (when using Container Apps)
output containerRegistryLoginServer string = frontendDeploymentType == 'containerApp' ? containerRegistry.outputs.loginServer : ''
output containerAppFqdn string = frontendDeploymentType == 'containerApp' ? frontendContainerApp.outputs.fqdn : ''

// To get the Static Web App deployment token after deployment, run:
// az staticwebapp secrets list --name <staticWebAppName> --query "properties.apiKey" -o tsv
