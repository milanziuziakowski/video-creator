// ============================================================================
// Azure Container App Module for Frontend SPA
// ============================================================================
// Deploys a Container App configured to serve a static SPA (React/Vite)
// Uses nginx container with external ingress for public accessibility
// ============================================================================

@description('Name of the Container App')
param containerAppName string

@description('Azure region for all resources')
param location string

@description('Resource ID of the Container Apps environment')
param containerAppsEnvironmentId string

@description('Container image to deploy (e.g., myregistry.azurecr.io/frontend:latest)')
param containerImage string

@description('Azure Container Registry server URL')
param containerRegistryServer string = ''

@description('Azure Container Registry username (if using basic auth)')
param containerRegistryUsername string = ''

@description('Azure Container Registry password (if using basic auth)')
@secure()
param containerRegistryPassword string = ''

@description('Use managed identity for ACR pull (recommended)')
param useManagedIdentityForAcr bool = true

@description('Resource tags')
param tags object = {}

@description('Minimum number of replicas')
param minReplicas int = 0

@description('Maximum number of replicas')
param maxReplicas int = 3

@description('CPU allocation (e.g., 0.25, 0.5, 1)')
param cpu string = '0.25'

@description('Memory allocation (e.g., 0.5Gi, 1Gi)')
param memory string = '0.5Gi'

@description('Environment variables for the container')
param environmentVariables array = []

@description('Backend API URL for CORS and API calls')
param backendApiUrl string = ''

@description('Allowed origins for CORS (comma-separated if multiple)')
param corsAllowedOrigins array = []

// ============================================================================
// Variables
// ============================================================================

var registryConfig = !empty(containerRegistryServer) && !useManagedIdentityForAcr ? [
  {
    server: containerRegistryServer
    username: containerRegistryUsername
    passwordSecretRef: 'registry-password'
  }
] : !empty(containerRegistryServer) && useManagedIdentityForAcr ? [
  {
    server: containerRegistryServer
    identity: 'system'
  }
] : []

var secretsConfig = !empty(containerRegistryPassword) && !useManagedIdentityForAcr ? [
  {
    name: 'registry-password'
    value: containerRegistryPassword
  }
] : []

// Merge custom env vars with standard ones
var standardEnvVars = [
  {
    name: 'PORT'
    value: '80'
  }
]

var backendEnvVar = !empty(backendApiUrl) ? [
  {
    name: 'VITE_API_URL'
    value: backendApiUrl
  }
] : []

var allEnvironmentVariables = concat(standardEnvVars, backendEnvVar, environmentVariables)

// ============================================================================
// Resources
// ============================================================================

resource containerApp 'Microsoft.App/containerApps@2024-03-01' = {
  name: containerAppName
  location: location
  tags: tags
  identity: useManagedIdentityForAcr ? {
    type: 'SystemAssigned'
  } : null
  properties: {
    managedEnvironmentId: containerAppsEnvironmentId
    workloadProfileName: 'Consumption'
    configuration: {
      activeRevisionsMode: 'Single'
      ingress: {
        external: true
        targetPort: 80
        transport: 'http'
        allowInsecure: false
        // CORS configuration for API calls from frontend
        corsPolicy: !empty(corsAllowedOrigins) ? {
          allowedOrigins: corsAllowedOrigins
          allowedMethods: [
            'GET'
            'POST'
            'PUT'
            'DELETE'
            'OPTIONS'
          ]
          allowedHeaders: [
            '*'
          ]
          exposeHeaders: [
            '*'
          ]
          maxAge: 86400
          allowCredentials: true
        } : null
      }
      registries: registryConfig
      secrets: secretsConfig
    }
    template: {
      containers: [
        {
          name: 'frontend'
          image: containerImage
          resources: {
            cpu: json(cpu)
            memory: memory
          }
          env: allEnvironmentVariables
          probes: [
            {
              type: 'Liveness'
              httpGet: {
                path: '/health'
                port: 80
                scheme: 'HTTP'
              }
              initialDelaySeconds: 10
              periodSeconds: 30
              timeoutSeconds: 5
              failureThreshold: 3
            }
            {
              type: 'Readiness'
              httpGet: {
                path: '/health'
                port: 80
                scheme: 'HTTP'
              }
              initialDelaySeconds: 5
              periodSeconds: 10
              timeoutSeconds: 3
              failureThreshold: 3
            }
          ]
        }
      ]
      scale: {
        minReplicas: minReplicas
        maxReplicas: maxReplicas
        rules: [
          {
            name: 'http-scaling'
            http: {
              metadata: {
                concurrentRequests: '100'
              }
            }
          }
        ]
      }
    }
  }
}

// ============================================================================
// Outputs
// ============================================================================

@description('Resource ID of the Container App')
output containerAppId string = containerApp.id

@description('Name of the Container App')
output containerAppName string = containerApp.name

@description('FQDN of the Container App (public URL)')
output fqdn string = containerApp.properties.configuration.ingress.fqdn

@description('Full URL of the Container App')
output url string = 'https://${containerApp.properties.configuration.ingress.fqdn}'

@description('Latest revision name')
output latestRevisionName string = containerApp.properties.latestRevisionName

@description('Principal ID of the managed identity (if enabled)')
output principalId string = useManagedIdentityForAcr ? containerApp.identity.principalId : ''
