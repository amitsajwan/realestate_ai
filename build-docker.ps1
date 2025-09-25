# Docker Build Script for Real Estate Platform
# ============================================
# This script builds all Docker images for the platform

param(
    [string]$BuildType = "all",
    [string]$Environment = "development",
    [switch]$PushImages = $false,
    [switch]$Help = $false
)

# Colors for output
$RED = "Red"
$GREEN = "Green"
$YELLOW = "Yellow"
$BLUE = "Blue"

# Logging functions
function Write-Info {
    param([string]$Message)
    Write-Host "[INFO] $Message" -ForegroundColor $BLUE
}

function Write-Success {
    param([string]$Message)
    Write-Host "[SUCCESS] $Message" -ForegroundColor $GREEN
}

function Write-Warning {
    param([string]$Message)
    Write-Host "[WARNING] $Message" -ForegroundColor $YELLOW
}

function Write-Error {
    param([string]$Message)
    Write-Host "[ERROR] $Message" -ForegroundColor $RED
}

# Help function
function Show-Help {
    Write-Host "Docker Build Script for Real Estate Platform" -ForegroundColor $GREEN
    Write-Host "============================================" -ForegroundColor $GREEN
    Write-Host ""
    Write-Host "Usage: .\build-docker.ps1 [-BuildType <type>] [-Environment <env>] [-PushImages] [-Help]"
    Write-Host ""
    Write-Host "Parameters:"
    Write-Host "  -BuildType    - What to build (all|backend|frontend|services) [default: all]"
    Write-Host "  -Environment  - Target environment (development|production) [default: development]"
    Write-Host "  -PushImages   - Push images to registry [default: false]"
    Write-Host "  -Help         - Show this help message"
    Write-Host ""
    Write-Host "Examples:"
    Write-Host "  .\build-docker.ps1                                    # Build all images for development"
    Write-Host "  .\build-docker.ps1 -BuildType backend                # Build only backend"
    Write-Host "  .\build-docker.ps1 -Environment production          # Build for production"
    Write-Host "  .\build-docker.ps1 -PushImages                       # Build and push to registry"
    Write-Host ""
}

# Validate build type
function Test-BuildType {
    param([string]$Type)
    $validTypes = @("all", "backend", "frontend", "services")
    if ($Type -notin $validTypes) {
        Write-Error "Invalid build type: $Type"
        Write-Error "Valid build types: $($validTypes -join ', ')"
        exit 1
    }
    Write-Info "Building: $Type"
}

# Validate environment
function Test-Environment {
    param([string]$Env)
    $validEnvs = @("development", "production")
    if ($Env -notin $validEnvs) {
        Write-Error "Invalid environment: $Env"
        Write-Error "Valid environments: $($validEnvs -join ', ')"
        exit 1
    }
    Write-Info "Environment: $Env"
}

# Check prerequisites
function Test-Prerequisites {
    Write-Info "Checking prerequisites..."
    
    # Check if Docker is installed
    try {
        docker --version | Out-Null
        Write-Success "Docker is installed"
    }
    catch {
        Write-Error "Docker is not installed. Please install Docker first."
        exit 1
    }
    
    # Check if Docker is running
    try {
        docker info | Out-Null
        Write-Success "Docker is running"
    }
    catch {
        Write-Error "Docker is not running. Please start Docker first."
        exit 1
    }
    
    Write-Success "Prerequisites check completed"
}

# Clean up old images
function Remove-OldImages {
    Write-Info "Cleaning up old images..."
    
    # Remove dangling images
    docker image prune -f | Out-Null
    
    # Remove old versions of our images
    $images = docker images --format "table {{.Repository}}:{{.Tag}}" | Where-Object { $_ -like "real-estate-*" }
    if ($images) {
        $images | ForEach-Object { docker rmi $_ -f | Out-Null }
    }
    
    Write-Success "Cleanup completed"
}

# Build backend image
function Build-Backend {
    Write-Info "Building backend image..."
    
    $dockerfile = "Dockerfile"
    $tagSuffix = ""
    
    if ($Environment -eq "development") {
        $dockerfile = "Dockerfile.dev"
        $tagSuffix = "-dev"
    }
    
    Push-Location backend
    
    # Build the image
    $timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
    docker build `
        -f $dockerfile `
        -t "real-estate-backend$tagSuffix`:latest" `
        -t "real-estate-backend$tagSuffix`:$timestamp" `
        .
    
    Pop-Location
    
    Write-Success "Backend image built successfully"
}

# Build frontend image
function Build-Frontend {
    Write-Info "Building frontend image..."
    
    $dockerfile = "Dockerfile"
    $tagSuffix = ""
    
    if ($Environment -eq "development") {
        $dockerfile = "Dockerfile.dev"
        $tagSuffix = "-dev"
    }
    
    Push-Location frontend
    
    # Build the image
    $timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
    docker build `
        -f $dockerfile `
        -t "real-estate-frontend$tagSuffix`:latest" `
        -t "real-estate-frontend$tagSuffix`:$timestamp" `
        .
    
    Pop-Location
    
    Write-Success "Frontend image built successfully"
}

# Build service images
function Build-Services {
    Write-Info "Building service images..."
    
    # Build nginx image if needed
    if (Test-Path "docker/Dockerfile.nginx") {
        Write-Info "Building nginx image..."
        docker build -f docker/Dockerfile.nginx -t "real-estate-nginx:latest" docker/
        Write-Success "Nginx image built successfully"
    }
    
    Write-Success "Service images built successfully"
}

# Push images to registry
function Push-Images {
    if ($PushImages) {
        Write-Info "Pushing images to registry..."
        Write-Warning "Image pushing not implemented yet"
        Write-Warning "Images are built locally and ready for use"
    }
}

# Show build summary
function Show-Summary {
    Write-Success "Build Summary"
    Write-Host "==============" -ForegroundColor $GREEN
    Write-Host "Build Type: $BuildType"
    Write-Host "Environment: $Environment"
    Write-Host "Timestamp: $(Get-Date)"
    Write-Host ""
    Write-Host "Built Images:"
    
    # List built images
    docker images | Select-String "real-estate-" | Select-Object -First 10
    
    Write-Host ""
    Write-Host "Next Steps:"
    Write-Host "  Development: docker-compose -f docker-compose.dev.yml up -d"
    Write-Host "  Production:  docker-compose up -d"
    Write-Host "  View logs:   docker-compose logs -f"
    Write-Host "  Stop:        docker-compose down"
}

# Main build function
function Main {
    if ($Help) {
        Show-Help
        return
    }
    
    Write-Info "Starting Docker Build Process"
    Write-Info "Build Type: $BuildType"
    Write-Info "Environment: $Environment"
    Write-Info "Push Images: $PushImages"
    Write-Host ""
    
    # Validate inputs
    Test-BuildType $BuildType
    Test-Environment $Environment
    
    # Check prerequisites
    Test-Prerequisites
    
    # Clean up old images
    Remove-OldImages
    
    # Build based on type
    switch ($BuildType) {
        "all" {
            Build-Backend
            Build-Frontend
            Build-Services
        }
        "backend" {
            Build-Backend
        }
        "frontend" {
            Build-Frontend
        }
        "services" {
            Build-Services
        }
    }
    
    # Push images if requested
    Push-Images
    
    # Show summary
    Show-Summary
    
    Write-Success "Docker build completed successfully! 🎉"
}

# Run main function
Main
