# GitHub Environments Setup Guide

**Phase:** 9 - Deployment Configuration  
**Status:** Required for CI/CD  
**Estimated Time:** 15-20 minutes

---

## 1. Overview

GitHub Environments are **required** for your CI/CD workflows to function properly. They provide:

- **Environment-specific secrets** (different API keys per environment)
- **Environment-specific variables** (different URLs per environment)
- **Deployment protection rules** (optional approval gates)
- **Deployment history and tracking**

Your workflows (`backend-cd.yml`, `frontend-cd.yml`, `infra-deploy.yml`) reference these environments:
- `dev` - Development environment
- `staging` - Pre-production testing (optional)
- `prod` - Production environment

---

## 2. Create GitHub Environments

### Step 1: Navigate to Environments Settings

1. Go to your GitHub repository
2. Click **Settings** tab
3. In the left sidebar, click **Environments**
4. Click **New environment**

### Step 2: Create Required Environments

Create these environments (one at a time):

| Environment Name | Purpose |
|------------------|---------|
| `dev` | Development/testing deployments |
| `staging` | Pre-production (optional) |
| `prod` | Production deployments |

For each environment:
1. Enter the environment name (e.g., `dev`)
2. Click **Configure environment**
3. Configure the settings below

---

## 3. Configure Environment-Specific Secrets

For **each environment**, add these secrets:

### Navigate to Environment Secrets
1. Go to **Settings** → **Environments** → click on environment name
2. Scroll to **Environment secrets** section
3. Click **Add secret** for each

### Required Secrets per Environment

| Secret Name | Description | Example |
|-------------|-------------|---------|
| `AZURE_CREDENTIALS` | Service principal JSON | `{"clientId": "...", ...}` |
| `AZURE_STATIC_WEB_APPS_API_TOKEN` | SWA deployment token | Get from Azure Portal |
| `POSTGRES_ADMIN_PASSWORD` | Database admin password | Strong password |
| `JWT_SECRET_KEY` | JWT signing key | 64+ char random string |

### Get SWA Token (for each environment)
```powershell
# Replace with your actual SWA name
az staticwebapp secrets list --name swa-aivideocreator-dev --query "properties.apiKey" -o tsv
```

---

## 4. Configure Environment-Specific Variables

For **each environment**, add these variables:

### Navigate to Environment Variables
1. Go to **Settings** → **Environments** → click on environment name
2. Scroll to **Environment variables** section
3. Click **Add variable** for each

### Required Variables per Environment

#### Dev Environment Variables
| Variable Name | Value |
|---------------|-------|
| `AZURE_CLIENT_ID` | Your Azure AD app client ID |
| `AZURE_TENANT_ID` | Your Azure AD tenant ID |
| `AZURE_API_CLIENT_ID` | Backend API app registration ID |

#### Prod Environment Variables
| Variable Name | Value |
|---------------|-------|
| `AZURE_CLIENT_ID` | Same as dev (or different for prod) |
| `AZURE_TENANT_ID` | Same as dev |
| `AZURE_API_CLIENT_ID` | Same as dev (or different for prod) |

---

## 5. Configure Deployment Protection Rules (Optional)

For **production** environment, add protection rules:

### Option A: Required Reviewers (Recommended for prod)
1. Go to **Settings** → **Environments** → `prod`
2. Check **Required reviewers**
3. Add team members who must approve production deploys
4. Click **Save protection rules**

### Option B: Wait Timer
1. Check **Wait timer**
2. Set minutes to wait (e.g., 5 minutes)
3. Click **Save protection rules**

### Option C: Branch Protection
1. Under **Deployment branches**, select **Selected branches**
2. Click **Add deployment branch rule**
3. Add `main` as the only allowed branch
4. Click **Add rule**

---

## 6. Quick Setup Summary

### Minimum Setup for MVP (dev environment only)

If you only need **dev** environment for now:

1. **Create environment:**
   - Settings → Environments → New environment → `dev`

2. **Add repository secrets** (these can be shared):
   - Settings → Secrets and variables → Actions → Secrets tab
   - Add: `AZURE_CREDENTIALS`, `OPENAI_API_KEY`, `MINIMAX_API_KEY`

3. **Add environment secrets:**
   - Settings → Environments → `dev`
   - Add: `AZURE_STATIC_WEB_APPS_API_TOKEN`, `JWT_SECRET_KEY`

4. **Add environment variables:**
   - Settings → Environments → `dev` → Variables
   - Add: `AZURE_CLIENT_ID`, `AZURE_TENANT_ID`, `AZURE_API_CLIENT_ID`

---

## 7. Verify Setup

### Test 1: Check Environments Exist
Go to **Settings** → **Environments** and verify all environments are listed.

### Test 2: Trigger a Deployment
1. Go to **Actions** tab
2. Select **Backend CD** workflow
3. Click **Run workflow**
4. Select environment: `dev`
5. Click **Run workflow**

### Test 3: Check Deployment History
After a successful deployment:
1. Go to your repository main page
2. Look for **Environments** section in the right sidebar
3. Click on environment to see deployment history

---

## 8. Troubleshooting

### Issue: "Environment 'dev' not found"
**Fix:** Create the environment in Settings → Environments

### Issue: "Secret not found"
**Fix:** Add the secret to both:
- Repository secrets (for shared secrets)
- Environment secrets (for environment-specific secrets)

### Issue: "Deployment requires approval"
**Fix:** Either:
- Approve the pending deployment in Actions tab
- Remove required reviewers from environment settings

### Issue: "Variable not accessible"
**Fix:** Make sure variable is added to the correct environment and use `${{ vars.VARIABLE_NAME }}` in workflow

---

## 9. Reference: Complete Secrets & Variables Checklist

### Repository-Level Secrets (Settings → Secrets → Actions)
- [ ] `AZURE_CREDENTIALS` - Service principal JSON
- [ ] `OPENAI_API_KEY` - OpenAI API key
- [ ] `MINIMAX_API_KEY` - MiniMax API key

### Environment-Level Secrets (per environment)
- [ ] `AZURE_STATIC_WEB_APPS_API_TOKEN` - SWA deploy token
- [ ] `POSTGRES_ADMIN_PASSWORD` - Database password
- [ ] `JWT_SECRET_KEY` - JWT signing key

### Environment-Level Variables (per environment)
- [ ] `AZURE_CLIENT_ID` - Frontend app registration ID
- [ ] `AZURE_TENANT_ID` - Azure AD tenant ID
- [ ] `AZURE_API_CLIENT_ID` - Backend API app registration ID

---

## 10. Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                     GitHub Repository                                │
├─────────────────────────────────────────────────────────────────────┤
│  Repository Secrets (shared):                                        │
│  ├── AZURE_CREDENTIALS                                              │
│  ├── OPENAI_API_KEY                                                 │
│  └── MINIMAX_API_KEY                                                │
├─────────────────────────────────────────────────────────────────────┤
│  Environments:                                                       │
│  ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐       │
│  │      dev        │ │    staging      │ │      prod       │       │
│  │                 │ │                 │ │                 │       │
│  │ Secrets:        │ │ Secrets:        │ │ Secrets:        │       │
│  │ - SWA_TOKEN     │ │ - SWA_TOKEN     │ │ - SWA_TOKEN     │       │
│  │ - JWT_SECRET    │ │ - JWT_SECRET    │ │ - JWT_SECRET    │       │
│  │                 │ │                 │ │                 │       │
│  │ Variables:      │ │ Variables:      │ │ Variables:      │       │
│  │ - CLIENT_ID     │ │ - CLIENT_ID     │ │ - CLIENT_ID     │       │
│  │ - TENANT_ID     │ │ - TENANT_ID     │ │ - TENANT_ID     │       │
│  │                 │ │                 │ │ Protection:     │       │
│  │                 │ │                 │ │ - Reviewers ✓   │       │
│  └─────────────────┘ └─────────────────┘ └─────────────────┘       │
└─────────────────────────────────────────────────────────────────────┘
           │                    │                    │
           ▼                    ▼                    ▼
┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
│  Azure Dev      │  │ Azure Staging   │  │  Azure Prod     │
│  - App Service  │  │ - App Service   │  │  - App Service  │
│  - SWA          │  │ - SWA           │  │  - SWA          │
│  - PostgreSQL   │  │ - PostgreSQL    │  │  - PostgreSQL   │
└─────────────────┘  └─────────────────┘  └─────────────────┘
```

---

## Next Steps

After completing this setup:

1. ✅ Run `infra-deploy.yml` workflow to create Azure resources
2. ✅ Run `backend-cd.yml` to deploy backend
3. ✅ Run `frontend-cd.yml` to deploy frontend
4. ✅ Verify application is accessible at deployed URLs
