# AI Video Creator - Container Apps Deployment Script
# This script deploys the frontend to Azure Container Apps
# Prerequisites: Azure CLI installed, logged in to Azure

param(
    [Parameter(Mandatory=$false)]
    [string]$Environment = "dev",
    
    [Parameter(Mandatory=$false)]
    [string]$ProjectName = "aivideocreator",
    
    [Parameter(Mandatory=$false)]
    [string]$Location = "westeurope",
    
    [Parameter(Mandatory=$false)]
    [string]$ImageTag = "latest",
    
    [switch]$BuildOnly,
    [switch]$DeployOnly,
    [switch]$SkipBuild
)

$ErrorActionPreference = "Stop"

# ============================================================================
# Variables
# ============================================================================
$ResourceGroup = "rg-$ProjectName-$Environment"
$ContainerRegistry = "cr$ProjectName$Environment"
$ContainerAppName = "ca-$ProjectName-frontend-$Environment"
$ImageName = "frontend"
$FullImageName = "$ContainerRegistry.azurecr.io/${ImageName}:$ImageTag"

Write-Host "=== AI Video Creator - Container Apps Deployment ===" -ForegroundColor Cyan
Write-Host "Environment: $Environment" -ForegroundColor Yellow
Write-Host "Resource Group: $ResourceGroup" -ForegroundColor Yellow
Write-Host "Container Registry: $ContainerRegistry" -ForegroundColor Yellow
Write-Host "Image: $FullImageName" -ForegroundColor Yellow

# ============================================================================
# Check Prerequisites
# ============================================================================
Write-Host "`nChecking prerequisites..." -ForegroundColor Yellow

# Check Azure CLI
try {
    $azVersion = az version --output json | ConvertFrom-Json
    Write-Host "Azure CLI: $($azVersion.'azure-cli')" -ForegroundColor Green
} catch {
    Write-Host "ERROR: Azure CLI not found. Install from https://docs.microsoft.com/cli/azure/install-azure-cli" -ForegroundColor Red
    exit 1
}

# Check Docker
if (-Not $DeployOnly) {
    try {
        $dockerVersion = docker --version
        Write-Host "Docker: $dockerVersion" -ForegroundColor Green
    } catch {
        Write-Host "ERROR: Docker not found. Install Docker Desktop." -ForegroundColor Red
        exit 1
    }
}

# Check Azure login
$account = az account show 2>$null | ConvertFrom-Json
if (-Not $account) {
    Write-Host "Not logged in to Azure. Running az login..." -ForegroundColor Yellow
    az login
}
Write-Host "Logged in as: $($account.user.name)" -ForegroundColor Green

# ============================================================================
# Build Docker Image
# ============================================================================
if (-Not $DeployOnly -And -Not $SkipBuild) {
    Write-Host "`n=== Building Docker Image ===" -ForegroundColor Cyan
    
    # Navigate to frontend directory
    $frontendPath = Join-Path $PSScriptRoot ".." "ai-video-creator-frontend"
    Push-Location $frontendPath
    
    try {
        Write-Host "Building image: $FullImageName" -ForegroundColor Yellow
        docker build -t $FullImageName -t "${ContainerRegistry}.azurecr.io/${ImageName}:latest" .
        
        if ($LASTEXITCODE -ne 0) {
            throw "Docker build failed"
        }
        Write-Host "Docker build successful" -ForegroundColor Green
    }
    finally {
        Pop-Location
    }
    
    if ($BuildOnly) {
        Write-Host "`nBuild complete. Use -DeployOnly to push and deploy." -ForegroundColor Green
        exit 0
    }
}

# ============================================================================
# Push to Azure Container Registry
# ============================================================================
Write-Host "`n=== Pushing to Azure Container Registry ===" -ForegroundColor Cyan

# Login to ACR
Write-Host "Logging in to ACR: $ContainerRegistry" -ForegroundColor Yellow
az acr login --name $ContainerRegistry

if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Failed to login to ACR. Ensure the registry exists." -ForegroundColor Red
    exit 1
}

# Push image
Write-Host "Pushing image: $FullImageName" -ForegroundColor Yellow
docker push $FullImageName
docker push "${ContainerRegistry}.azurecr.io/${ImageName}:latest"

if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Failed to push image to ACR" -ForegroundColor Red
    exit 1
}
Write-Host "Image pushed successfully" -ForegroundColor Green

# ============================================================================
# Update Container App
# ============================================================================
Write-Host "`n=== Updating Container App ===" -ForegroundColor Cyan

Write-Host "Updating Container App: $ContainerAppName" -ForegroundColor Yellow

# Update the container app with the new image
az containerapp update `
    --name $ContainerAppName `
    --resource-group $ResourceGroup `
    --image $FullImageName

if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Failed to update Container App" -ForegroundColor Red
    exit 1
}

# Get the Container App URL
$appUrl = az containerapp show `
    --name $ContainerAppName `
    --resource-group $ResourceGroup `
    --query "properties.configuration.ingress.fqdn" `
    --output tsv

Write-Host "`n=== Deployment Complete ===" -ForegroundColor Cyan
Write-Host "Container App URL: https://$appUrl" -ForegroundColor Green
Write-Host "`nTo view logs:" -ForegroundColor Yellow
Write-Host "az containerapp logs show --name $ContainerAppName --resource-group $ResourceGroup --follow" -ForegroundColor White
