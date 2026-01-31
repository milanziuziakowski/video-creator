# AI Video Creator Frontend - Setup Script
# Run this from the frontend directory: .\setup.ps1

param(
    [switch]$SkipInstall,
    [switch]$Production,
    [switch]$Clean
)

$ErrorActionPreference = "Stop"

Write-Host "=== AI Video Creator Frontend Setup ===" -ForegroundColor Cyan

# Clean previous installations if requested
if ($Clean) {
    Write-Host "`nCleaning previous installation..." -ForegroundColor Yellow
    if (Test-Path "node_modules") {
        Remove-Item -Recurse -Force "node_modules"
        Write-Host "Removed node_modules" -ForegroundColor Green
    }
    if (Test-Path "dist") {
        Remove-Item -Recurse -Force "dist"
        Write-Host "Removed dist" -ForegroundColor Green
    }
    if (Test-Path "package-lock.json") {
        Remove-Item -Force "package-lock.json"
        Write-Host "Removed package-lock.json" -ForegroundColor Green
    }
}

# Check Node.js version
Write-Host "`nChecking Node.js version..." -ForegroundColor Yellow
try {
    $nodeVersion = node --version 2>&1
    if ($LASTEXITCODE -ne 0) {
        throw "Node.js not found"
    }
    
    # Extract major version number
    $majorVersion = [int]($nodeVersion -replace 'v(\d+)\..*', '$1')
    
    if ($majorVersion -lt 18) {
        Write-Host "WARNING: Node.js $nodeVersion detected. Version 18+ is recommended." -ForegroundColor Yellow
        Write-Host "Download from: https://nodejs.org/" -ForegroundColor Yellow
    } else {
        Write-Host "Found: Node.js $nodeVersion" -ForegroundColor Green
    }
} catch {
    Write-Host "ERROR: Node.js not found. Please install Node.js 18+ from https://nodejs.org/" -ForegroundColor Red
    exit 1
}

# Check npm version
Write-Host "`nChecking npm version..." -ForegroundColor Yellow
try {
    $npmVersion = npm --version 2>&1
    if ($LASTEXITCODE -ne 0) {
        throw "npm not found"
    }
    Write-Host "Found: npm $npmVersion" -ForegroundColor Green
} catch {
    Write-Host "ERROR: npm not found. It should be installed with Node.js." -ForegroundColor Red
    exit 1
}

# Check for .env file
Write-Host "`nChecking environment configuration..." -ForegroundColor Yellow
if (-Not (Test-Path ".env")) {
    if (Test-Path ".env.example") {
        Write-Host "Creating .env from .env.example..." -ForegroundColor Yellow
        Copy-Item ".env.example" ".env"
        Write-Host "Created .env file. Please update it with your configuration." -ForegroundColor Yellow
    } else {
        Write-Host "WARNING: No .env file found. You may need to create one." -ForegroundColor Yellow
    }
} else {
    Write-Host ".env file exists" -ForegroundColor Green
}

# Install dependencies
if (-Not $SkipInstall) {
    Write-Host "`nInstalling dependencies..." -ForegroundColor Yellow
    
    # Use npm ci for clean installs (faster, deterministic) if lock file exists
    if (Test-Path "package-lock.json") {
        Write-Host "Using npm ci for clean install..." -ForegroundColor Cyan
        npm ci
    } else {
        Write-Host "Using npm install..." -ForegroundColor Cyan
        npm install
    }
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host "ERROR: Failed to install dependencies" -ForegroundColor Red
        exit 1
    }
    Write-Host "Dependencies installed successfully" -ForegroundColor Green
} else {
    Write-Host "`nSkipping dependency installation (--SkipInstall flag)" -ForegroundColor Yellow
}

# Build for production if requested
if ($Production) {
    Write-Host "`nBuilding for production..." -ForegroundColor Yellow
    npm run build
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host "ERROR: Production build failed" -ForegroundColor Red
        exit 1
    }
    
    # Show build output stats
    if (Test-Path "dist") {
        $distSize = (Get-ChildItem -Path "dist" -Recurse | Measure-Object -Property Length -Sum).Sum
        $distSizeMB = [math]::Round($distSize / 1MB, 2)
        Write-Host "Build successful! Output size: ${distSizeMB}MB" -ForegroundColor Green
    }
}

# Run linting check
Write-Host "`nRunning lint check..." -ForegroundColor Yellow
npm run lint 2>&1 | Out-Null
if ($LASTEXITCODE -eq 0) {
    Write-Host "Lint check passed" -ForegroundColor Green
} else {
    Write-Host "Lint issues found. Run 'npm run lint' to see details." -ForegroundColor Yellow
}

Write-Host "`n=== Setup Complete ===" -ForegroundColor Cyan
Write-Host "`nInstalled packages:" -ForegroundColor Yellow

# Show key dependencies
$packageJson = Get-Content "package.json" | ConvertFrom-Json
Write-Host "  React: $($packageJson.dependencies.react)" -ForegroundColor White
Write-Host "  React Router: $($packageJson.dependencies.'react-router-dom')" -ForegroundColor White
Write-Host "  Vite: $($packageJson.devDependencies.vite)" -ForegroundColor White
Write-Host "  TypeScript: $($packageJson.devDependencies.typescript)" -ForegroundColor White

Write-Host "`n=== Quick Commands ===" -ForegroundColor Cyan
Write-Host "Start dev server:     npm run dev" -ForegroundColor White
Write-Host "Build production:     npm run build" -ForegroundColor White
Write-Host "Preview build:        npm run preview" -ForegroundColor White
Write-Host "Run linter:           npm run lint" -ForegroundColor White
Write-Host "Format code:          npm run format" -ForegroundColor White

Write-Host "`n=== Script Options ===" -ForegroundColor Cyan
Write-Host ".\setup.ps1                    # Full setup with npm install" -ForegroundColor White
Write-Host ".\setup.ps1 -SkipInstall       # Skip npm install" -ForegroundColor White
Write-Host ".\setup.ps1 -Production        # Install and build for production" -ForegroundColor White
Write-Host ".\setup.ps1 -Clean             # Clean and reinstall everything" -ForegroundColor White
Write-Host ".\setup.ps1 -Clean -Production # Full clean rebuild" -ForegroundColor White

Write-Host "`nFrontend is ready for development!" -ForegroundColor Green
