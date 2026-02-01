# CI/CD Setup Checklist for Beginners

This guide helps you set up and verify your CI/CD pipeline step by step.

---

## 📋 Pre-Flight Checklist

### 1. Azure Prerequisites
- [ ] Azure subscription is active (`az account show`)
- [ ] Azure CLI installed and logged in (`az login`)
- [ ] Resource group exists (`az group list`)

### 2. GitHub Prerequisites  
- [ ] Repository created on GitHub
- [ ] `main` branch exists
- [ ] `develop` branch exists (for staging)

---

## 🔐 Step 1: Create Azure Service Principal

Run this command to create credentials for GitHub Actions:

```powershell
# First, get your subscription ID
az account show --query id -o tsv

# Create service principal (replace placeholders)
az ad sp create-for-rbac `
  --name "github-actions-ai-video-creator" `
  --role contributor `
  --scopes /subscriptions/YOUR_SUBSCRIPTION_ID/resourceGroups/YOUR_RESOURCE_GROUP `
  --sdk-auth
```

**Save the JSON output** - you'll need it for the next step.

---

## 🔑 Step 2: Configure GitHub Secrets

Go to: **Repository** → **Settings** → **Secrets and variables** → **Actions**

### Required Secrets (click "New repository secret" for each):

| Secret Name | Value | How to Get It |
|-------------|-------|---------------|
| `AZURE_CREDENTIALS` | JSON from Step 1 | Copy entire JSON output |
| `AZURE_SUBSCRIPTION_ID` | Your subscription ID | `az account show --query id -o tsv` |
| `AZURE_WEBAPP_NAME` | Your App Service name | From Azure Portal or Bicep output |
| `AZURE_SWA_TOKEN` | Static Web App token | See command below |
| `OPENAI_API_KEY` | OpenAI API key | From platform.openai.com |
| `MINIMAX_API_KEY` | MiniMax API key | From minimax platform |
| `AZURE_DB_CONNECTION_STRING` | PostgreSQL URL | See format below |

### Get Static Web App Token:
```powershell
az staticwebapp secrets list --name YOUR_SWA_NAME --query "properties.apiKey" -o tsv
```

### Database Connection String Format:
```
postgresql+asyncpg://USERNAME:PASSWORD@SERVERNAME.postgres.database.azure.com:5432/DATABASE?sslmode=require
```

---

## 📊 Step 3: Configure GitHub Variables

Go to: **Repository** → **Settings** → **Secrets and variables** → **Actions** → **Variables tab**

| Variable Name | Value | Example |
|--------------|-------|---------|
| `VITE_API_URL` | Backend API URL (staging) | `https://app-aivideo-dev.azurewebsites.net/api/v1` |
| `VITE_API_URL_PROD` | Backend API URL (prod) | `https://app-aivideo-prod.azurewebsites.net/api/v1` |


---

## ✅ Step 4: Verify Setup

### Test 1: Check Secrets are Set
```powershell
# Go to Actions tab in GitHub
# If workflows fail with "secret not found", you missed a secret
```

### Test 2: Manual Workflow Run
1. Go to **Actions** tab
2. Select "Backend CI" workflow
3. Click **Run workflow**
4. Watch the execution

### Test 3: Check Azure Resources
```powershell
# List your resources
az resource list --resource-group YOUR_RG_NAME --output table
```

---

## 🔧 Step 5: First Deployment

### Deploy Infrastructure First:
```powershell
cd infra

# Deploy to dev environment
az deployment sub create `
  --location westeurope `
  --template-file main.bicep `
  --parameters parameters/dev.parameters.json
```

### Then Push Code:
```powershell
git add .
git commit -m "Initial commit"
git push origin main
```

---

## 🐛 Troubleshooting Common Issues

### Issue: "Azure login failed"
**Fix:** Regenerate service principal credentials and update `AZURE_CREDENTIALS`

### Issue: "Resource not found"
**Fix:** Deploy infrastructure first with `az deployment`

### Issue: "Permission denied"
**Fix:** Check service principal has `Contributor` role on resource group

### Issue: "Build failed - module not found"
**Fix:** Ensure all dependencies are in `pyproject.toml` / `package.json`

### Issue: "Health check failed"
**Fix:** 
1. Check App Service logs: `az webapp log tail --name YOUR_APP --resource-group YOUR_RG`
2. Verify environment variables are set
3. Check database connection

---

## 🌍 Step 6: Create GitHub Environments

**IMPORTANT:** Your workflows reference GitHub Environments. You must create them!

1. Go to: **Repository** → **Settings** → **Environments**
2. Create these environments:

| Environment | Purpose | Protection Rules |
|-------------|---------|------------------|
| `dev` | Development testing | None |
| `staging` | Pre-production (optional) | None |
| `prod` | Production | Required reviewers (recommended) |

3. For each environment, add **environment secrets** and **variables**

📖 **See [09-GITHUB-ENVIRONMENTS-SETUP.md](./09-GITHUB-ENVIRONMENTS-SETUP.md) for complete setup guide**

---

## 📈 Monitoring Your Pipelines

### View Workflow Runs:
- Go to **Actions** tab in GitHub
- Click on any workflow run to see details
- Expand steps to see logs

### View Azure Logs:
```powershell
# Backend logs
az webapp log tail --name YOUR_APP_NAME --resource-group YOUR_RG

# Or view in Azure Portal → App Service → Log stream
```

---

## 🚀 Workflow Triggers Reference

| Event | Backend CI | Backend Deploy | Frontend CI | Frontend Deploy |
|-------|-----------|----------------|-------------|-----------------|
| Push to `main` | ✅ | ✅ | ✅ | ✅ |
| Push to `develop` | ✅ | ❌ | ✅ | ❌ |
| Pull Request | ✅ | ❌ | ✅ | ❌ |
| Manual | ❌ | ✅ | ❌ | ✅ |

---

## 📝 Notes for Your Project

- **No Docker needed**: Your deployment uses Azure App Service with native Python runtime
- **Bicep handles infrastructure**: Run Bicep deployment once before CI/CD
- **Secrets stay secret**: Never commit `.env` files or log secret values
