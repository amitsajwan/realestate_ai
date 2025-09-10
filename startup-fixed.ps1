# =============================================================================
# PROPERTYAI - SIMPLIFIED DEPLOYMENT SCRIPT
# =============================================================================
# Fixed PowerShell syntax, no && operators, proper command chaining
# Handles: Frontend Build, Backend Build, Docker, Testing

param(
    [Parameter(Mandatory=$false)]
    [ValidateSet("build-frontend", "build-backend", "build-images", "full-deploy", "test-playwright", "test-backend", "cleanup", "status")]
    [string]$Mode = "status",
    
    [Parameter(Mandatory=$false)]
    [switch]$SkipFacebook = $false,
    
    [Parameter(Mandatory=$false)]
    [switch]$Force = $false,
    
    [Parameter(Mandatory=$false)]
    [switch]$Interactive = $true
)

# Configuration
$SCRIPT_VERSION = "2.0.0"
$PROJECT_NAME = "PropertyAI"
$BACKEND_PORT = 8000
$FRONTEND_PORT = 3000

# Colors for output
function Write-ColorOutput {
    param([string]$Message, [string]$Color = "White")
    $OriginalColor = $Host.UI.RawUI.ForegroundColor
    $Host.UI.RawUI.ForegroundColor = [ConsoleColor]::$Color
    Write-Host $Message
    $Host.UI.RawUI.ForegroundColor = $OriginalColor
}

function Write-Header {
    param([string]$Title)
    Write-Host ""
    Write-ColorOutput "==================================================================================" "Cyan"
    Write-ColorOutput "  $Title" "Cyan"
    Write-ColorOutput "==================================================================================" "Cyan"
    Write-Host ""
}

function Write-Step {
    param([string]$Step, [string]$Description = "")
    Write-ColorOutput "[$Step]" "Yellow" -NoNewline
    Write-Host " $Description"
}

function Write-Success {
    param([string]$Message)
    Write-ColorOutput "[OK] $Message" "Green"
}

function Write-Error {
    param([string]$Message)
    Write-ColorOutput "[ERROR] $Message" "Red"
}

function Write-Warning {
    param([string]$Message)
    Write-ColorOutput "[WARN] $Message" "Yellow"
}

function Test-Port {
    param([int]$Port)
    try {
        $connection = New-Object System.Net.Sockets.TcpClient
        $connection.Connect("localhost", $Port)
        $connection.Close()
        return $true
    } catch {
        return $false
    }
}

function Build-Frontend {
    Write-Header "Building Frontend"
    
    try {
        Push-Location frontend
        
        Write-Step "FRONTEND" "Installing dependencies..."
        npm install
        
        Write-Step "FRONTEND" "Building production version..."
        npm run build
        
        Write-Success "Frontend built successfully"
        Pop-Location
        return $true
        
    } catch {
        Write-Error "Frontend build failed: $($_.Exception.Message)"
        Pop-Location
        return $false
    }
}

function Build-Backend {
    Write-Header "Building Backend"
    
    try {
        Push-Location backend
        
        # Create virtual environment if it doesn't exist
        if (!(Test-Path ".venv")) {
            Write-Step "BACKEND" "Creating virtual environment..."
            python -m venv .venv
        }
        
        # Activate virtual environment
        Write-Step "BACKEND" "Activating virtual environment..."
        & .\.venv\Scripts\Activate.ps1
        
        # Install dependencies
        Write-Step "BACKEND" "Installing dependencies..."
        pip install -r requirements.txt
        
        Write-Success "Backend built successfully"
        Pop-Location
        return $true
        
    } catch {
        Write-Error "Backend build failed: $($_.Exception.Message)"
        Pop-Location
        return $false
    }
}

function Build-DockerImages {
    Write-Header "Building Docker Images"
    
    try {
        # Build backend image
        Write-Step "DOCKER" "Building backend image..."
        Push-Location backend
        docker build -t propertyai-backend .
        Pop-Location
        
        # Build frontend image
        Write-Step "DOCKER" "Building frontend image..."
        Push-Location frontend
        docker build -f Dockerfile.frontend -t propertyai-frontend .
        Pop-Location
        
        Write-Success "Docker images built successfully"
        return $true
        
    } catch {
        Write-Error "Docker build failed: $($_.Exception.Message)"
        return $false
    }
}

function Start-FullDeploy {
    Write-Header "Full Deployment"
    
    # Build frontend
    if (!(Build-Frontend)) {
        Write-Error "Frontend build failed. Aborting deployment."
        return $false
    }
    
    # Build backend
    if (!(Build-Backend)) {
        Write-Error "Backend build failed. Aborting deployment."
        return $false
    }
    
    # Build Docker images
    if (!(Build-DockerImages)) {
        Write-Error "Docker build failed. Aborting deployment."
        return $false
    }
    
    # Start with Docker Compose
    Write-Step "DEPLOY" "Starting with Docker Compose..."
    Push-Location docker
    docker-compose up -d
    Pop-Location
    
    Write-Success "Full deployment completed"
    return $true
}

function Test-Playwright {
    Write-Header "Running Playwright Tests"
    
    try {
        Write-Step "TEST" "Installing Playwright dependencies..."
        npm install
        
        Write-Step "TEST" "Running Playwright tests..."
        npx playwright test
        
        Write-Success "Playwright tests completed"
        return $true
        
    } catch {
        Write-Error "Playwright tests failed: $($_.Exception.Message)"
        return $false
    }
}

function Test-Backend {
    Write-Header "Running Backend Tests"
    
    try {
        Push-Location backend
        
        # Activate virtual environment
        & .\.venv\Scripts\Activate.ps1
        
        Write-Step "TEST" "Running backend tests..."
        python -m pytest tests/ -v
        
        Write-Success "Backend tests completed"
        Pop-Location
        return $true
        
    } catch {
        Write-Error "Backend tests failed: $($_.Exception.Message)"
        Pop-Location
        return $false
    }
}

function Cleanup-All {
    Write-Header "Cleanup"
    
    try {
        # Stop Docker containers
        Write-Step "CLEANUP" "Stopping Docker containers..."
        Push-Location docker
        docker-compose down
        Pop-Location
        
        # Remove Docker images
        Write-Step "CLEANUP" "Removing Docker images..."
        docker rmi propertyai-backend propertyai-frontend -f
        
        # Clean up build artifacts
        Write-Step "CLEANUP" "Cleaning build artifacts..."
        if (Test-Path "frontend/.next") {
            Remove-Item "frontend/.next" -Recurse -Force
        }
        if (Test-Path "frontend/out") {
            Remove-Item "frontend/out" -Recurse -Force
        }
        
        Write-Success "Cleanup completed"
        return $true
        
    } catch {
        Write-Error "Cleanup failed: $($_.Exception.Message)"
        return $false
    }
}

function Show-Status {
    Write-Header "System Status"
    
    # Check ports
    if (Test-Port $BACKEND_PORT) {
        Write-ColorOutput "Backend: " "White" -NoNewline
        Write-ColorOutput "[RUNNING] Port $BACKEND_PORT" "Green"
    } else {
        Write-ColorOutput "Backend: " "White" -NoNewline
        Write-ColorOutput "[STOPPED]" "Red"
    }
    
    if (Test-Port $FRONTEND_PORT) {
        Write-ColorOutput "Frontend: " "White" -NoNewline
        Write-ColorOutput "[RUNNING] Port $FRONTEND_PORT" "Green"
    } else {
        Write-ColorOutput "Frontend: " "White" -NoNewline
        Write-ColorOutput "[STOPPED]" "Red"
    }
    
    # Check Docker
    try {
        $dockerInfo = docker info 2>$null
        if ($LASTEXITCODE -eq 0) {
            Write-ColorOutput "Docker: " "White" -NoNewline
            Write-ColorOutput "[RUNNING]" "Green"
        } else {
            Write-ColorOutput "Docker: " "White" -NoNewline
            Write-ColorOutput "[NOT RUNNING]" "Red"
        }
    } catch {
        Write-ColorOutput "Docker: " "White" -NoNewline
        Write-ColorOutput "[NOT INSTALLED]" "Red"
    }
    
    Write-Host ""
    Write-ColorOutput "Available Commands:" "Cyan"
    Write-Host "  .\startup-fixed.ps1 -Mode build-frontend    # Build frontend only"
    Write-Host "  .\startup-fixed.ps1 -Mode build-backend     # Build backend only"
    Write-Host "  .\startup-fixed.ps1 -Mode build-images      # Build Docker images"
    Write-Host "  .\startup-fixed.ps1 -Mode full-deploy       # Full deployment"
    Write-Host "  .\startup-fixed.ps1 -Mode test-playwright   # Run Playwright tests"
    Write-Host "  .\startup-fixed.ps1 -Mode test-backend      # Run backend tests"
    Write-Host "  .\startup-fixed.ps1 -Mode cleanup           # Cleanup everything"
}

# Main execution
Write-Header "$PROJECT_NAME Deployment Script v$SCRIPT_VERSION"

switch ($Mode) {
    "build-frontend" {
        Build-Frontend
    }
    
    "build-backend" {
        Build-Backend
    }
    
    "build-images" {
        Build-DockerImages
    }
    
    "full-deploy" {
        Start-FullDeploy
    }
    
    "test-playwright" {
        Test-Playwright
    }
    
    "test-backend" {
        Test-Backend
    }
    
    "cleanup" {
        Cleanup-All
    }
    
    "status" {
        Show-Status
    }
    
    default {
        Show-Status
    }
}

Write-Host ""
