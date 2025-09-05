# Real Estate AI - Comprehensive Startup Script
# This script handles: environment setup, backend, frontend, and configuration
# Supports both Docker and local development modes

param(
    [switch]$Docker,
    [switch]$Local,
    [string]$Mode = "local"
)

Write-Host "Real Estate AI - Starting Services" -ForegroundColor Green
Write-Host "====================================" -ForegroundColor Green

# Determine deployment mode
if ($Docker) {
    $deploymentMode = "docker"
} elseif ($Local) {
    $deploymentMode = "local"
} else {
    $deploymentMode = $Mode.ToLower()
}

Write-Host "Deployment Mode: $deploymentMode" -ForegroundColor Cyan

# Step 1: Stop any existing services
Write-Host "Step 1: Cleaning up existing services..." -ForegroundColor Yellow
Get-Process -Name "uvicorn" -ErrorAction SilentlyContinue | Stop-Process -Force
Get-Process -Name "node" -ErrorAction SilentlyContinue | Stop-Process -Force
if ($deploymentMode -eq "docker") {
    docker-compose down 2>$null
}
Start-Sleep -Seconds 2

# Set URLs based on deployment mode
if ($deploymentMode -eq "docker") {
    $backendUrl = "http://localhost"
    $frontendUrl = "http://localhost"
    $backendPort = 80
    $frontendPort = 80
} else {
    $backendUrl = "http://localhost:8000"
    $frontendUrl = "http://localhost:3000"
    $backendPort = 8000
    $frontendPort = 3000
}

# Step 2: Update .env file with backend URL
Write-Host "Step 2: Updating backend environment variables..." -ForegroundColor Yellow
$envPath = ".env"
if (Test-Path $envPath) {
    $envContent = Get-Content $envPath -Raw
    $envContent = $envContent -replace 'BASE_URL=.*', "BASE_URL=$backendUrl"
    Set-Content -Path $envPath -Value $envContent
    Write-Host "Backend environment variables updated with: $backendUrl" -ForegroundColor Green
} else {
    Write-Host "Warning: .env file not found" -ForegroundColor Yellow
}

# Step 3: Update CORS configuration in main.py
Write-Host "Step 3: Updating CORS configuration..." -ForegroundColor Yellow
$mainPyPath = "app\main.py"
if (Test-Path $mainPyPath) {
    $mainPyContent = Get-Content $mainPyPath -Raw
    
    if ($mainPyContent -match 'allow_origins=\[') {
        $corsPattern = '(?s)allow_origins=\[.*?\]'
        if ($deploymentMode -eq "docker") {
            $newCorsConfig = @"
allow_origins=[
        "http://localhost",  # Docker frontend
        "http://localhost:3000",  # Local development fallback
        "http://127.0.0.1",
        "http://127.0.0.1:3000"
    ]
"@
        } else {
            $newCorsConfig = @"
allow_origins=[
        "http://localhost:3000",  # Next.js frontend
        "http://127.0.0.1:3000",  # Alternative localhost
        "http://localhost:8000",  # Backend self-reference
        "http://127.0.0.1:8000"
    ]
"@
        }
        $updatedContent = $mainPyContent -replace $corsPattern, $newCorsConfig
        Set-Content -Path $mainPyPath -Value $updatedContent
        Write-Host "CORS configuration updated for $deploymentMode mode" -ForegroundColor Green
    } else {
        Write-Host "CORS configuration already uses regex patterns" -ForegroundColor Green
    }
} else {
    Write-Host "Warning: main.py file not found" -ForegroundColor Yellow
}

# Step 4: Update Next.js environment variables
Write-Host "Step 4: Updating Next.js environment..." -ForegroundColor Yellow
$nextjsEnvPath = "nextjs-app\.env.local"
if (Test-Path $nextjsEnvPath) {
    $nextjsEnvContent = Get-Content $nextjsEnvPath -Raw
    $nextjsEnvContent = $nextjsEnvContent -replace 'NEXT_PUBLIC_API_BASE_URL=.*', "NEXT_PUBLIC_API_BASE_URL=$backendUrl"
    $nextjsEnvContent = $nextjsEnvContent -replace 'NEXT_PUBLIC_BASE_URL=.*', "NEXT_PUBLIC_BASE_URL=$frontendUrl"
    Set-Content -Path $nextjsEnvPath -Value $nextjsEnvContent
} else {
    $nextjsEnvContent = @"
NEXT_PUBLIC_API_BASE_URL=$backendUrl
NEXT_PUBLIC_BASE_URL=$frontendUrl
"@
    Set-Content -Path $nextjsEnvPath -Value $nextjsEnvContent
}
Write-Host "Next.js environment updated for $deploymentMode mode" -ForegroundColor Green

# Step 5: Start Services
if ($deploymentMode -eq "docker") {
    Write-Host "Step 5: Starting services with Docker..." -ForegroundColor Yellow
    docker-compose up -d
    Start-Sleep -Seconds 30
    
    # Check if services are running
    try {
        $response = Invoke-WebRequest -Uri "http://localhost/docs" -Method Get -TimeoutSec 10
        Write-Host "Backend started successfully via Docker" -ForegroundColor Green
    } catch {
        Write-Host "Backend starting via Docker... (may take a moment)" -ForegroundColor Yellow
    }
    
    try {
        $response = Invoke-WebRequest -Uri "http://localhost" -Method Get -TimeoutSec 10
        Write-Host "Frontend started successfully via Docker" -ForegroundColor Green
    } catch {
        Write-Host "Frontend starting via Docker... (may take a moment)" -ForegroundColor Yellow
    }
} else {
    # Step 5a: Start Backend (Local)
    Write-Host "Step 5a: Starting FastAPI backend locally..." -ForegroundColor Yellow
    Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd c:\Users\code\realestate_ai; python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"
    Start-Sleep -Seconds 15
    
    # Check if backend is running
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:8000/docs" -Method Get -TimeoutSec 10
        Write-Host "Backend started successfully on http://localhost:8000" -ForegroundColor Green
    } catch {
        Write-Host "Backend starting... (may take a moment)" -ForegroundColor Yellow
    }
    
    # Step 5b: Start Frontend (Local)
    Write-Host "Step 5b: Starting Next.js frontend locally..." -ForegroundColor Yellow
    Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd c:\Users\code\realestate_ai\nextjs-app; npm run dev"
    Start-Sleep -Seconds 20
    
    # Check if frontend is running
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:3000" -Method Get -TimeoutSec 10
        Write-Host "Frontend started successfully on http://localhost:3000" -ForegroundColor Green
    } catch {
        Write-Host "Frontend starting... (may take a moment)" -ForegroundColor Yellow
    }
}

# Step 6: Display Facebook Configuration
Write-Host "" 
Write-Host "Facebook App Configuration" -ForegroundColor Yellow
Write-Host "============================" -ForegroundColor Cyan
Write-Host "Update your Facebook App settings with:" -ForegroundColor White
Write-Host "" 
Write-Host "Valid OAuth Redirect URIs:" -ForegroundColor Cyan
if ($deploymentMode -eq "docker") {
    Write-Host "  http://localhost/api/v1/facebook/callback" -ForegroundColor White
} else {
    Write-Host "  http://localhost:8000/api/v1/facebook/callback" -ForegroundColor White
}
Write-Host ""
Write-Host "Site URL:" -ForegroundColor Cyan  
Write-Host "  $frontendUrl" -ForegroundColor White
Write-Host ""
Write-Host "App Domains:" -ForegroundColor Cyan
Write-Host "  localhost" -ForegroundColor White

# Final Status
Write-Host "" 
Write-Host "All Services Started!" -ForegroundColor Green
Write-Host "====================" -ForegroundColor Green
if ($deploymentMode -eq "docker") {
    Write-Host "Deployment Mode: Docker" -ForegroundColor Cyan
    Write-Host "Frontend: http://localhost" -ForegroundColor White
    Write-Host "Backend: http://localhost" -ForegroundColor White
    Write-Host "API Docs: http://localhost/docs" -ForegroundColor White
} else {
    Write-Host "Deployment Mode: Local Development" -ForegroundColor Cyan
    Write-Host "Frontend: http://localhost:3000" -ForegroundColor White
    Write-Host "Backend: http://localhost:8000" -ForegroundColor White
    Write-Host "API Docs: http://localhost:8000/docs" -ForegroundColor White
}
Write-Host "" 
Write-Host "Environment files updated:" -ForegroundColor Cyan
Write-Host "  .env (BASE_URL updated)" -ForegroundColor White
Write-Host "  nextjs-app/.env.local (API and Base URLs updated)" -ForegroundColor White
Write-Host "  app/main.py (CORS updated if needed)" -ForegroundColor White
Write-Host "" 
Write-Host "Remember to update Facebook App settings with the URLs above!" -ForegroundColor Yellow

Write-Host "Press Ctrl+C to stop all services..." -ForegroundColor Gray

# Keep script running and monitor services
try {
    while ($true) {
        Start-Sleep -Seconds 30
        # Check if services are still running
        try {
            if ($deploymentMode -eq "docker") {
                $backendResponse = Invoke-WebRequest -Uri "http://localhost/docs" -Method Get -TimeoutSec 3 -ErrorAction SilentlyContinue
                $frontendResponse = Invoke-WebRequest -Uri "http://localhost" -Method Get -TimeoutSec 3 -ErrorAction SilentlyContinue
            } else {
                $backendResponse = Invoke-WebRequest -Uri "http://localhost:8000/docs" -Method Get -TimeoutSec 3 -ErrorAction SilentlyContinue
                $frontendResponse = Invoke-WebRequest -Uri "http://localhost:3000" -Method Get -TimeoutSec 3 -ErrorAction SilentlyContinue
            }
            if ($backendResponse -and $frontendResponse) {
                Write-Host "." -NoNewline -ForegroundColor Green
            } else {
                Write-Host "!" -NoNewline -ForegroundColor Yellow
            }
        } catch {
            Write-Host "!" -NoNewline -ForegroundColor Yellow
        }
    }
} finally {
    Write-Host "" 
    Write-Host "Stopping services..." -ForegroundColor Red
    if ($deploymentMode -eq "docker") {
        docker-compose down
    } else {
        Get-Process -Name "uvicorn" -ErrorAction SilentlyContinue | Stop-Process -Force
        Get-Process -Name "node" -ErrorAction SilentlyContinue | Stop-Process -Force
    }
    Write-Host "All services stopped." -ForegroundColor Green
}
