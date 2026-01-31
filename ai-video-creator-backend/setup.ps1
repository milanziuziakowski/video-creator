# AI Video Creator Backend - Setup Script
# Run this from the backend directory: .\setup.ps1

$ErrorActionPreference = "Stop"
$VenvPath = ".\.venv"

Write-Host "=== AI Video Creator Backend Setup ===" -ForegroundColor Cyan

# Check Python version
Write-Host "`nChecking Python version..." -ForegroundColor Yellow
$pythonVersion = python --version 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Python not found. Please install Python 3.11+" -ForegroundColor Red
    exit 1
}
Write-Host "Found: $pythonVersion" -ForegroundColor Green

# Create virtual environment if it doesn't exist
if (-Not (Test-Path $VenvPath)) {
    Write-Host "`nCreating virtual environment..." -ForegroundColor Yellow
    python -m venv $VenvPath
    if ($LASTEXITCODE -ne 0) {
        Write-Host "ERROR: Failed to create virtual environment" -ForegroundColor Red
        exit 1
    }
    Write-Host "Virtual environment created at $VenvPath" -ForegroundColor Green
} else {
    Write-Host "`nVirtual environment already exists at $VenvPath" -ForegroundColor Green
}

# Activate virtual environment
Write-Host "`nActivating virtual environment..." -ForegroundColor Yellow
& "$VenvPath\Scripts\Activate.ps1"

# Upgrade pip
Write-Host "`nUpgrading pip..." -ForegroundColor Yellow
python -m pip install --upgrade pip

# Install package with dev dependencies
Write-Host "`nInstalling package with dev dependencies..." -ForegroundColor Yellow
pip install -e ".[dev]"

if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Failed to install dependencies" -ForegroundColor Red
    exit 1
}

# Verify installation
Write-Host "`n=== Installation Complete ===" -ForegroundColor Cyan
Write-Host "`nInstalled packages:" -ForegroundColor Yellow
pip list

Write-Host "`n=== Quick Commands ===" -ForegroundColor Cyan
Write-Host "Activate venv:    .\.venv\Scripts\Activate.ps1" -ForegroundColor White
Write-Host "Run server:       uvicorn app.main:app --reload" -ForegroundColor White
Write-Host "Run all tests:    pytest -v" -ForegroundColor White
Write-Host "Run E2E tests:    pytest -m e2e -v" -ForegroundColor White
Write-Host "Deactivate:       deactivate" -ForegroundColor White

Write-Host "`nVirtual environment is now ACTIVE" -ForegroundColor Green
