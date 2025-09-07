# =============================================================================
# SIMPLE DOCKER DEPLOYMENT SCRIPT
# =============================================================================
# This script deploys the application using Docker without ngrok complexity
# Perfect for production-like testing and deployment

param(
    [Parameter(Mandatory=$false)]
    [ValidateSet("start", "stop", "restart", "status", "logs", "build", "clean")]
    [string]$Action = "start",
    
    [Parameter(Mandatory=$false)]
    [switch]$Force = $false
)

# Configuration
$DOCKER_COMPOSE_FILE = "docker/docker-compose.yml"
$APP_URL = "http://localhost"

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

function Test-Command {
    param([string]$Command)
    try {
        $null = Get-Command $Command -ErrorAction Stop
        return $true
    } catch {
        return $false
    }
}

function Test-DockerRunning {
    try {
        $null = docker info 2>$null
        return $true
    } catch {
        return $false
    }
}

function Build-Images {
    Write-Step "BUILD" "Building Docker images..."
    
    try {
        Push-Location docker
        
        # Build all images
        Write-Step "BUILD" "Building backend image..."
        docker-compose build backend
        
        Write-Step "BUILD" "Building frontend image..."
        docker-compose build frontend
        
        Pop-Location
        Write-Success "All Docker images built successfully"
        return $true
        
    } catch {
        Write-Error "Failed to build Docker images: $($_.Exception.Message)"
        Pop-Location
        return $false
    }
}

function Start-Containers {
    Write-Step "DOCKER" "Starting all containers..."
    
    try {
        Push-Location docker
        
        # Start services
        docker-compose up -d
        
        # Wait for services to be healthy
        Write-Step "DOCKER" "Waiting for services to be healthy..."
        Start-Sleep -Seconds 30
        
        # Check if services are running
        $containers = docker-compose ps --services --filter "status=running"
        if ($containers.Count -ge 4) {  # mongodb, backend, frontend, nginx
            Write-Success "All containers started successfully"
            Pop-Location
            return $true
        } else {
            Write-Warning "Some containers may not be running properly"
            Pop-Location
            return $false
        }
        
    } catch {
        Write-Error "Failed to start containers: $($_.Exception.Message)"
        Pop-Location
        return $false
    }
}

function Stop-Containers {
    Write-Step "DOCKER" "Stopping all containers..."
    
    try {
        Push-Location docker
        docker-compose down
        Pop-Location
        Write-Success "All containers stopped"
        return $true
        
    } catch {
        Write-Error "Failed to stop containers: $($_.Exception.Message)"
        Pop-Location
        return $false
    }
}

function Show-Status {
    Write-Header "DOCKER CONTAINER STATUS"
    
    try {
        Push-Location docker
        
        # Show container status
        Write-ColorOutput "Container Status:" "Cyan"
        docker-compose ps
        
        # Show resource usage
        Write-Host ""
        Write-ColorOutput "Resource Usage:" "Cyan"
        docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}"
        
        Pop-Location
        
        Write-Host ""
        Write-ColorOutput "Application URLs:" "Cyan"
        Write-Host "  Application: $APP_URL"
        Write-Host "  API Documentation: $APP_URL/docs"
        Write-Host "  Health Check: $APP_URL/health"
        
    } catch {
        Write-Error "Failed to get container status: $($_.Exception.Message)"
        Pop-Location
    }
}

function Show-Logs {
    param([string]$Service = "")
    
    Write-Header "CONTAINER LOGS"
    
    try {
        Push-Location docker
        
        if ($Service) {
            Write-ColorOutput "Logs for $Service:" "Cyan"
            docker-compose logs -f $Service
        } else {
            Write-ColorOutput "Recent logs from all services:" "Cyan"
            docker-compose logs --tail=50
        }
        
        Pop-Location
        
    } catch {
        Write-Error "Failed to get logs: $($_.Exception.Message)"
        Pop-Location
    }
}

function Clean-Resources {
    Write-Step "CLEAN" "Cleaning up Docker resources..."
    
    try {
        Push-Location docker
        
        # Stop and remove containers
        docker-compose down -v
        
        # Remove images (if force flag is set)
        if ($Force) {
            Write-Step "CLEAN" "Removing Docker images..."
            docker-compose down --rmi all
        }
        
        # Clean up unused resources
        docker system prune -f
        
        Pop-Location
        Write-Success "Docker resources cleaned up"
        return $true
        
    } catch {
        Write-Error "Failed to clean Docker resources: $($_.Exception.Message)"
        Pop-Location
        return $false
    }
}

function Test-Health {
    Write-Step "HEALTH" "Testing application health..."
    
    $maxRetries = 10
    $retryCount = 0
    
    while ($retryCount -lt $maxRetries) {
        try {
            $response = Invoke-WebRequest -Uri "$APP_URL/health" -Method Get -TimeoutSec 5
            if ($response.StatusCode -eq 200) {
                Write-Success "Application is healthy and responding"
                return $true
            }
        } catch {
            # Continue retrying
        }
        
        $retryCount++
        Write-Step "HEALTH" "Waiting for application to be ready... ($retryCount/$maxRetries)"
        Start-Sleep -Seconds 5
    }
    
    Write-Warning "Application health check failed after $maxRetries attempts"
    return $false
}

# Main execution
Write-Header "PropertyAI Docker Deployment"

# Check prerequisites
if (!(Test-Command "docker")) {
    Write-Error "Docker is not installed or not in PATH"
    exit 1
}

if (!(Test-DockerRunning)) {
    Write-Error "Docker is not running. Please start Docker Desktop."
    exit 1
}

if (!(Test-Path $DOCKER_COMPOSE_FILE)) {
    Write-Error "Docker compose file not found: $DOCKER_COMPOSE_FILE"
    exit 1
}

switch ($Action) {
    "start" {
        Write-Step "START" "Starting Docker deployment..."
        
        # Build images if needed
        if ($Force) {
            $buildSuccess = Build-Images
            if (!$buildSuccess) {
                Write-Error "Failed to build images. Exiting."
                exit 1
            }
        }
        
        # Start containers
        $startSuccess = Start-Containers
        if (!$startSuccess) {
            Write-Error "Failed to start containers. Exiting."
            exit 1
        }
        
        # Test health
        $healthSuccess = Test-Health
        if ($healthSuccess) {
            Write-Header "DEPLOYMENT COMPLETE"
            Write-ColorOutput "🎉 Application deployed successfully!" "Green"
            Write-Host ""
            Write-ColorOutput "Access your application:" "Cyan"
            Write-Host "  Application: $APP_URL"
            Write-Host "  API Documentation: $APP_URL/docs"
            Write-Host "  Health Check: $APP_URL/health"
            Write-Host ""
            Write-ColorOutput "Useful commands:" "Cyan"
            Write-Host "  .\start-docker.ps1 -Action status    # Check status"
            Write-Host "  .\start-docker.ps1 -Action logs      # View logs"
            Write-Host "  .\start-docker.ps1 -Action stop      # Stop containers"
        } else {
            Write-Warning "Application started but health check failed"
            Write-Host "Check logs with: .\start-docker.ps1 -Action logs"
        }
    }
    
    "stop" {
        Stop-Containers
    }
    
    "restart" {
        Stop-Containers
        Start-Sleep -Seconds 2
        & $PSCommandPath -Action start
    }
    
    "build" {
        Build-Images
    }
    
    "status" {
        Show-Status
    }
    
    "logs" {
        Show-Logs
    }
    
    "clean" {
        Clean-Resources
    }
    
    default {
        Write-Header "USAGE"
        Write-Host "Usage: .\start-docker.ps1 -Action [action]"
        Write-Host ""
        Write-ColorOutput "Available Actions:" "Cyan"
        Write-Host "  start    - Start all containers (default)"
        Write-Host "  stop     - Stop all containers"
        Write-Host "  restart  - Restart all containers"
        Write-Host "  build    - Build Docker images"
        Write-Host "  status   - Show container status"
        Write-Host "  logs     - Show container logs"
        Write-Host "  clean    - Clean up Docker resources"
        Write-Host ""
        Write-ColorOutput "Options:" "Cyan"
        Write-Host "  -Force   - Force rebuild images"
        Write-Host ""
        Write-ColorOutput "Examples:" "Cyan"
        Write-Host "  .\start-docker.ps1                      # Start containers"
        Write-Host "  .\start-docker.ps1 -Action build        # Build images"
        Write-Host "  .\start-docker.ps1 -Action status       # Check status"
        Write-Host "  .\start-docker.ps1 -Action logs         # View logs"
        Write-Host "  .\start-docker.ps1 -Action clean -Force # Clean everything"
    }
}

Write-Host ""











