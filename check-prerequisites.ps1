# =============================================================================
# PREREQUISITES CHECK SCRIPT
# =============================================================================
# This script checks if all prerequisites are met before deployment

Write-Host "🔍 Checking Prerequisites for ngrok + Docker Deployment..." -ForegroundColor Cyan
Write-Host ""

# Colors for output
function Write-ColorOutput {
    param([string]$Message, [string]$Color = "White")
    $OriginalColor = $Host.UI.RawUI.ForegroundColor
    $Host.UI.RawUI.ForegroundColor = [ConsoleColor]::$Color
    Write-Host $Message
    $Host.UI.RawUI.ForegroundColor = $OriginalColor
}

function Write-Success {
    param([string]$Message)
    Write-ColorOutput "✅ $Message" "Green"
}

function Write-Error {
    param([string]$Message)
    Write-ColorOutput "❌ $Message" "Red"
}

function Write-Warning {
    param([string]$Message)
    Write-ColorOutput "⚠️ $Message" "Yellow"
}

# Check Docker
Write-Host "1. Checking Docker..." -ForegroundColor Yellow
try {
    $dockerVersion = docker --version 2>$null
    if ($dockerVersion) {
        Write-Success "Docker is installed: $dockerVersion"
    } else {
        Write-Error "Docker is not installed or not in PATH"
        exit 1
    }
} catch {
    Write-Error "Docker is not installed or not in PATH"
    Write-Host "Please install Docker Desktop from https://www.docker.com/products/docker-desktop/"
    exit 1
}

# Check if Docker is running
try {
    $null = docker info 2>$null
    Write-Success "Docker is running"
} catch {
    Write-Error "Docker is not running"
    Write-Host "Please start Docker Desktop and wait for it to be ready"
    exit 1
}

# Check ngrok
Write-Host "2. Checking ngrok..." -ForegroundColor Yellow
try {
    $ngrokVersion = ngrok version 2>$null
    if ($ngrokVersion) {
        Write-Success "ngrok is installed: $ngrokVersion"
    } else {
        Write-Error "ngrok is not installed or not in PATH"
        Write-Host "Please install ngrok from https://ngrok.com/download"
        exit 1
    }
} catch {
    Write-Error "ngrok is not installed or not in PATH"
    Write-Host "Please install ngrok from https://ngrok.com/download"
    exit 1
}

# Check required files
Write-Host "3. Checking required files..." -ForegroundColor Yellow

$requiredFiles = @(
    "docker-compose.yml",
    "docker-compose.ngrok.yml", 
    "docker/nginx-ngrok.conf",
    "ngrok.yml",
    "start-ngrok-docker-external.ps1"
)

$allFilesExist = $true
foreach ($file in $requiredFiles) {
    if (Test-Path $file) {
        Write-Success "Found: $file"
    } else {
        Write-Error "Missing: $file"
        $allFilesExist = $false
    }
}

if (!$allFilesExist) {
    Write-Error "Some required files are missing. Please run setup first."
    exit 1
}

# Check source code
Write-Host "4. Checking source code..." -ForegroundColor Yellow
if (Test-Path "backend" -PathType Container) {
    Write-Success "Backend source code found"
} else {
    Write-Error "Backend source code not found"
    exit 1
}

if (Test-Path "frontend" -PathType Container) {
    Write-Success "Frontend source code found"
} else {
    Write-Error "Frontend source code not found"
    exit 1
}

# Check Dockerfiles
Write-Host "5. Checking Dockerfiles..." -ForegroundColor Yellow
if (Test-Path "backend/Dockerfile") {
    Write-Success "Backend Dockerfile found"
} else {
    Write-Error "Backend Dockerfile not found"
    exit 1
}

if (Test-Path "frontend/Dockerfile") {
    Write-Success "Frontend Dockerfile found"
} else {
    Write-Error "Frontend Dockerfile not found"
    exit 1
}

Write-Host ""
Write-ColorOutput "🎉 All prerequisites are met! Ready to deploy." "Green"
Write-Host ""
Write-ColorOutput "Next steps:" "Cyan"
Write-Host "1. Run: .\start-ngrok-docker-external.ps1"
Write-Host "2. Wait for deployment to complete"
Write-Host "3. Check ngrok dashboard at http://localhost:4040"
Write-Host "4. Access your application via the ngrok URL"