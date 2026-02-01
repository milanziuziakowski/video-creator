# CI/CD Pipeline Guide

**Phase:** 7  
**Technology:** GitHub Actions, Azure App Service, Azure Static Web Apps

---

## 1. Overview

This guide covers setting up continuous integration and deployment pipelines for:

- **Backend:** Python FastAPI → Azure App Service
- **Frontend:** React/Vite → Azure Static Web Apps

```
┌─────────────────────────────────────────────────────────────────────┐
│                         CI/CD Pipeline                               │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────────┐  │
│  │  Commit  │───▶│  Build   │───▶│   Test   │───▶│    Deploy    │  │
│  │  (Push)  │    │ & Lint   │    │  (Unit,  │    │   (Staging/  │  │
│  │          │    │          │    │   E2E)   │    │    Prod)     │  │
│  └──────────┘    └──────────┘    └──────────┘    └──────────────┘  │
│                                                                      │
│  Triggers:                                                           │
│  - Push to main → Deploy to Production                              │
│  - Push to develop → Deploy to Staging                              │
│  - Pull Request → Build + Test only                                  │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 2. Repository Structure

```
ai-video-creator/
├── .github/
│   └── workflows/
│       ├── backend-ci.yml          # Backend CI pipeline
│       ├── backend-deploy.yml      # Backend deployment
│       ├── frontend-ci.yml         # Frontend CI pipeline
│       └── frontend-deploy.yml     # Frontend deployment (Static Web Apps)
├── backend/
│   ├── app/
│   ├── tests/
│   ├── pyproject.toml
│   └── Dockerfile
├── frontend/
│   ├── src/
│   ├── package.json
│   └── vite.config.ts
└── README.md
```

---

## 3. GitHub Secrets Configuration

### 3.1 Required Secrets

Navigate to **Repository Settings** → **Secrets and variables** → **Actions**

Add these secrets:

```
# Azure Credentials (Service Principal)
AZURE_CREDENTIALS          # JSON output from az ad sp create-for-rbac

# Azure Resources
AZURE_SUBSCRIPTION_ID      # Your Azure subscription ID
AZURE_RG_NAME              # Resource group name
AZURE_WEBAPP_NAME          # Backend App Service name
AZURE_SWA_TOKEN            # Static Web Apps deployment token

# API Keys (for deployment)
OPENAI_API_KEY             # OpenAI API key
MINIMAX_API_KEY            # MiniMax API key

# Database
AZURE_DB_CONNECTION_STRING # PostgreSQL connection string
```

### 3.2 Create Azure Service Principal

```bash
# Login to Azure
az login

# Create service principal with Contributor role
az ad sp create-for-rbac \
  --name "github-actions-ai-video-creator" \
  --role contributor \
  --scopes /subscriptions/{subscription-id}/resourceGroups/{resource-group} \
  --sdk-auth

# Copy the JSON output to AZURE_CREDENTIALS secret
```

---

## 4. Backend CI Pipeline

### 4.1 Backend CI Workflow (.github/workflows/backend-ci.yml)

```yaml
name: Backend CI

on:
  push:
    branches: [main, develop]
    paths:
      - 'backend/**'
      - '.github/workflows/backend-*.yml'
  pull_request:
    branches: [main, develop]
    paths:
      - 'backend/**'

defaults:
  run:
    working-directory: backend

jobs:
  lint:
    name: Lint & Type Check
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      
      - name: Install uv
        uses: astral-sh/setup-uv@v4
      
      - name: Install dependencies
        run: uv sync --dev
      
      - name: Run Ruff (lint)
        run: uv run ruff check app/ tests/
      
      - name: Run Ruff (format check)
        run: uv run ruff format --check app/ tests/
      
      - name: Run mypy (type check)
        run: uv run mypy app/

  test:
    name: Unit Tests
    runs-on: ubuntu-latest
    needs: lint
    
    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_USER: test
          POSTGRES_PASSWORD: test
          POSTGRES_DB: test_db
        ports:
          - 5432:5432
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
    
    env:
      DATABASE_URL: postgresql+asyncpg://test:test@localhost:5432/test_db
      OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
      MINIMAX_API_KEY: ${{ secrets.MINIMAX_API_KEY }}
    
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      
      - name: Install uv
        uses: astral-sh/setup-uv@v4
      
      - name: Install dependencies
        run: uv sync --dev
      
      - name: Run tests with coverage
        run: |
          uv run pytest tests/ \
            --cov=app \
            --cov-report=xml \
            --cov-report=html \
            -v
      
      - name: Upload coverage report
        uses: codecov/codecov-action@v4
        with:
          files: ./backend/coverage.xml
          fail_ci_if_error: false

  build:
    name: Build Docker Image
    runs-on: ubuntu-latest
    needs: test
    
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v3
      
      - name: Build image
        uses: docker/build-push-action@v5
        with:
          context: ./backend
          push: false
          tags: ai-video-creator-backend:${{ github.sha }}
          cache-from: type=gha
          cache-to: type=gha,mode=max
```

### 4.2 Backend Deployment (.github/workflows/backend-deploy.yml)

```yaml
name: Backend Deploy

on:
  push:
    branches: [main]
    paths:
      - 'backend/**'
  workflow_dispatch:
    inputs:
      environment:
        description: 'Deployment environment'
        required: true
        default: 'staging'
        type: choice
        options:
          - staging
          - production

defaults:
  run:
    working-directory: backend

jobs:
  deploy:
    name: Deploy to Azure App Service
    runs-on: ubuntu-latest
    environment: ${{ github.event.inputs.environment || 'production' }}
    
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      
      - name: Install uv
        uses: astral-sh/setup-uv@v4
      
      - name: Install dependencies (production only)
        run: uv sync --no-dev
      
      - name: Create deployment package
        run: |
          mkdir -p deploy
          cp -r app deploy/
          cp pyproject.toml deploy/
          cp uv.lock deploy/
          cd deploy && zip -r ../deploy.zip .
      
      - name: Login to Azure
        uses: azure/login@v2
        with:
          creds: ${{ secrets.AZURE_CREDENTIALS }}
      
      - name: Deploy to Azure App Service
        uses: azure/webapps-deploy@v3
        with:
          app-name: ${{ secrets.AZURE_WEBAPP_NAME }}
          package: backend/deploy.zip
      
      - name: Configure App Settings
        uses: azure/appservice-settings@v1
        with:
          app-name: ${{ secrets.AZURE_WEBAPP_NAME }}
          app-settings-json: |
            [
              {"name": "SCM_DO_BUILD_DURING_DEPLOYMENT", "value": "true"},
              {"name": "OPENAI_API_KEY", "value": "${{ secrets.OPENAI_API_KEY }}"},
              {"name": "MINIMAX_API_KEY", "value": "${{ secrets.MINIMAX_API_KEY }}"},
              {"name": "DATABASE_URL", "value": "${{ secrets.AZURE_DB_CONNECTION_STRING }}"}
            ]
      
      - name: Logout from Azure
        run: az logout
```

---

## 5. Frontend CI Pipeline

### 5.1 Frontend CI Workflow (.github/workflows/frontend-ci.yml)

```yaml
name: Frontend CI

on:
  push:
    branches: [main, develop]
    paths:
      - 'frontend/**'
      - '.github/workflows/frontend-*.yml'
  pull_request:
    branches: [main, develop]
    paths:
      - 'frontend/**'

defaults:
  run:
    working-directory: frontend

jobs:
  lint:
    name: Lint & Type Check
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Node.js
        uses: actions/setup-node@v4
        with:
          node-version: '20'
          cache: 'npm'
          cache-dependency-path: frontend/package-lock.json
      
      - name: Install dependencies
        run: npm ci
      
      - name: Run ESLint
        run: npm run lint
      
      - name: Run TypeScript check
        run: npm run type-check

  test:
    name: Unit Tests
    runs-on: ubuntu-latest
    needs: lint
    
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Node.js
        uses: actions/setup-node@v4
        with:
          node-version: '20'
          cache: 'npm'
          cache-dependency-path: frontend/package-lock.json
      
      - name: Install dependencies
        run: npm ci
      
      - name: Run tests
        run: npm run test -- --coverage --watchAll=false
      
      - name: Upload coverage
        uses: codecov/codecov-action@v4
        with:
          files: ./frontend/coverage/lcov.info
          fail_ci_if_error: false

  build:
    name: Build
    runs-on: ubuntu-latest
    needs: test
    
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Node.js
        uses: actions/setup-node@v4
        with:
          node-version: '20'
          cache: 'npm'
          cache-dependency-path: frontend/package-lock.json
      
      - name: Install dependencies
        run: npm ci
      
      - name: Build
        env:
          VITE_API_URL: ${{ vars.VITE_API_URL }}
          VITE_AZURE_CLIENT_ID: ${{ vars.VITE_AZURE_CLIENT_ID }}
          VITE_AZURE_TENANT_ID: ${{ vars.VITE_AZURE_TENANT_ID }}
        run: npm run build
      
      - name: Upload build artifact
        uses: actions/upload-artifact@v4
        with:
          name: frontend-build
          path: frontend/dist
```

### 5.2 Frontend Deployment (.github/workflows/frontend-deploy.yml)

```yaml
name: Frontend Deploy

on:
  push:
    branches: [main]
    paths:
      - 'frontend/**'
  workflow_dispatch:

defaults:
  run:
    working-directory: frontend

jobs:
  deploy:
    name: Deploy to Azure Static Web Apps
    runs-on: ubuntu-latest
    environment: production
    
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Node.js
        uses: actions/setup-node@v4
        with:
          node-version: '20'
          cache: 'npm'
          cache-dependency-path: frontend/package-lock.json
      
      - name: Install dependencies
        run: npm ci
      
      - name: Build
        env:
          VITE_API_URL: ${{ vars.VITE_API_URL_PROD }}
          VITE_AZURE_CLIENT_ID: ${{ secrets.AZURE_CLIENT_ID }}
          VITE_AZURE_TENANT_ID: ${{ secrets.AZURE_TENANT_ID }}
          VITE_AZURE_REDIRECT_URI: ${{ vars.VITE_REDIRECT_URI_PROD }}
        run: npm run build
      
      - name: Deploy to Azure Static Web Apps
        uses: Azure/static-web-apps-deploy@v1
        with:
          azure_static_web_apps_api_token: ${{ secrets.AZURE_SWA_TOKEN }}
          repo_token: ${{ secrets.GITHUB_TOKEN }}
          action: "upload"
          app_location: "/frontend"
          output_location: "dist"
          skip_app_build: true
```

---

## 6. E2E Testing Pipeline

### 6.1 E2E Test Workflow (.github/workflows/e2e-tests.yml)

```yaml
name: E2E Tests

on:
  pull_request:
    branches: [main]
  schedule:
    - cron: '0 6 * * *'  # Daily at 6 AM UTC
  workflow_dispatch:

jobs:
  e2e:
    name: Playwright E2E Tests
    runs-on: ubuntu-latest
    timeout-minutes: 30
    
    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_USER: test
          POSTGRES_PASSWORD: test
          POSTGRES_DB: test_db
        ports:
          - 5432:5432
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
    
    steps:
      - uses: actions/checkout@v4
      
      # Setup Backend
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      
      - name: Install uv
        uses: astral-sh/setup-uv@v4
      
      - name: Install backend dependencies
        working-directory: backend
        run: uv sync --dev
      
      - name: Start backend server
        working-directory: backend
        env:
          DATABASE_URL: postgresql+asyncpg://test:test@localhost:5432/test_db
          OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
          MINIMAX_API_KEY: ${{ secrets.MINIMAX_API_KEY }}
        run: |
          uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 &
          sleep 5
      
      # Setup Frontend
      - name: Set up Node.js
        uses: actions/setup-node@v4
        with:
          node-version: '20'
          cache: 'npm'
          cache-dependency-path: frontend/package-lock.json
      
      - name: Install frontend dependencies
        working-directory: frontend
        run: npm ci
      
      - name: Install Playwright browsers
        working-directory: frontend
        run: npx playwright install --with-deps chromium
      
      - name: Start frontend dev server
        working-directory: frontend
        env:
          VITE_API_URL: http://localhost:8000/api/v1
          VITE_AZURE_CLIENT_ID: test-client-id
          VITE_AZURE_TENANT_ID: test-tenant-id
        run: |
          npm run dev &
          sleep 5
      
      # Run E2E Tests
      - name: Run Playwright tests
        working-directory: frontend
        run: npx playwright test
      
      - name: Upload test results
        uses: actions/upload-artifact@v4
        if: always()
        with:
          name: playwright-report
          path: frontend/playwright-report/
          retention-days: 7
```

---

## 7. Azure Resources Setup (Bicep)

### 7.1 Infrastructure as Code (infra/main.bicep)

```bicep
@description('Environment name')
param environmentName string = 'prod'

@description('Location for all resources')
param location string = resourceGroup().location

@description('App Service Plan SKU')
param appServicePlanSku string = 'B1'

var resourceToken = toLower(uniqueString(resourceGroup().id, environmentName))
var appServicePlanName = 'plan-aivideo-${resourceToken}'
var webAppName = 'app-aivideo-backend-${resourceToken}'
var staticWebAppName = 'swa-aivideo-frontend-${resourceToken}'
var dbServerName = 'psql-aivideo-${resourceToken}'
var dbName = 'videocreator'

// App Service Plan
resource appServicePlan 'Microsoft.Web/serverfarms@2022-09-01' = {
  name: appServicePlanName
  location: location
  sku: {
    name: appServicePlanSku
  }
  kind: 'linux'
  properties: {
    reserved: true
  }
}

// Web App (Backend)
resource webApp 'Microsoft.Web/sites@2022-09-01' = {
  name: webAppName
  location: location
  properties: {
    serverFarmId: appServicePlan.id
    siteConfig: {
      linuxFxVersion: 'PYTHON|3.11'
      appCommandLine: 'uvicorn app.main:app --host 0.0.0.0 --port 8000'
      alwaysOn: true
    }
    httpsOnly: true
  }
}

// Static Web App (Frontend)
resource staticWebApp 'Microsoft.Web/staticSites@2022-09-01' = {
  name: staticWebAppName
  location: location
  sku: {
    name: 'Standard'
    tier: 'Standard'
  }
  properties: {
    stagingEnvironmentPolicy: 'Enabled'
    allowConfigFileUpdates: true
  }
}

// PostgreSQL Flexible Server
resource dbServer 'Microsoft.DBforPostgreSQL/flexibleServers@2022-12-01' = {
  name: dbServerName
  location: location
  sku: {
    name: 'Standard_B1ms'
    tier: 'Burstable'
  }
  properties: {
    version: '15'
    administratorLogin: 'adminuser'
    administratorLoginPassword: '${uniqueString(resourceGroup().id)}P@ss!'
    storage: {
      storageSizeGB: 32
    }
    backup: {
      backupRetentionDays: 7
      geoRedundantBackup: 'Disabled'
    }
  }
}

// Database
resource database 'Microsoft.DBforPostgreSQL/flexibleServers/databases@2022-12-01' = {
  parent: dbServer
  name: dbName
  properties: {
    charset: 'UTF8'
    collation: 'en_US.utf8'
  }
}

// Outputs
output webAppUrl string = 'https://${webApp.properties.defaultHostName}'
output staticWebAppUrl string = 'https://${staticWebApp.properties.defaultHostname}'
output dbConnectionString string = 'postgresql+asyncpg://adminuser:${uniqueString(resourceGroup().id)}P@ss!@${dbServer.properties.fullyQualifiedDomainName}:5432/${dbName}'
```

### 7.2 Deploy Infrastructure

```bash
# Create resource group
az group create --name rg-aivideo-prod --location eastus

# Deploy Bicep template
az deployment group create \
  --resource-group rg-aivideo-prod \
  --template-file infra/main.bicep \
  --parameters environmentName=prod

# Get Static Web App deployment token
az staticwebapp secrets list \
  --name <static-web-app-name> \
  --query "properties.apiKey" -o tsv
```

---

## 8. Deployment Checklist

### Before First Deployment

- [ ] Azure subscription active
- [ ] Resource group created
- [ ] Service principal created with Contributor role
- [ ] GitHub secrets configured
- [ ] Azure Entra ID app registration complete
- [ ] Database provisioned and migrations ready

### For Each Release

- [ ] All tests passing in CI
- [ ] Version bumped (if applicable)
- [ ] Changelog updated
- [ ] Environment variables verified
- [ ] Database migrations prepared

### Post-Deployment

- [ ] Health check endpoint responds
- [ ] Authentication flow works
- [ ] API endpoints accessible
- [ ] Logs accessible in Azure Portal
- [ ] Monitoring alerts configured

---

## 9. Next Steps

After setting up CI/CD:

1. **Test the pipeline:**
   - Push a change to trigger CI
   - Verify all checks pass
   - Deploy to staging environment

2. **Configure monitoring:**
   - Set up Azure Application Insights
   - Configure alerts for errors

3. **Proceed to E2E Testing:**
   - See [08-E2E-TESTING.md](./08-E2E-TESTING.md)
