# Real Estate AI - Comprehensive Startup Script
# This script handles: cloudflared, env updates, CORS config, backend, frontend, and Facebook redirect URL

Write-Host "Real Estate AI - Starting Services" -ForegroundColor Green
Write-Host "====================================" -ForegroundColor Green

# Step 1: Stop any existing services
Write-Host "Step 1: Cleaning up existing services..." -ForegroundColor Yellow
Get-Process -Name "cloudflared" -ErrorAction SilentlyContinue | Stop-Process -Force
Get-Process -Name "uvicorn" -ErrorAction SilentlyContinue | Stop-Process -Force
Get-Process -Name "node" -ErrorAction SilentlyContinue | Stop-Process -Force
Start-Sleep -Seconds 2

# Function to start cloudflared and get the URL
function Start-CloudflaredTunnel {
    param (
        [int]$port,
        [string]$name
    )

    $logFile = "$name-cloudflared.log"
    if (Test-Path $logFile) {
        Remove-Item $logFile
    }

    Write-Host "Starting cloudflared tunnel for $name on port $port..." -ForegroundColor Yellow
    Start-Process -FilePath "C:\Program Files (x86)\cloudflared\cloudflared.exe" -ArgumentList "tunnel", "--url", "http://localhost:$port" -RedirectStandardError $logFile -WindowStyle Minimized

    $maxRetries = 15
    $retryDelay = 2
    $retries = 0
    $tunnelUrl = $null

    while ($retries -lt $maxRetries) {
        Start-Sleep -Seconds $retryDelay
        if (Test-Path $logFile) {
            $logContent = Get-Content $logFile -Raw
            $match = $logContent | Select-String -Pattern "https://[a-zA-Z0-9-]+.trycloudflare.com"
            if ($match) {
                $tunnelUrl = $match.Matches[0].Value
                Write-Host "$name cloudflared tunnel active: $tunnelUrl" -ForegroundColor Green
                return $tunnelUrl
            }
        }
        $retries++
    }

    Write-Host "Failed to get cloudflared URL for $name after multiple retries. Please check the log file: $logFile" -ForegroundColor Red
    exit 1
}

# Step 2: Start cloudflared tunnels
$backendCloudflaredUrl = Start-CloudflaredTunnel -port 8000 -name "Backend"
$frontendCloudflaredUrl = Start-CloudflaredTunnel -port 3000 -name "Frontend"

# Step 3: Update .env file with current backend cloudflared URL
Write-Host "Step 3: Updating backend environment variables..." -ForegroundColor Yellow
$envPath = ".env"
if (Test-Path $envPath) {
    $envContent = Get-Content $envPath -Raw
    $envContent = $envContent -replace 'BASE_URL=https://.*', "BASE_URL=$backendCloudflaredUrl"
    Set-Content -Path $envPath -Value $envContent
    Write-Host "Backend environment variables updated with: $backendCloudflaredUrl" -ForegroundColor Green
} else {
    Write-Host "Warning: .env file not found" -ForegroundColor Yellow
}

# Step 4: Update CORS configuration in main.py
Write-Host "Step 4: Updating CORS configuration..." -ForegroundColor Yellow
$mainPyPath = "app\main.py"
if (Test-Path $mainPyPath) {
    $mainPyContent = Get-Content $mainPyPath -Raw
    
    if ($mainPyContent -match 'allow_origins=\[') {
        $corsPattern = '(?s)allow_origins=\[.*?\]'
        $newCorsConfig = @"
allow_origins=[
        "http://localhost:3000",  # Next.js frontend
        "$frontendCloudflaredUrl", # Frontend cloudflared tunnel
        "$backendCloudflaredUrl",  # Backend cloudflared tunnel
        "https://*.trycloudflare.com"
    ]
"@
        $updatedContent = $mainPyContent -replace $corsPattern, $newCorsConfig
        Set-Content -Path $mainPyPath -Value $updatedContent
        Write-Host "CORS configuration updated" -ForegroundColor Green
    } else {
        Write-Host "CORS configuration already uses regex patterns" -ForegroundColor Green
    }
} else {
    Write-Host "Warning: main.py file not found" -ForegroundColor Yellow
}

# Step 5: Update Next.js environment variables
Write-Host "Step 5: Updating Next.js environment..." -ForegroundColor Yellow
$nextjsEnvPath = "nextjs-app\.env.local"
if (Test-Path $nextjsEnvPath) {
    $nextjsEnvContent = Get-Content $nextjsEnvPath -Raw
    $nextjsEnvContent = $nextjsEnvContent -replace 'NEXT_PUBLIC_API_BASE_URL=https://.*', "NEXT_PUBLIC_API_BASE_URL=$backendCloudflaredUrl"
    $nextjsEnvContent = $nextjsEnvContent -replace 'NEXT_PUBLIC_BASE_URL=https://.*', "NEXT_PUBLIC_BASE_URL=$frontendCloudflaredUrl"
    Set-Content -Path $nextjsEnvPath -Value $nextjsEnvContent
} else {
    $nextjsEnvContent = @"
NEXT_PUBLIC_API_BASE_URL=$backendCloudflaredUrl
NEXT_PUBLIC_BASE_URL=$frontendCloudflaredUrl
"@
    Set-Content -Path $nextjsEnvPath -Value $nextjsEnvContent
}
Write-Host "Next.js environment updated" -ForegroundColor Green

# Step 6: Start Backend
Write-Host "Step 6: Starting FastAPI backend..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd c:\Users\code\realestate_ai; python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"
Start-Sleep -Seconds 15

# Check if backend is running
try {
    $response = Invoke-WebRequest -Uri "http://localhost:8000/docs" -Method Get -TimeoutSec 10
    Write-Host "Backend started successfully on http://localhost:8000" -ForegroundColor Green
} catch {
    Write-Host "Backend starting... (may take a moment)" -ForegroundColor Yellow
}

# Step 7: Start Frontend
Write-Host "Step 7: Starting Next.js frontend..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd c:\Users\code\realestate_ai\nextjs-app; npm run dev"
Start-Sleep -Seconds 20

# Check if frontend is running
try {
    $response = Invoke-WebRequest -Uri "http://localhost:3000" -Method Get -TimeoutSec 10
    Write-Host "Frontend started successfully on http://localhost:3000" -ForegroundColor Green
} catch {
    Write-Host "Frontend starting... (may take a moment)" -ForegroundColor Yellow
}

# Step 8: Display Facebook Configuration
Write-Host "" 
Write-Host "Facebook App Configuration" -ForegroundColor Yellow
Write-Host "============================" -ForegroundColor Cyan
Write-Host "Update your Facebook App settings with:" -ForegroundColor White
Write-Host "" 
Write-Host "Valid OAuth Redirect URIs:" -ForegroundColor Cyan
Write-Host "  $backendCloudflaredUrl/api/v1/facebook/callback" -ForegroundColor White
Write-Host ""
Write-Host "Site URL:" -ForegroundColor Cyan  
Write-Host "  $frontendCloudflaredUrl" -ForegroundColor White
Write-Host ""
Write-Host "App Domains:" -ForegroundColor Cyan
Write-Host "  localhost" -ForegroundColor White
$backendDomain = $backendCloudflaredUrl -replace 'https://', ''
$frontendDomain = $frontendCloudflaredUrl -replace 'https://', ''
Write-Host "  $backendDomain" -ForegroundColor White
Write-Host "  $frontendDomain" -ForegroundColor White

# Final Status
Write-Host "" 
Write-Host "All Services Started!" -ForegroundColor Green
Write-Host "====================" -ForegroundColor Green
Write-Host "Frontend Local: http://localhost:3000" -ForegroundColor White
Write-Host "Frontend Public: $frontendCloudflaredUrl" -ForegroundColor White
Write-Host "Backend Local: http://localhost:8000" -ForegroundColor White
Write-Host "Backend Public: $backendCloudflaredUrl" -ForegroundColor White
Write-Host "API Docs: http://localhost:8000/docs" -ForegroundColor White
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
            $backendResponse = Invoke-WebRequest -Uri "http://localhost:8000/docs" -Method Get -TimeoutSec 3 -ErrorAction SilentlyContinue
            $frontendResponse = Invoke-WebRequest -Uri "http://localhost:3000" -Method Get -TimeoutSec 3 -ErrorAction SilentlyContinue
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
    Get-Process -Name "cloudflared" -ErrorAction SilentlyContinue | Stop-Process -Force
    Get-Process -Name "uvicorn" -ErrorAction SilentlyContinue | Stop-Process -Force
    Get-Process -Name "node" -ErrorAction SilentlyContinue | Stop-Process -Force
    Write-Host "All services stopped." -ForegroundColor Green
}
