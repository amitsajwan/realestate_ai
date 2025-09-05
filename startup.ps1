# PropertyAI - Complete Deployment & Development Script
# Handles: Frontend Build, Backend Build, Docker, Ngrok, Facebook OAuth, Testing
# Author: AI Assistant
# Version: 2.0.0
# Date: January 2024

param(
    [Parameter(Mandatory=$false)]
    [ValidateSet("build-frontend", "build-backend", "build-images", "full-deploy", "step-deploy", "step-deploy-continue", "test-playwright", "test-backend", "ngrok-setup", "facebook-config", "cleanup", "status")]
    [string]$Mode = "status",
    
    [Parameter(Mandatory=$false)]
    [switch]$SkipFacebook = $false,
    
    [Parameter(Mandatory=$false)]
    [switch]$Force = $false,
    
    [Parameter(Mandatory=$false)]
    [string]$NgrokUrl = "",
    
    [Parameter(Mandatory=$false)]
    [switch]$Interactive = $true
)

# Configuration
$SCRIPT_VERSION = "2.0.0"
$PROJECT_NAME = "PropertyAI"
$BACKEND_PORT = 8000
$FRONTEND_PORT = 3000
$DOCKER_BACKEND_PORT = 80
$DOCKER_FRONTEND_PORT = 80

# Colors for output
$Colors = @{
    "Red" = [ConsoleColor]::Red
    "Green" = [ConsoleColor]::Green
    "Yellow" = [ConsoleColor]::Yellow
    "Cyan" = [ConsoleColor]::Cyan
    "Magenta" = [ConsoleColor]::Magenta
    "White" = [ConsoleColor]::White
    "Gray" = [ConsoleColor]::Gray
}

function Write-ColoredOutput {
    param([string]$Message, [string]$Color = "White")
    $OriginalColor = $Host.UI.RawUI.ForegroundColor
    $Host.UI.RawUI.ForegroundColor = $Colors[$Color]
    Write-Host $Message
    $Host.UI.RawUI.ForegroundColor = $OriginalColor
}

function Write-Header {
    param([string]$Title)
    Write-Host ""
    Write-ColoredOutput "==================================================================================" "Cyan"
    Write-ColoredOutput "  $Title" "Cyan"
    Write-ColoredOutput "==================================================================================" "Cyan"
    Write-Host ""
}

function Write-Step {
    param([string]$Step, [string]$Description = "")
    Write-ColoredOutput "[$Step]" "Yellow" -NoNewline
    Write-Host " $Description"
}

function Write-Success {
    param([string]$Message)
    Write-ColoredOutput "[OK] $Message" "Green"
}

function Write-Error {
    param([string]$Message)
    Write-ColoredOutput "[ERROR] $Message" "Red"
}

function Write-Warning {
    param([string]$Message)
    Write-ColoredOutput "[WARN] $Message" "Yellow"
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

function Get-NgrokUrl {
    try {
        Write-Step "NGROK" "Detecting ngrok tunnel URL..."
        
        # Try to get ngrok URL from API
        $response = Invoke-RestMethod -Uri "http://localhost:4040/api/tunnels" -ErrorAction SilentlyContinue
        
        if ($response -and $response.tunnels) {
            $tunnel = $response.tunnels | Where-Object { $_.proto -eq "https" } | Select-Object -First 1
            if ($tunnel) {
                $ngrokUrl = $tunnel.public_url
                Write-Success "Ngrok URL detected: $ngrokUrl"
                return $ngrokUrl
            }
        }
        
        # Fallback: try to parse from ngrok web interface
        try {
            $webResponse = Invoke-WebRequest -Uri "http://localhost:4040" -ErrorAction SilentlyContinue
            if ($webResponse.Content -match 'https://[a-zA-Z0-9\-]+\.ngrok-free\.app') {
                $ngrokUrl = $matches[0]
                Write-Success "Ngrok URL detected from web interface: $ngrokUrl"
                return $ngrokUrl
            }
        } catch {
            # Ignore web interface fallback errors
        }
        
        Write-Warning "Could not detect ngrok URL automatically"
        return $null
        
    } catch {
        Write-Warning "Ngrok detection failed: $($_.Exception.Message)"
        return $null
    }
}

function Update-EnvironmentFile {
    param([string]$FilePath, [hashtable]$Updates)
    
    if (!(Test-Path $FilePath)) {
        Write-Warning "Environment file not found: $FilePath"
        return $false
    }
    
    try {
        $content = Get-Content $FilePath -Raw
        
        foreach ($key in $Updates.Keys) {
            $value = $Updates[$key]
            if ($content -match "^$key=") {
                $content = $content -replace "^$key=.*", "$key=$value"
            } else {
                $content += "`n$key=$value"
            }
        }
        
        Set-Content -Path $FilePath -Value $content.Trim()
        Write-Success "Updated $FilePath with new values"
        return $true
        
    } catch {
        Write-Error "Failed to update environment file: $($_.Exception.Message)"
        return $false
    }
}

function Update-FacebookConfig {
    param([string]$NgrokUrl)
    
    Write-Step "FACEBOOK" "Updating Facebook OAuth configuration..."
    
    $facebookCallback = "$NgrokUrl/api/v1/facebook/callback"
    
    # Update backend configuration
    $backendUpdates = @{
        "FB_REDIRECT_URI" = $facebookCallback
        "BASE_URL" = $NgrokUrl
        "USE_NGROK" = "true"
    }
    
    Update-EnvironmentFile -FilePath ".env" -Updates $backendUpdates
    
    # Update CORS in main.py
    $mainPyPath = "backend/app/main.py"
    if (Test-Path $mainPyPath) {
        $content = Get-Content $mainPyPath -Raw
        $ngrokPattern = "https://[a-zA-Z0-9\-]+\.ngrok-free\.app"
        if ($content -notmatch $ngrokPattern) {
            $replacement = "allow_origins=[`n        `"$ngrokUrl`","
            $content = $content -replace 'allow_origins=\[', $replacement
            Set-Content -Path $mainPyPath -Value $content
            Write-Success "Updated CORS configuration for ngrok URL"
        }
    }
    
    # Update frontend environment
    $frontendUpdates = @{
        "NEXT_PUBLIC_API_BASE_URL" = $NgrokUrl
        "NEXT_PUBLIC_BASE_URL" = $NgrokUrl
    }
    
    Update-EnvironmentFile -FilePath "frontend/.env.local" -Updates $frontendUpdates
    
    return $facebookCallback
}

function Build-Frontend {
    Write-Step "BUILD" "Building Next.js frontend..."

    try {
        Push-Location frontend

        # Check if node_modules exists
        if (!(Test-Path "node_modules")) {
            Write-Step "BUILD" "Installing frontend dependencies..."
            & npm install
            if ($LASTEXITCODE -ne 0) {
                Write-Error "npm install failed with exit code: $LASTEXITCODE"
                throw "npm install failed"
            }
        }

        # Build the frontend
        Write-Step "BUILD" "Building production bundle..."
        try {
            $npmCommand = "npm run build"
            Invoke-Expression $npmCommand
            if ($LASTEXITCODE -ne 0) {
                Write-Error "npm run build failed with exit code: $LASTEXITCODE"
                throw "npm run build failed"
            }
        } catch {
            Write-Error "Failed to execute npm run build: $($_.Exception.Message)"
            throw "npm run build failed"
        }

        Pop-Location
        Write-Success "Frontend built successfully"
        return $true

    } catch {
        Write-Error "Frontend build failed: $($_.Exception.Message)"
        if ((Get-Location).Path -like "*frontend") {
            Pop-Location
        }
        return $false
    }
}

function Build-Backend {
    Write-Step "BUILD" "Building FastAPI backend..."
    
    try {
        Push-Location backend
        
        # Build Docker image
        Write-Step "BUILD" "Building Docker image for backend..."
        & docker build -t propertyai-backend:latest .
        if ($LASTEXITCODE -ne 0) { throw "Docker build failed" }
        
        Pop-Location
        Write-Success "Backend Docker image built successfully"
        return $true
        
    } catch {
        Write-Error "Backend build failed: $($_.Exception.Message)"
        Pop-Location
        return $false
    }
}

function Build-FrontendImage {
    Write-Step "BUILD" "Building frontend Docker image..."
    
    try {
        Push-Location frontend
        
        # Build Docker image
        & docker build -f Dockerfile.frontend -t propertyai-frontend:latest .
        if ($LASTEXITCODE -ne 0) { throw "Frontend Docker build failed" }
        
        Pop-Location
        Write-Success "Frontend Docker image built successfully"
        return $true
        
    } catch {
        Write-Error "Frontend Docker build failed: $($_.Exception.Message)"
        Pop-Location
        return $false
    }
}

function Start-Ngrok {
    param([int]$Port = 80)
    
    Write-Step "NGROK" "Checking for existing ngrok tunnel..."
    
    # Check if ngrok is installed
    if (!(Test-Command "ngrok")) {
        Write-Error "ngrok is not installed. Please install ngrok first."
        Write-Host "Download from: https://ngrok.com/download"
        return $false
    }
    
    # Check if ngrok is already running and forwarding the correct port
    try {
        $response = Invoke-RestMethod -Uri "http://localhost:4040/api/tunnels" -ErrorAction SilentlyContinue
        
        if ($response -and $response.tunnels) {
            $tunnel = $response.tunnels | Where-Object { $_.proto -eq "https" -and $_.config.addr -like "*$Port*" } | Select-Object -First 1
            if ($tunnel) {
                $existingUrl = $tunnel.public_url
                Write-Success "Found existing ngrok tunnel forwarding port $Port : $existingUrl"
                return $existingUrl
            }
        }
    } catch {
        # ngrok API not available, continue with starting new tunnel
    }
    
    Write-Step "NGROK" "Starting new ngrok tunnel..."
    
    # Start ngrok in background
    try {
        $ngrokProcess = Start-Process -FilePath "ngrok" -ArgumentList "http $Port" -NoNewWindow -PassThru
        
        # Wait for ngrok to start
        Start-Sleep -Seconds 3
        
        # Try to get the URL
        $ngrokUrl = Get-NgrokUrl
        
        if ($ngrokUrl) {
            Write-Success "Ngrok tunnel started: $ngrokUrl"
            return $ngrokUrl
        } else {
            Write-Warning "Ngrok started but URL detection failed"
            Write-Host "Please check ngrok web interface at: http://localhost:4040"
            return $null
        }
        
    } catch {
        Write-Error "Failed to start ngrok: $($_.Exception.Message)"
        return $false
    }
}

function Wait-ForUserApproval {
    param([string]$NgrokUrl, [string]$FacebookCallback)
    
    Write-Header "FACEBOOK CONFIGURATION REQUIRED"
    
    Write-ColoredOutput "Current ngrok URL: $NgrokUrl" "Cyan"
    Write-ColoredOutput "Facebook Callback URL: $FacebookCallback" "Cyan"
    Write-Host ""
    
    Write-ColoredOutput "Please update your Facebook App settings:" "Yellow"
    Write-Host ""
    Write-ColoredOutput "1. Go to: https://developers.facebook.com/apps/" "White"
    Write-ColoredOutput "2. Select your app" "White"
    Write-ColoredOutput "3. Go to Facebook Login > Settings" "White"
    Write-ColoredOutput "4. Add this URL to 'Valid OAuth Redirect URIs':" "White"
    Write-ColoredOutput "   $FacebookCallback" "Green"
    Write-ColoredOutput "5. Save changes" "White"
    Write-Host ""
    
    if ($Interactive) {
        $confirmation = Read-Host "Have you updated Facebook settings? (y/n)"
        if ($confirmation -ne "y" -and $confirmation -ne "Y") {
            Write-Warning "Facebook configuration not confirmed. Some features may not work."
            return $false
        }
    }
    
    Write-Success "Facebook configuration confirmed"
    return $true
}

function Start-Containers {
    Write-Step "DOCKER" "Starting all containers..."
    
    try {
        Push-Location docker
        
        # Start services
        & docker-compose up -d
        if ($LASTEXITCODE -ne 0) { throw "docker-compose up failed" }
        
        # Wait for services to be healthy
        Write-Step "DOCKER" "Waiting for services to be healthy..."
        Start-Sleep -Seconds 30
        
        # Check backend health
        try {
            $response = Invoke-WebRequest -Uri "http://localhost/health" -Method Get -TimeoutSec 10
            Write-Success "Backend is healthy"
        } catch {
            Write-Warning "Backend health check failed"
        }
        
        Pop-Location
        Write-Success "All containers started successfully"
        return $true
        
    } catch {
        Write-Error "Failed to start containers: $($_.Exception.Message)"
        Pop-Location
        return $false
    }
}

function Run-PlaywrightTests {
    Write-Step "TEST" "Running Playwright E2E tests..."
    
    try {
        # Install dependencies in root directory where package.json is located
        if (!(Test-Path "node_modules")) {
            & npm install
        }
        
        # Install Playwright browsers if needed
        & npx playwright install
        
        Push-Location e2e-tests
        
        # Run tests from e2e-tests directory with explicit config
        $env:E2E_BASE_URL = $using:ngrokUrl
        $env:NEXT_PUBLIC_BASE_URL = $using:ngrokUrl
        
        & npx @playwright/test test --config playwright.config.ts
        if ($LASTEXITCODE -ne 0) { 
            Write-Warning "Some tests failed"
            Pop-Location
            return $false
        }
        
        Pop-Location
        Write-Success "All Playwright tests passed"
        return $true
        
    } catch {
        Write-Error "Playwright tests failed: $($_.Exception.Message)"
        if ((Get-Location).Path -like "*e2e-tests") {
            Pop-Location
        }
        return $false
    }
}

function Run-BackendTests {
    Write-Step "TEST" "Running backend tests..."
    
    try {
        Push-Location backend
        
        # Run pytest
        & python -m pytest tests/ -v
        if ($LASTEXITCODE -ne 0) { 
            Write-Warning "Some backend tests failed"
            return $false
        }
        
        Pop-Location
        Write-Success "All backend tests passed"
        return $true
        
    } catch {
        Write-Error "Backend tests failed: $($_.Exception.Message)"
        Pop-Location
        return $false
    }
}

function Show-Status {
    Write-Header "SYSTEM STATUS"
    
    # Check Docker
    if (Test-Command "docker") {
        Write-ColoredOutput "Docker: " "White" -NoNewline
        Write-ColoredOutput "[OK] Installed" "Green"
    } else {
        Write-ColoredOutput "Docker: " "White" -NoNewline
        Write-ColoredOutput "[NO] Not installed" "Red"
    }
    
    # Check ngrok
    if (Test-Command "ngrok") {
        Write-ColoredOutput "ngrok: " "White" -NoNewline
        Write-ColoredOutput "[OK] Installed" "Green"
    } else {
        Write-ColoredOutput "ngrok: " "White" -NoNewline
        Write-ColoredOutput "[NO] Not installed" "Red"
    }
    
    # Check Node.js
    if (Test-Command "node") {
        $nodeVersion = & node --version
        Write-ColoredOutput "Node.js: " "White" -NoNewline
        Write-ColoredOutput "[OK] $nodeVersion" "Green"
    } else {
        Write-ColoredOutput "Node.js: " "White" -NoNewline
        Write-ColoredOutput "[NO] Not installed" "Red"
    }
    
    # Check Python
    if (Test-Command "python") {
        $pythonVersion = & python --version
        Write-ColoredOutput "Python: " "White" -NoNewline
        Write-ColoredOutput "[OK] $pythonVersion" "Green"
    } else {
        Write-ColoredOutput "Python: " "White" -NoNewline
        Write-ColoredOutput "[NO] Not installed" "Red"
    }
    
    # Check services
    Write-Host ""
    Write-ColoredOutput "Service Status:" "Cyan"
    
    # Check backend
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:8000/health" -Method Get -TimeoutSec 5 -ErrorAction SilentlyContinue
        Write-ColoredOutput "Backend (Local): " "White" -NoNewline
        Write-ColoredOutput "[OK] Running" "Green"
    } catch {
        Write-ColoredOutput "Backend (Local): " "White" -NoNewline
        Write-ColoredOutput "[NO] Not running" "Red"
    }
    
    # Check frontend
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:3000" -Method Get -TimeoutSec 5 -ErrorAction SilentlyContinue
        Write-ColoredOutput "Frontend (Local): " "White" -NoNewline
        Write-ColoredOutput "[OK] Running" "Green"
    } catch {
        Write-ColoredOutput "Frontend (Local): " "White" -NoNewline
        Write-ColoredOutput "[NO] Not running" "Red"
    }
    
    # Check Docker containers
    try {
        $containers = & docker ps --format "table {{.Names}}\t{{.Status}}" 2>$null
        if ($containers -and $containers.Count -gt 1) {
            Write-ColoredOutput "Docker Containers: " "White" -NoNewline
            Write-ColoredOutput "[OK] Running" "Green"
        } else {
            Write-ColoredOutput "Docker Containers: " "White" -NoNewline
            Write-ColoredOutput "[NO] No containers running" "Yellow"
        }
    } catch {
        Write-ColoredOutput "Docker Containers: " "White" -NoNewline
        Write-ColoredOutput "[NO] Docker not running" "Red"
    }
    
    # Check ngrok
    $ngrokUrl = Get-NgrokUrl
    if ($ngrokUrl) {
        Write-ColoredOutput "ngrok URL: " "White" -NoNewline
        Write-ColoredOutput "[OK] $ngrokUrl" "Green"
    } else {
        Write-ColoredOutput "ngrok URL: " "White" -NoNewline
        Write-ColoredOutput "[NO] Not detected" "Yellow"
    }
}

function Cleanup {
    Write-Step "CLEANUP" "Cleaning up resources..."
    
    # Stop local processes
    Get-Process -Name "uvicorn" -ErrorAction SilentlyContinue | Stop-Process -Force
    Get-Process -Name "node" -ErrorAction SilentlyContinue | Stop-Process -Force
    Get-Process -Name "ngrok" -ErrorAction SilentlyContinue | Stop-Process -Force
    
    # Stop Docker containers
    try {
        Push-Location docker
        & docker-compose down 2>$null
        Pop-Location
    } catch {
        # Ignore errors
    }
    
    # Remove Docker images (optional)
    if ($Force) {
        Write-Step "CLEANUP" "Removing Docker images..."
        & docker rmi propertyai-backend:latest 2>$null
        & docker rmi propertyai-frontend:latest 2>$null
    }
    
    Write-Success "Cleanup completed"
}

# Main execution logic
Write-Header "$PROJECT_NAME Deployment Script v$SCRIPT_VERSION"

switch ($Mode) {
    "build-frontend" {
        Write-Header "BUILDING FRONTEND"
        Build-Frontend
    }
    
    "build-backend" {
        Write-Header "BUILDING BACKEND"
        Build-Backend
    }
    
    "build-images" {
        Write-Header "BUILDING DOCKER IMAGES"
        $frontendSuccess = Build-FrontendImage
        $backendSuccess = Build-Backend
        
        if ($frontendSuccess -and $backendSuccess) {
            Write-Success "All Docker images built successfully"
        } else {
            Write-Error "Some image builds failed"
        }
    }
    
    "full-deploy" {
        Write-Header "FULL DEPLOYMENT WORKFLOW"
        
        # Step 1: Build components
        Write-Step "DEPLOY" "Step 1: Building components..."
        $frontendBuilt = Build-Frontend
        $backendBuilt = Build-Backend
        
        if (!$frontendBuilt -or !$backendBuilt) {
            Write-Error "Build failed. Aborting deployment."
            exit 1
        }
        
        # Step 2: Build Docker images
        Write-Step "DEPLOY" "Step 2: Building Docker images..."
        if ($frontendBuilt -and $backendBuilt) {
            $frontendImageBuilt = Build-FrontendImage
        } else {
            Write-Error "Skipping Docker image build due to failed component builds"
            exit 1
        }
        
        # Step 3: Start ngrok
        Write-Step "DEPLOY" "Step 3: Starting ngrok tunnel..."
        $ngrokUrl = Start-Ngrok -Port 80
        
        if (!$ngrokUrl -and !$NgrokUrl) {
            Write-Error "ngrok URL not available. Aborting deployment."
            exit 1
        }
        
        if ($NgrokUrl) {
            $ngrokUrl = $NgrokUrl
        }
        
        # Step 4: Update Facebook configuration
        if (!$SkipFacebook) {
            Write-Step "DEPLOY" "Step 4: Configuring Facebook OAuth..."
            $facebookCallback = Update-FacebookConfig -NgrokUrl $ngrokUrl
            
            # Step 5: Wait for user approval
            Write-Step "DEPLOY" "Step 5: Waiting for Facebook configuration..."
            $facebookApproved = Wait-ForUserApproval -NgrokUrl $ngrokUrl -FacebookCallback $facebookCallback
            
            if (!$facebookApproved -and !$Force) {
                Write-Warning "Facebook configuration not confirmed. Continuing anyway..."
            }
        }
        
        # Step 6: Start containers
        Write-Step "DEPLOY" "Step 6: Starting containers..."
        $containersStarted = Start-Containers
        
        if ($containersStarted) {
            Write-Header "DEPLOYMENT COMPLETE"
            Write-ColoredOutput "Application URL: $ngrokUrl" "Green"
            Write-ColoredOutput "API Docs: $ngrokUrl/docs" "Green"
            Write-ColoredOutput "Facebook Callback: $ngrokUrl/api/v1/facebook/callback" "Green"
        } else {
            Write-Error "Container startup failed"
            exit 1
        }
    }
    
    "test-playwright" {
        Write-Header "RUNNING PLAYWRIGHT TESTS"
        
        # Step 1: Start containers
        Write-Step "TEST" "Step 1: Starting containers for testing..."
        $containersStarted = Start-Containers
        
        if (!$containersStarted) {
            Write-Error "Failed to start containers for testing"
            exit 1
        }
        
        # Step 2: Start ngrok tunnel for external access
        Write-Step "TEST" "Step 2: Starting ngrok tunnel..."
        $ngrokUrl = Start-Ngrok -Port 80
        
        if ($ngrokUrl) {
            Write-Step "TEST" "Step 3: Updating configuration for testing..."
            $facebookCallback = Update-FacebookConfig -NgrokUrl $ngrokUrl
            
            # Set environment variable for tests
            $env:E2E_BASE_URL = $ngrokUrl
            $env:NEXT_PUBLIC_BASE_URL = $ngrokUrl
            
            Write-Step "TEST" "Step 4: Environment configured for E2E testing"
            Write-ColoredOutput "Test Base URL: $ngrokUrl" "Green"
            Write-ColoredOutput "Facebook Callback: $facebookCallback" "Green"
            
            # Step 5: Run the Playwright tests
            Run-PlaywrightTests
        } else {
            Write-Error "Failed to start ngrok tunnel for testing"
            exit 1
        }
    }
    
    "test-backend" {
        Write-Header "RUNNING BACKEND TESTS"
        Run-BackendTests
    }
    
    "ngrok-setup" {
        Write-Header "NGROK TUNNEL SETUP"
        $ngrokUrl = Start-Ngrok -Port 80
        
        if ($ngrokUrl) {
            Write-Step "NGROK" "Updating configuration..."
            $facebookCallback = Update-FacebookConfig -NgrokUrl $ngrokUrl
            Wait-ForUserApproval -NgrokUrl $ngrokUrl -FacebookCallback $facebookCallback
        }
    }
    
    "facebook-config" {
        Write-Header "FACEBOOK OAUTH CONFIGURATION"
        
        $ngrokUrl = Get-NgrokUrl
        if (!$ngrokUrl) {
            Write-Error "ngrok URL not detected. Please start ngrok first."
            exit 1
        }
        
        $facebookCallback = Update-FacebookConfig -NgrokUrl $ngrokUrl
        Wait-ForUserApproval -NgrokUrl $ngrokUrl -FacebookCallback $facebookCallback
    }
    
    "step-deploy" {
        Write-Header "STEP-BY-STEP DEPLOYMENT"
        
        Write-Step "DEPLOY" "Step 1: Starting ngrok tunnel for external access..."
        $ngrokUrl = Start-Ngrok -Port 80
        
        if ($ngrokUrl) {
            Write-Step "DEPLOY" "Step 2: Updating Facebook OAuth configuration..."
            $facebookCallback = Update-FacebookConfig -NgrokUrl $ngrokUrl
            
            Write-Step "DEPLOY" "Step 3: Waiting for Facebook configuration approval..."
            $facebookApproved = Wait-ForUserApproval -NgrokUrl $ngrokUrl -FacebookCallback $facebookCallback
            
            if (!$facebookApproved -and !$Force) {
                Write-Warning "Facebook configuration not confirmed. Please update Facebook app settings first."
                Write-ColoredOutput "Facebook App Settings URL: https://developers.facebook.com/apps/" "Yellow"
                Write-ColoredOutput "Callback URL to add: $facebookCallback" "Yellow"
                Write-ColoredOutput "Run this command after updating Facebook: .\startup.ps1 -Mode step-deploy-continue" "Green"
                Write-ColoredOutput "Or run with -Force to skip: .\startup.ps1 -Mode step-deploy -Force" "Cyan"
                exit 0
            }
            
            Write-Step "DEPLOY" "Step 4: Building frontend and backend..."
            $frontendBuilt = Build-Frontend
            Write-Step "DEPLOY" "Frontend build result: $frontendBuilt"
            $backendBuilt = Build-Backend
            Write-Step "DEPLOY" "Backend build result: $backendBuilt"

            if (!$frontendBuilt -or !$backendBuilt) {
                Write-Error "Build failed. Aborting deployment."
                Write-Step "DEPLOY" "Frontend built: $frontendBuilt, Backend built: $backendBuilt"
                exit 1
            }
            
            Write-Step "DEPLOY" "Step 5: Building Docker images..."
            if ($frontendBuilt -and $backendBuilt) {
                $frontendImageBuilt = Build-FrontendImage
            } else {
                Write-Error "Skipping Docker image build due to failed component builds"
                exit 1
            }
            
            Write-Step "DEPLOY" "Step 6: Starting containers..."
            $containersStarted = Start-Containers
            
            if ($containersStarted) {
                Write-Header "DEPLOYMENT COMPLETE"
                Write-ColoredOutput "Application URL: $ngrokUrl" "Green"
                Write-ColoredOutput "API Docs: $ngrokUrl/docs" "Green"
                Write-ColoredOutput "Facebook Callback: $facebookCallback" "Green"
                Write-ColoredOutput "Ready for Playwright testing! Run: .\startup.ps1 -Mode test-playwright" "Cyan"
            } else {
                Write-Error "Container startup failed"
                exit 1
            }
        } else {
            Write-Error "Failed to start ngrok tunnel"
            exit 1
        }
    }
    
    "step-deploy-continue" {
        Write-Header "CONTINUING STEP-BY-STEP DEPLOYMENT"
        
        # Get existing ngrok URL
        $ngrokUrl = Get-NgrokUrl
        if (!$ngrokUrl) {
            Write-Error "No active ngrok tunnel found. Please run step-deploy first."
            exit 1
        }
        
        Write-Step "DEPLOY" "Continuing with build and deployment..."
        
        # Build frontend and backend
        $frontendBuilt = Build-Frontend
        $backendBuilt = Build-Backend
        
        if (!$frontendBuilt -or !$backendBuilt) {
            Write-Error "Build failed. Aborting deployment."
            exit 1
        }
        
        # Build Docker images
        $frontendImageBuilt = Build-FrontendImage
        
        # Start containers
        $containersStarted = Start-Containers
        
        if ($containersStarted) {
            Write-Header "DEPLOYMENT COMPLETE"
            Write-ColoredOutput "Application URL: $ngrokUrl" "Green"
            Write-ColoredOutput "API Docs: $ngrokUrl/docs" "Green"
            Write-ColoredOutput "Ready for Playwright testing! Run: .\startup.ps1 -Mode test-playwright" "Cyan"
        } else {
            Write-Error "Container startup failed"
            exit 1
        }
    }
    
    "status" {
        Show-Status
    }
    
    default {
        Write-Header "USAGE INFORMATION"
        Write-Host "Usage: .\deploy.ps1 -Mode [mode] [options]"
        Write-Host ""
        Write-ColoredOutput "Available Modes:" "Cyan"
        Write-Host "  build-frontend    - Build Next.js frontend only"
        Write-Host "  build-backend     - Build FastAPI backend only" 
        Write-Host "  build-images      - Build all Docker images"
        Write-Host "  full-deploy       - Complete deployment workflow"
        Write-Host "  step-deploy       - Step-by-step deployment with Facebook approval"
        Write-Host "  step-deploy-continue - Continue step-by-step deployment after Facebook setup"
        Write-Host "  test-playwright   - Run Playwright E2E tests"
        Write-Host "  test-backend      - Run backend unit tests"
        Write-Host "  ngrok-setup       - Setup ngrok tunnel"
        Write-Host "  facebook-config   - Configure Facebook OAuth"
        Write-Host "  cleanup          - Clean up all resources"
        Write-Host "  status           - Show system status"
        Write-Host ""
        Write-ColoredOutput "Options:" "Cyan"
        Write-Host "  -SkipFacebook     - Skip Facebook configuration"
        Write-Host "  -Force           - Force operations without confirmation"
        Write-Host "  -NgrokUrl [url]  - Specify ngrok URL manually"
        Write-Host "  -Interactive     - Enable interactive prompts"
        Write-Host ""
        Write-ColoredOutput "Examples:" "Cyan"
        Write-Host "  .\deploy.ps1 -Mode full-deploy"
        Write-Host "  .\deploy.ps1 -Mode build-frontend -Force"
        Write-Host "  .\deploy.ps1 -Mode test-playwright"
        Write-Host "  .\deploy.ps1 -Mode facebook-config -NgrokUrl https://abc123.ngrok-free.app"
    }
}

Write-Host ""
Write-ColoredOutput "Script completed. Use -Mode status to check system status." "Gray"
