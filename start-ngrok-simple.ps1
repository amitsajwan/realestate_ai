# =============================================================================
# SIMPLE NGROK SCRIPT FOR LOCAL SERVICES
# =============================================================================
# This script works with your existing local frontend (3000) and backend (8000)

param(
    [Parameter(Position=0)]
    [ValidateSet("start", "status", "stop")]
    [string]$Action = "start"
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

function Test-Prerequisites {
    Write-ColorOutput "Checking prerequisites..." $Blue
    
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
    
    # Check if local services are running
    try {
        $frontendResponse = Invoke-WebRequest -Uri "http://localhost:3000" -TimeoutSec 5 -ErrorAction Stop
        Write-ColorOutput "Frontend (port 3000): Running" $Green
    } catch {
        Write-ColorOutput "Frontend (port 3000): Not running" $Red
        Write-ColorOutput "Please start your frontend first" $Yellow
        return $false
    }
    
    try {
        $backendResponse = Invoke-WebRequest -Uri "http://localhost:8000/health" -TimeoutSec 5 -ErrorAction Stop
        Write-ColorOutput "Backend (port 8000): Running" $Green
    } catch {
        Write-ColorOutput "Backend (port 8000): Not running" $Red
        Write-ColorOutput "Please start your backend first" $Yellow
        return $false
    }
    
    return $true
}

function Start-NgrokTunnels {
    Write-ColorOutput "Starting ngrok tunnels..." $Blue
    
    # Kill any existing ngrok processes
    Get-Process -Name "ngrok" -ErrorAction SilentlyContinue | Stop-Process -Force
    Start-Sleep -Seconds 2
    
    # Start frontend tunnel
    Write-ColorOutput "Starting frontend tunnel (port 3000)..." $Blue
    Start-Process -FilePath "ngrok" -ArgumentList "http", "3000" -WindowStyle Hidden
    
    # Start backend tunnel
    Write-ColorOutput "Starting backend tunnel (port 8000)..." $Blue
    Start-Process -FilePath "ngrok" -ArgumentList "http", "8000" -WindowStyle Hidden
    
    # Wait for tunnels to start
    Start-Sleep -Seconds 5
    
    # Get the public URLs
    try {
        $response = Invoke-RestMethod -Uri "http://localhost:4040/api/tunnels" -ErrorAction Stop
        $frontendUrl = $null
        $backendUrl = $null
        
        foreach ($tunnel in $response.tunnels) {
            if ($tunnel.config.addr -eq "localhost:3000") {
                $frontendUrl = $tunnel.public_url
            } elseif ($tunnel.config.addr -eq "localhost:8000") {
                $backendUrl = $tunnel.public_url
            }
        }
        
        if ($frontendUrl) {
            Write-ColorOutput "Frontend tunnel: $frontendUrl" $Green
        }
        if ($backendUrl) {
            Write-ColorOutput "Backend tunnel: $backendUrl" $Green
        }
        
        return @{
            Frontend = $frontendUrl
            Backend = $backendUrl
        }
    } catch {
        Write-ColorOutput "Could not get tunnel URLs automatically" $Yellow
        Write-ColorOutput "Check ngrok dashboard: http://localhost:4040" $Blue
        return $null
    }
}

function Show-Status {
    Write-ColorOutput "Service Status:" $Blue
    
    # Check local services
    try {
        $frontendResponse = Invoke-WebRequest -Uri "http://localhost:3000" -TimeoutSec 5 -ErrorAction Stop
        Write-ColorOutput "Frontend (localhost:3000): Running" $Green
    } catch {
        Write-ColorOutput "Frontend (localhost:3000): Not running" $Red
    }
    
    try {
        $backendResponse = Invoke-WebRequest -Uri "http://localhost:8000/health" -TimeoutSec 5 -ErrorAction Stop
        Write-ColorOutput "Backend (localhost:8000): Running" $Green
    } catch {
        Write-ColorOutput "Backend (localhost:8000): Not running" $Red
    }
    
    # Check ngrok
    try {
        $response = Invoke-RestMethod -Uri "http://localhost:4040/api/tunnels" -ErrorAction Stop
        if ($response.tunnels.Count -gt 0) {
            Write-ColorOutput "`nActive ngrok tunnels:" $Blue
            foreach ($tunnel in $response.tunnels) {
                Write-ColorOutput "  $($tunnel.config.addr) -> $($tunnel.public_url)" $Green
            }
        } else {
            Write-ColorOutput "No ngrok tunnels active" $Red
        }
    } catch {
        Write-ColorOutput "ngrok not accessible" $Red
    }
}

function Stop-Services {
    Write-ColorOutput "Stopping ngrok tunnels..." $Blue
    
    # Stop ngrok
    Get-Process -Name "ngrok" -ErrorAction SilentlyContinue | Stop-Process -Force
    
    Write-ColorOutput "ngrok tunnels stopped" $Green
    Write-ColorOutput "Your local services (3000, 8000) are still running" $Yellow
}

function Show-AccessInfo {
    param($Urls)
    
    Write-ColorOutput "`nDeployment Complete!" $Green
    Write-ColorOutput "=================================" $Blue
    
    if ($Urls) {
        if ($Urls.Frontend) {
            Write-ColorOutput "Frontend (Public): $($Urls.Frontend)" $Green
        }
        if ($Urls.Backend) {
            Write-ColorOutput "Backend (Public): $($Urls.Backend)" $Green
        }
    } else {
        Write-ColorOutput "Public URLs: Check ngrok dashboard" $Yellow
    }
    
    Write-ColorOutput "Local Frontend: http://localhost:3000" $Blue
    Write-ColorOutput "Local Backend: http://localhost:8000" $Blue
    Write-ColorOutput "ngrok Dashboard: http://localhost:4040" $Blue
    Write-ColorOutput "API Documentation: http://localhost:8000/docs" $Blue
    
    Write-ColorOutput "`nImportant Notes:" $Yellow
    Write-ColorOutput "1. You have TWO separate ngrok URLs (frontend and backend)" $Reset
    Write-ColorOutput "2. Update your frontend to use the backend ngrok URL for API calls" $Reset
    Write-ColorOutput "3. Or use a single tunnel with nginx proxy (see docker version)" $Reset
}

# Main execution
Write-ColorOutput "Real Estate AI - Simple ngrok Setup" $Blue
Write-ColorOutput "====================================" $Blue

switch ($Action) {
    "start" {
        if (-not (Test-Prerequisites)) {
            exit 1
        }
        
        Write-ColorOutput "`nStarting ngrok tunnels..." $Blue
        $urls = Start-NgrokTunnels
        Show-AccessInfo -Urls $urls
    }
    
    "status" {
        Show-Status
    }
    
    "stop" {
        Stop-Services
    }
    
    default {
        Write-ColorOutput "Invalid action: $Action" $Red
        Write-ColorOutput "Valid actions: start, status, stop" $Yellow
        exit 1
    }
}
