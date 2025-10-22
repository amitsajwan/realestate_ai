# =============================================================================
# NGROK + DOCKER EXTERNAL CONFIGURATION SCRIPT
# =============================================================================
# One-click deployment for ngrok with external configuration
# Application stays clean - no ngrok URLs hardcoded

param(
    [Parameter(Position=0)]
    [ValidateSet("oneclick", "setup", "start", "status", "logs", "stop", "clean", "help")]
    [string]$Action = "oneclick",
    
    [Parameter()]
    [switch]$Help = $false
)

# Colors for output
$Green = "`e[32m"
$Red = "`e[31m"
$Yellow = "`e[33m"
$Blue = "`e[34m"
$Reset = "`e[0m"

function Write-ColorOutput {
    param([string]$Message, [string]$Color = $Reset)
    Write-Host "$Color$Message$Reset"
}

function Show-Help {
    Write-ColorOutput "Real Estate AI - Docker + ngrok Deployment" $Blue
    Write-ColorOutput "===========================================" $Blue
    Write-ColorOutput ""
    Write-ColorOutput "Usage: .\start-ngrok-docker-external.ps1 [ACTION]" $Yellow
    Write-ColorOutput ""
    Write-ColorOutput "Actions:" $Cyan
    Write-ColorOutput "  oneclick - One-click deployment (default)" $Reset
    Write-ColorOutput "  setup    - Setup configuration files only" $Reset
    Write-ColorOutput "  start    - Start Docker services + ngrok" $Reset
    Write-ColorOutput "  status   - Check service status" $Reset
    Write-ColorOutput "  logs     - View service logs" $Reset
    Write-ColorOutput "  stop     - Stop all services" $Reset
    Write-ColorOutput "  clean    - Clean up everything" $Reset
    Write-ColorOutput "  help     - Show this help" $Reset
    Write-ColorOutput ""
    Write-ColorOutput "Prerequisites:" $Yellow
    Write-ColorOutput "• Docker Desktop installed and running" $Reset
    Write-ColorOutput "• ngrok installed and in PATH" $Reset
    Write-ColorOutput ""
    Write-ColorOutput "Examples:" $Yellow
    Write-ColorOutput "  .\start-ngrok-docker-external.ps1              # One-click deployment" $Reset
    Write-ColorOutput "  .\start-ngrok-docker-external.ps1 oneclick   # One-click deployment" $Reset
    Write-ColorOutput "  .\start-ngrok-docker-external.ps1 status      # Check status" $Reset
    Write-ColorOutput "  .\start-ngrok-docker-external.ps1 logs        # View logs" $Reset
    Write-ColorOutput "  .\start-ngrok-docker-external.ps1 stop        # Stop services" $Reset
    Write-ColorOutput ""
    Write-ColorOutput "After deployment:" $Yellow
    Write-ColorOutput "• Single public URL for entire application" $Reset
    Write-ColorOutput "• nginx handles routing and CORS" $Reset
    Write-ColorOutput "• Use ngrok dashboard (http://localhost:4040) for monitoring" $Reset
    Write-ColorOutput "• API docs available at /docs" $Reset
}

function Test-Prerequisites {
    Write-ColorOutput "Checking prerequisites..." $Blue
    
    # Check Docker
    try {
        $dockerVersion = docker --version 2>$null
        if ($dockerVersion) {
            Write-ColorOutput "Docker: $dockerVersion" $Green
        } else {
            throw "Docker not found"
        }
    } catch {
        Write-ColorOutput "Docker not found or not running" $Red
        Write-ColorOutput "Please install Docker Desktop and ensure it's running" $Yellow
        return $false
    }
    
    # Check ngrok
    try {
        $ngrokVersion = ngrok version 2>$null
        if ($ngrokVersion) {
            Write-ColorOutput "ngrok: $ngrokVersion" $Green
        } else {
            throw "ngrok not found"
        }
    } catch {
        Write-ColorOutput "ngrok not found" $Red
        Write-ColorOutput "Please install ngrok: https://ngrok.com/download" $Yellow
        return $false
    }
    
    # Check if ngrok is working (free version doesn't require auth)
    try {
        $ngrokHelp = ngrok help 2>$null
        if ($LASTEXITCODE -eq 0) {
            Write-ColorOutput "ngrok is ready (free version)" $Green
        } else {
            Write-ColorOutput "ngrok not working properly" $Red
            return $false
        }
    } catch {
        Write-ColorOutput "ngrok check failed" $Red
        return $false
    }
    
    return $true
}

function Start-NgrokTunnel {
    Write-ColorOutput "Starting ngrok tunnel..." $Blue
    
    # Kill any existing ngrok processes
    Get-Process -Name "ngrok" -ErrorAction SilentlyContinue | Stop-Process -Force
    
    # Start ngrok tunnel (free version)
    Start-Process -FilePath "ngrok" -ArgumentList "http", "80" -WindowStyle Hidden
    
    # Wait for ngrok to start
    Start-Sleep -Seconds 3
    
    # Get the public URL
    try {
        $response = Invoke-RestMethod -Uri "http://localhost:4040/api/tunnels" -ErrorAction Stop
        $publicUrl = $response.tunnels[0].public_url
        Write-ColorOutput "ngrok tunnel active: $publicUrl" $Green
        return $publicUrl
    } catch {
        Write-ColorOutput "Could not get ngrok URL automatically" $Yellow
        Write-ColorOutput "Check ngrok dashboard: http://localhost:4040" $Blue
        return $null
    }
}

function Start-DockerServices {
    Write-ColorOutput "Starting Docker services..." $Blue
    
    # Stop any existing containers
    docker-compose -f docker-compose.yml -f docker-compose.ngrok.yml down 2>$null
    
    # Start services
    docker-compose -f docker-compose.yml -f docker-compose.ngrok.yml up -d
    
    if ($LASTEXITCODE -eq 0) {
        Write-ColorOutput "Docker services started" $Green
        
        # Ensure nginx service is running (it might not start automatically)
        Write-ColorOutput "Ensuring nginx service is running..." $Blue
        docker-compose -f docker-compose.yml -f docker-compose.ngrok.yml up -d nginx
        
        return $true
    } else {
        Write-ColorOutput "Failed to start Docker services" $Red
        return $false
    }
}

function Show-Status {
    Write-ColorOutput "Service Status:" $Blue
    
    # Check Docker services
    $services = docker-compose -f docker-compose.yml -f docker-compose.ngrok.yml ps
    Write-Host $services
    
    # Check ngrok
    try {
        $response = Invoke-RestMethod -Uri "http://localhost:4040/api/tunnels" -ErrorAction Stop
        if ($response.tunnels.Count -gt 0) {
            Write-ColorOutput "ngrok tunnel active: $($response.tunnels[0].public_url)" $Green
        } else {
            Write-ColorOutput "No ngrok tunnels active" $Red
        }
    } catch {
        Write-ColorOutput "ngrok not accessible" $Red
    }
}

function Show-Logs {
    Write-ColorOutput "Recent logs:" $Blue
    docker-compose -f docker-compose.yml -f docker-compose.ngrok.yml logs --tail=50
}

function Stop-Services {
    Write-ColorOutput "Stopping services..." $Blue
    
    # Stop Docker services
    docker-compose -f docker-compose.yml -f docker-compose.ngrok.yml down
    
    # Stop ngrok
    Get-Process -Name "ngrok" -ErrorAction SilentlyContinue | Stop-Process -Force
    
    Write-ColorOutput "Services stopped" $Green
}

function Clean-Up {
    Write-ColorOutput "Cleaning up..." $Blue
    
    # Stop and remove containers
    docker-compose -f docker-compose.yml -f docker-compose.ngrok.yml down -v
    
    # Remove unused images
    docker image prune -f
    
    # Stop ngrok
    Get-Process -Name "ngrok" -ErrorAction SilentlyContinue | Stop-Process -Force
    
    Write-ColorOutput "Cleanup completed" $Green
}

function Show-AccessInfo {
    param([string]$PublicUrl)
    
    Write-ColorOutput "`nDeployment Complete!" $Green
    Write-ColorOutput "=================================" $Blue
    
    if ($PublicUrl) {
        Write-ColorOutput "Public Access: $PublicUrl" $Green
    } else {
        Write-ColorOutput "Public Access: Check ngrok dashboard" $Yellow
        Write-ColorOutput "   Dashboard: http://localhost:4040" $Blue
    }
    
    Write-ColorOutput "Local Access: http://localhost:80" $Blue
    Write-ColorOutput "ngrok Dashboard: http://localhost:4040" $Blue
    Write-ColorOutput "API Documentation: http://localhost:80/docs" $Blue
    Write-ColorOutput "Health Check: http://localhost:80/health" $Blue
    
    Write-ColorOutput "`nNext Steps:" $Yellow
    Write-ColorOutput "1. Test your application at the public URL" $Reset
    Write-ColorOutput "2. Check logs if needed: .\start-ngrok-docker-external.ps1 -Action logs" $Reset
    Write-ColorOutput "3. Monitor status: .\start-ngrok-docker-external.ps1 -Action status" $Reset
    Write-ColorOutput "4. Stop when done: .\start-ngrok-docker-external.ps1 -Action stop" $Reset
}

# Main execution
if ($Help) {
    Show-Help
    exit 0
}

Write-ColorOutput "Real Estate AI - ngrok + Docker Deployment" $Blue
Write-ColorOutput "=============================================" $Blue

switch ($Action) {
    "oneclick" {
        if (-not (Test-Prerequisites)) {
            exit 1
        }
        
        Write-ColorOutput "`nStarting one-click deployment..." $Blue
        
        # Start Docker services
        if (-not (Start-DockerServices)) {
            exit 1
        }
        
        # Start ngrok tunnel
        $publicUrl = Start-NgrokTunnel
        
        # Wait for services to be ready
        Write-ColorOutput "Waiting for services to be ready..." $Yellow
        Start-Sleep -Seconds 10
        
        Show-AccessInfo -PublicUrl $publicUrl
    }
    
    "setup" {
        Write-ColorOutput "Setup mode - configuration files are ready" $Blue
        Write-ColorOutput "Run 'start' action to deploy" $Yellow
    }
    
    "start" {
        if (-not (Test-Prerequisites)) {
            exit 1
        }
        
        if (-not (Start-DockerServices)) {
            exit 1
        }
        
        $publicUrl = Start-NgrokTunnel
        Show-AccessInfo -PublicUrl $publicUrl
    }
    
    "status" {
        Show-Status
    }
    
    "logs" {
        Show-Logs
    }
    
    "stop" {
        Stop-Services
    }
    
    "clean" {
        Clean-Up
    }
    
    "help" {
        Show-Help
    }
    
    default {
        Write-ColorOutput "Invalid action: $Action" $Red
        Write-ColorOutput "Valid actions: oneclick, setup, start, status, logs, stop, clean, help" $Yellow
        Write-ColorOutput "Use -Help for detailed information" $Yellow
        exit 1
    }
}