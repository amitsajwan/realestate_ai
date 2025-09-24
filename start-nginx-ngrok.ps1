# =============================================================================
# NGINX + NGROK SINGLE URL SETUP
# =============================================================================
# This script sets up nginx as a local proxy and creates a single ngrok tunnel

param(
    [Parameter(Position=0)]
    [ValidateSet("start", "status", "stop", "restart")]
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
    
    # Check nginx
    try {
        $nginxVersion = nginx -v 2>&1
        if ($nginxVersion -match "nginx") {
            Write-ColorOutput "nginx: $nginxVersion" $Green
        } else {
            throw "nginx not found"
        }
    } catch {
        Write-ColorOutput "nginx not found" $Red
        Write-ColorOutput "Please install nginx: winget install freenginx.nginx" $Yellow
        return $false
    }
    
    # Check if local services are running
    try {
        $frontendResponse = Invoke-WebRequest -Uri "http://localhost:3000" -TimeoutSec 5 -ErrorAction Stop
        Write-ColorOutput "Frontend (port 3000): Running" $Green
    } catch {
        Write-ColorOutput "Frontend (port 3000): Not running" $Red
        Write-ColorOutput "Please start your frontend first: cd frontend && npm run dev" $Yellow
        return $false
    }
    
    try {
        $backendResponse = Invoke-WebRequest -Uri "http://localhost:8000/health" -TimeoutSec 5 -ErrorAction Stop
        Write-ColorOutput "Backend (port 8000): Running" $Green
    } catch {
        Write-ColorOutput "Backend (port 8000): Not running" $Red
        Write-ColorOutput "Please start your backend first: cd backend && python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload" $Yellow
        return $false
    }
    
    return $true
}

function Start-Nginx {
    Write-ColorOutput "Starting nginx..." $Blue
    
    # Stop any existing nginx processes
    Get-Process -Name "nginx" -ErrorAction SilentlyContinue | Stop-Process -Force
    Start-Sleep -Seconds 2
    
    # Find nginx installation directory
    $nginxPath = Get-Command nginx -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Source
    if (-not $nginxPath) {
        Write-ColorOutput "nginx not found in PATH" $Red
        return $false
    }
    
    $nginxDir = Split-Path $nginxPath -Parent
    
    # Copy our config to nginx directory
    $configSource = Join-Path $PWD "nginx-simple.conf"
    $configDest = Join-Path $nginxDir "conf\nginx.conf"
    
    try {
        Copy-Item $configSource $configDest -Force
        Write-ColorOutput "nginx configuration updated" $Green
    } catch {
        Write-ColorOutput "Failed to copy nginx configuration" $Red
        return $false
    }
    
    # Start nginx
    try {
        Start-Process -FilePath $nginxPath -WindowStyle Hidden
        Start-Sleep -Seconds 3
        
        # Test if nginx is running
        $nginxResponse = Invoke-WebRequest -Uri "http://localhost:80" -TimeoutSec 5 -ErrorAction Stop
        Write-ColorOutput "nginx started successfully on port 80" $Green
        return $true
    } catch {
        Write-ColorOutput "Failed to start nginx" $Red
        return $false
    }
}

function Start-NgrokTunnel {
    Write-ColorOutput "Starting ngrok tunnel..." $Blue
    
    # Kill any existing ngrok processes
    Get-Process -Name "ngrok" -ErrorAction SilentlyContinue | Stop-Process -Force
    Start-Sleep -Seconds 2
    
    # Start ngrok tunnel pointing to nginx (port 80)
    Start-Process -FilePath "ngrok" -ArgumentList "http", "80" -WindowStyle Hidden
    
    # Wait for ngrok to start
    Start-Sleep -Seconds 5
    
    # Get the public URL
    try {
        $response = Invoke-RestMethod -Uri "http://localhost:4040/api/tunnels" -ErrorAction Stop
        if ($response.tunnels.Count -gt 0) {
            $publicUrl = $response.tunnels[0].public_url
            Write-ColorOutput "ngrok tunnel active: $publicUrl" $Green
            return $publicUrl
        } else {
            Write-ColorOutput "No ngrok tunnels found" $Red
            return $null
        }
    } catch {
        Write-ColorOutput "Could not get ngrok URL automatically" $Yellow
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
    
    # Check nginx
    try {
        $nginxResponse = Invoke-WebRequest -Uri "http://localhost:80" -TimeoutSec 5 -ErrorAction Stop
        Write-ColorOutput "nginx (localhost:80): Running" $Green
    } catch {
        Write-ColorOutput "nginx (localhost:80): Not running" $Red
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
    Write-ColorOutput "Stopping services..." $Blue
    
    # Stop nginx
    Get-Process -Name "nginx" -ErrorAction SilentlyContinue | Stop-Process -Force
    
    # Stop ngrok
    Get-Process -Name "ngrok" -ErrorAction SilentlyContinue | Stop-Process -Force
    
    Write-ColorOutput "nginx and ngrok stopped" $Green
    Write-ColorOutput "Your local services (3000, 8000) are still running" $Yellow
}

function Show-AccessInfo {
    param([string]$PublicUrl)
    
    Write-ColorOutput "`nDeployment Complete!" $Green
    Write-ColorOutput "=================================" $Blue
    
    if ($PublicUrl) {
        Write-ColorOutput "Public URL: $PublicUrl" $Green
        Write-ColorOutput "`nThis single URL serves both:" $Blue
        Write-ColorOutput "  Frontend: $PublicUrl" $Reset
        Write-ColorOutput "  Backend API: $PublicUrl/api/" $Reset
        Write-ColorOutput "  API Docs: $PublicUrl/docs" $Reset
        Write-ColorOutput "  Health Check: $PublicUrl/health" $Reset
    } else {
        Write-ColorOutput "Public URL: Check ngrok dashboard" $Yellow
    }
    
    Write-ColorOutput "`nLocal Access:" $Blue
    Write-ColorOutput "  Frontend: http://localhost:3000" $Reset
    Write-ColorOutput "  Backend: http://localhost:8000" $Reset
    Write-ColorOutput "  nginx Proxy: http://localhost:80" $Reset
    Write-ColorOutput "  ngrok Dashboard: http://localhost:4040" $Reset
    
    Write-ColorOutput "`nArchitecture:" $Blue
    Write-ColorOutput "  Internet -> ngrok -> nginx:80 -> { frontend:3000, backend:8000 }" $Reset
}

# Main execution
Write-ColorOutput "Real Estate AI - nginx + ngrok Single URL Setup" $Blue
Write-ColorOutput "=================================================" $Blue

switch ($Action) {
    "start" {
        if (-not (Test-Prerequisites)) {
            exit 1
        }
        
        Write-ColorOutput "`nStarting nginx proxy..." $Blue
        if (-not (Start-Nginx)) {
            exit 1
        }
        
        Write-ColorOutput "`nStarting ngrok tunnel..." $Blue
        $publicUrl = Start-NgrokTunnel
        
        Show-AccessInfo -PublicUrl $publicUrl
    }
    
    "status" {
        Show-Status
    }
    
    "stop" {
        Stop-Services
    }
    
    "restart" {
        Stop-Services
        Start-Sleep -Seconds 3
        if (Test-Prerequisites) {
            Start-Nginx
            Start-NgrokTunnel
        }
    }
    
    default {
        Write-ColorOutput "Invalid action: $Action" $Red
        Write-ColorOutput "Valid actions: start, status, stop, restart" $Yellow
        exit 1
    }
}
