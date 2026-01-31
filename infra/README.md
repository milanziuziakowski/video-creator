# Azure Infrastructure Deployment Guide

This folder contains Bicep templates to provision all Azure resources for the AI Video Creator application.

## 📁 Structure

```
infra/
├── main.bicep                    # Main orchestration file
├── parameters/
│   ├── dev.parameters.json       # Development environment parameters
│   └── prod.parameters.json      # Production environment parameters
├── modules/
│   ├── app-service-plan.bicep    # Linux App Service Plan
│   ├── app-service.bicep         # Backend API (FastAPI)
│   ├── container-apps-environment.bicep  # Container Apps Environment
│   ├── container-app-frontend.bicep      # Frontend Container App
│   ├── container-registry.bicep  # Azure Container Registry
│   ├── postgresql.bicep          # PostgreSQL Flexible Server
│   ├── static-web-app.bicep      # Frontend (React/Vite) - Static Web App
│   └── storage-account.bicep     # Blob Storage for media files
├── deploy-frontend-containerapp.ps1  # Script to deploy frontend to Container Apps
└── README.md                     # This file
```

## 🏗️ Resources Created

| Resource | Azure Service | Purpose |
|----------|---------------|---------|
| Resource Group | `rg-aivideocreator-{env}` | Container for all resources |
| App Service Plan | `asp-aivideocreator-{env}` | Hosting plan (Linux) |
| App Service | `app-aivideocreator-api-{env}` | Backend FastAPI |
| PostgreSQL | `psql-aivideocreator-{env}` | Database |
| Storage Account | `staivideocreator{env}` | Media files storage |

**Frontend Deployment Options (choose one):**

| Resource | Azure Service | Purpose |
|----------|---------------|---------|
| Static Web App | `swa-aivideocreator-{env}` | Frontend React SPA (default) |
| **OR** Container App | `ca-aivideocreator-frontend-{env}` | Frontend as containerized nginx |
| Container Registry | `craivideocreator{env}` | Docker images (if using Container Apps) |
| Container Apps Env | `cae-aivideocreator-{env}` | Container Apps hosting (if using Container Apps) |

## 📋 Prerequisites

### 1. Install Azure CLI

```powershell
# Check if Azure CLI is installed
az --version

# If not installed, download from:
# https://docs.microsoft.com/en-us/cli/azure/install-azure-cli-windows
# Or use winget:
winget install Microsoft.AzureCLI
```

### 2. Install Bicep

```powershell
# Bicep is included with Azure CLI 2.20.0+
# Verify installation:
az bicep version

# If needed, install/upgrade:
az bicep install
az bicep upgrade
```

### 3. Login to Azure

```powershell
# Login to Azure
az login

# If you have multiple subscriptions, set the one you want to use:
az account list --output table
az account set --subscription "Your Subscription Name"

# Verify current subscription
az account show
```

---

## 🚀 Step-by-Step Deployment

### Step 1: Create Azure Entra ID App Registration (FIRST!)

Before deploying infrastructure, create the App Registration for authentication:

```powershell
# 1. Create the App Registration
az ad app create `
  --display-name "AI Video Creator - Frontend" `
  --sign-in-audience AzureADMyOrg `
  --web-redirect-uris "http://localhost:5173" "http://localhost:3000"

# 2. Note the output - save these values:
#    - "appId" = This is your AZURE_CLIENT_ID
#    - "id" = This is the Object ID (different from appId)

# 3. Get your Tenant ID:
az account show --query tenantId -o tsv
```

**Save these values - you'll need them:**
- `AZURE_CLIENT_ID` = appId from step 2
- `AZURE_TENANT_ID` = output from step 3

### Step 2: Configure Parameters File

Edit `parameters/dev.parameters.json`:

```powershell
# Open the file in VS Code or your editor
code infra/parameters/dev.parameters.json
```

Fill in the secure values:

```json
{
  "parameters": {
    "environment": { "value": "dev" },
    "location": { "value": "westeurope" },
    "projectName": { "value": "aivideocreator" },
    "postgresAdminLogin": { "value": "pgadmin" },
    "postgresAdminPassword": { "value": "YourSecurePassword123!" },
    "openaiApiKey": { "value": "sk-proj-your-key-here" },
    "minimaxApiKey": { "value": "your-minimax-key-here" },
    "azureTenantId": { "value": "your-tenant-id" },
    "azureClientId": { "value": "your-client-id" }
  }
}
```

⚠️ **Security Note:** Never commit parameter files with secrets to Git!

### Step 3: Validate the Bicep Template

```powershell
# Navigate to infra folder
cd C:\Users\milan\video_creator\infra

# Validate the template (dry run)
az deployment sub validate `
  --location westeurope `
  --template-file main.bicep `
  --parameters parameters/dev.parameters.json
```

### Step 4: Preview Changes (What-If)

```powershell
# See what resources will be created (no actual deployment)
az deployment sub what-if `
  --location westeurope `
  --template-file main.bicep `
  --parameters parameters/dev.parameters.json
```

### Step 5: Deploy Infrastructure

```powershell
# Deploy all resources
az deployment sub create `
  --name "ai-video-creator-$(Get-Date -Format 'yyyyMMdd-HHmmss')" `
  --location westeurope `
  --template-file main.bicep `
  --parameters parameters/dev.parameters.json

# This takes 10-15 minutes for PostgreSQL provisioning
```

### Step 6: Get Deployment Outputs

```powershell
# Get the outputs from the deployment
az deployment sub show `
  --name "ai-video-creator-deployment" `
  --query properties.outputs

# Or get specific values:
az deployment sub show `
  --name "ai-video-creator-deployment" `
  --query properties.outputs.appServiceUrl.value -o tsv
```

### Step 7: Configure App Registration API Scope

```powershell
# Get your Client ID
$clientId = "your-client-id-here"

# Add API scope (access_as_user)
az ad app update `
  --id $clientId `
  --identifier-uris "api://$clientId"

# Note: Adding scopes via CLI is complex. Do this in Azure Portal:
# 1. Go to: Azure Portal > App registrations > Your App > Expose an API
# 2. Click "Add a scope"
# 3. Scope name: access_as_user
# 4. Who can consent: Admins and users
# 5. Save
```

### Step 8: Add Redirect URIs (After Deployment)

Once you know your Static Web App URL:

```powershell
# Get the Static Web App URL
$swaUrl = az deployment sub show `
  --name "ai-video-creator-deployment" `
  --query properties.outputs.staticWebAppUrl.value -o tsv

# Add production redirect URI to App Registration
az ad app update `
  --id "your-client-id" `
  --web-redirect-uris "http://localhost:5173" "http://localhost:3000" "$swaUrl"
```

---

## 🔄 Update Existing Deployment

```powershell
# Re-run the same deployment command - Bicep is idempotent
az deployment sub create `
  --name "ai-video-creator-update-$(Get-Date -Format 'yyyyMMdd-HHmmss')" `
  --location westeurope `
  --template-file main.bicep `
  --parameters parameters/dev.parameters.json
```

---

## 🗑️ Cleanup (Delete All Resources)

```powershell
# Delete the entire resource group (DESTRUCTIVE!)
az group delete --name rg-aivideocreator-dev --yes --no-wait

# Or for production:
# az group delete --name rg-aivideocreator-prod --yes --no-wait
```

---

## 🔒 Security Best Practices

### 1. Use Azure Key Vault for Secrets (Recommended for Production)

```powershell
# Create Key Vault
az keyvault create `
  --name "kv-aivideocreator-prod" `
  --resource-group "rg-aivideocreator-prod" `
  --location westeurope

# Store secrets
az keyvault secret set --vault-name "kv-aivideocreator-prod" --name "openai-api-key" --value "sk-proj-xxx"
az keyvault secret set --vault-name "kv-aivideocreator-prod" --name "minimax-api-key" --value "xxx"
```

### 2. Restrict PostgreSQL Firewall

After deployment, remove the "AllowAll" firewall rule:

```powershell
az postgres flexible-server firewall-rule delete `
  --resource-group rg-aivideocreator-dev `
  --name psql-aivideocreator-dev `
  --rule-name AllowAll-Dev `
  --yes
```

### 3. Enable Private Endpoints (Production)

For production, consider using Private Endpoints for PostgreSQL and Storage Account.

---

## 📊 Estimated Costs (West Europe)

| Resource | SKU (Dev) | Est. Monthly Cost |
|----------|-----------|-------------------|
| App Service Plan | B1 | ~$13 |
| PostgreSQL Flexible | B1ms | ~$15 |
| Static Web App | Free | $0 |
| Storage Account | Standard LRS | ~$2 |
| **Total (Dev)** | | **~$30/month** |

| Resource | SKU (Prod) | Est. Monthly Cost |
|----------|-----------|-------------------|
| App Service Plan | P1v3 | ~$130 |
| PostgreSQL Flexible | Standard_D2s_v3 | ~$130 |
| Static Web App | Standard | ~$9 |
| Storage Account | Standard GRS | ~$5 |
| **Total (Prod)** | | **~$275/month** |

---

## 🐛 Troubleshooting

### Deployment Failed

```powershell
# Get detailed error messages
az deployment sub show `
  --name "your-deployment-name" `
  --query properties.error
```

### PostgreSQL Connection Issues

```powershell
# Check firewall rules
az postgres flexible-server firewall-rule list `
  --resource-group rg-aivideocreator-dev `
  --name psql-aivideocreator-dev

# Test connection
az postgres flexible-server connect `
  --name psql-aivideocreator-dev `
  --admin-user pgadmin `
  --admin-password "YourPassword"
```

### App Service Not Starting

```powershell
# View logs
az webapp log tail `
  --resource-group rg-aivideocreator-dev `
  --name app-aivideocreator-api-dev

# Check configuration
az webapp config show `
  --resource-group rg-aivideocreator-dev `
  --name app-aivideocreator-api-dev
```

### Container App Issues

```powershell
# View Container App logs
az containerapp logs show `
  --name ca-aivideocreator-frontend-dev `
  --resource-group rg-aivideocreator-dev `
  --follow

# Check Container App status
az containerapp show `
  --name ca-aivideocreator-frontend-dev `
  --resource-group rg-aivideocreator-dev `
  --query "{status:properties.runningStatus, fqdn:properties.configuration.ingress.fqdn}"

# List revisions
az containerapp revision list `
  --name ca-aivideocreator-frontend-dev `
  --resource-group rg-aivideocreator-dev `
  --output table
```

---

## 🐳 Using Container Apps for Frontend (Alternative)

Instead of Static Web Apps, you can deploy the frontend as a containerized nginx app:

### Option A: Deploy with Container Apps (Full Infrastructure)

```powershell
# Deploy with Container Apps instead of Static Web Apps
az deployment sub create `
  --name "ai-video-creator-containerapp" `
  --location westeurope `
  --template-file main.bicep `
  --parameters parameters/dev.parameters.json `
  --parameters frontendDeploymentType=containerApp
```

### Option B: Build and Deploy Frontend Image

```powershell
# 1. Build the Docker image locally
cd ai-video-creator-frontend
docker build -t craivideocreatordev.azurecr.io/frontend:latest .

# 2. Login to Azure Container Registry
az acr login --name craivideocreatordev

# 3. Push the image
docker push craivideocreatordev.azurecr.io/frontend:latest

# 4. Update the Container App
az containerapp update `
  --name ca-aivideocreator-frontend-dev `
  --resource-group rg-aivideocreator-dev `
  --image craivideocreatordev.azurecr.io/frontend:latest
```

### Using the Deployment Script

```powershell
# Full build and deploy
.\infra\deploy-frontend-containerapp.ps1 -Environment dev

# Build only (don't push/deploy)
.\infra\deploy-frontend-containerapp.ps1 -Environment dev -BuildOnly

# Deploy only (image already in ACR)
.\infra\deploy-frontend-containerapp.ps1 -Environment dev -DeployOnly
```

### Container Apps Benefits

- **More control**: Custom scaling rules, health probes, resource limits
- **Better for microservices**: Share environment with backend container apps
- **Custom domains**: Easier custom domain setup with certificates
- **Cost**: Can scale to zero (consumption plan), pay per request

---

## 📚 References

- [Bicep Documentation](https://docs.microsoft.com/en-us/azure/azure-resource-manager/bicep/)
- [Azure App Service](https://docs.microsoft.com/en-us/azure/app-service/)
- [Azure Static Web Apps](https://docs.microsoft.com/en-us/azure/static-web-apps/)
- [Azure Container Apps](https://learn.microsoft.com/en-us/azure/container-apps/)
- [Azure Container Registry](https://learn.microsoft.com/en-us/azure/container-registry/)
- [Azure Database for PostgreSQL](https://docs.microsoft.com/en-us/azure/postgresql/)
- [Azure Entra ID (Azure AD)](https://docs.microsoft.com/en-us/azure/active-directory/)
