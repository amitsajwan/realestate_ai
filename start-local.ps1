# =============================================================================
# SIMPLE LOCAL DEVELOPMENT SCRIPT - MULTI-TERMINAL VERSION
# =============================================================================
# This script starts the application locally with separate terminal windows
# Perfect for development and testing with better visibility

param(
    [Parameter(Mandatory=$false)]
    [ValidateSet("start", "stop", "restart", "status", "logs", "backend", "frontend", "mongo")]
    [string]$Action = "start",
    
    [Parameter(Mandatory=$false)]
    [switch]$SkipMongo = $false,
    
    [Parameter(Mandatory=$false)]
    [switch]$IntegratedTerminal = $false
)

# Configuration
$BACKEND_PORT = 8000
$FRONTEND_PORT = 3000
$MONGO_PORT = 27017

# Global variables for process tracking
$Global:BackendProcess = $null
$Global:FrontendProcess = $null
$Global:MongoProcess = $null

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

function Test-BackendHealthy {
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:$BACKEND_PORT/api/v1/health" -UseBasicParsing -TimeoutSec 5
        return $response.StatusCode -eq 200
    } catch {
        return $false
    }
}

function Test-FrontendHealthy {
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:$FRONTEND_PORT/" -UseBasicParsing -TimeoutSec 5
        return $response.StatusCode -eq 200
    } catch {
        return $false
    }
}

function Stop-StaleLocalProcess {
    param([string]$Name, [string[]]$Patterns)

    foreach ($pattern in $Patterns) {
        Get-Process -Name $Name -ErrorAction SilentlyContinue |
            Where-Object { $_.CommandLine -match $pattern } |
            ForEach-Object { Stop-Process -Id $_.Id -Force -ErrorAction SilentlyContinue }
    }
}

function Start-MongoDB {
    Write-Step "MONGO" "Starting MongoDB..."
    
    if (Test-Port $MONGO_PORT) {
        Write-Success "MongoDB is already running on port $MONGO_PORT"
        return $true
    }
    
    # Try to start MongoDB service
    try {
        Start-Service MongoDB -ErrorAction SilentlyContinue
        Start-Sleep -Seconds 3
        
        if (Test-Port $MONGO_PORT) {
            Write-Success "MongoDB started successfully"
            return $true
        }
    } catch {
        Write-Warning "Could not start MongoDB service automatically"
    }
    
    Write-Warning "MongoDB is not running. Please start MongoDB manually:"
    Write-Host "  - Windows: Start MongoDB service or run 'mongod'"
    Write-Host "  - macOS: brew services start mongodb-community"
    Write-Host "  - Linux: sudo systemctl start mongod"
    return $false
}

function Start-Backend {
    Write-Step "BACKEND" "Starting FastAPI backend..."
    
    if (Test-Port $BACKEND_PORT) {
        if (Test-BackendHealthy) {
            Write-Success "Backend is already running on port $BACKEND_PORT"
            return $true
        }
        Write-Warning "Backend port is occupied but the health endpoint is not healthy; restarting stale backend..."
        Stop-StaleLocalProcess -Name "python" -Patterns @("uvicorn", "app.main")
        Stop-StaleLocalProcess -Name "uvicorn" -Patterns @("uvicorn")
    }
    
    try {
        Push-Location backend
        
        # Check if virtual environment exists
        if (!(Test-Path ".venv")) {
            Write-Step "BACKEND" "Creating Python virtual environment..."
            python -m venv .venv
        }
        
        # Install dependencies
        Write-Step "BACKEND" "Installing Python dependencies..."
        & .\.venv\Scripts\Activate.ps1
        pip install -r requirements.txt
        
        # Create backend startup script
        $backendScript = @"
# PropertyAI Backend - FastAPI Server
Write-Host "================================================================================" -ForegroundColor Cyan
Write-Host "  PropertyAI Backend - FastAPI Server" -ForegroundColor Cyan
Write-Host "================================================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Starting FastAPI server on http://localhost:$BACKEND_PORT" -ForegroundColor Green
Write-Host "Press Ctrl+C to stop the server" -ForegroundColor Yellow
Write-Host ""
Set-Location "$((Get-Location).Path)"
& .\.venv\Scripts\Activate.ps1
uvicorn app.main:app --host 127.0.0.1 --port $BACKEND_PORT --reload
"@
        
        $backendScript | Out-File -FilePath "start_backend.ps1" -Encoding UTF8
        
        # Start backend in new terminal window
        Write-Step "BACKEND" "Opening backend terminal window..."
        $Global:BackendProcess = Start-Process -FilePath "powershell.exe" -ArgumentList "-ExecutionPolicy", "Bypass", "-File", "start_backend.ps1" -WindowStyle Normal
        
        # Wait for backend to start
        $timeout = 30
        $elapsed = 0
        while ($elapsed -lt $timeout) {
            if (Test-Port $BACKEND_PORT) {
                Write-Success "Backend started successfully on http://localhost:$BACKEND_PORT"
                Pop-Location
                return $true
            }
            Start-Sleep -Seconds 1
            $elapsed++
        }
        
        Write-Error "Backend failed to start within $timeout seconds"
        Pop-Location
        return $false
        
    } catch {
        Write-Error "Failed to start backend: $($_.Exception.Message)"
        Pop-Location
        return $false
    }
}

function Start-Frontend {
    Write-Step "FRONTEND" "Starting Next.js frontend..."
    
    if (Test-Port $FRONTEND_PORT) {
        if (Test-FrontendHealthy) {
            Write-Success "Frontend is already running on port $FRONTEND_PORT"
            return $true
        }
        Write-Warning "Frontend port is occupied but the app is not serving a healthy page; restarting stale frontend..."
        Stop-StaleLocalProcess -Name "node" -Patterns @("next", "next-server", "frontend")
        Stop-StaleLocalProcess -Name "powershell" -Patterns @("start_frontend.ps1")
    }
    
    try {
        Push-Location frontend

        # Clear any stale Next.js build cache before starting to avoid reusing broken generated assets.
        if (Test-Path ".next") {
            Write-Step "FRONTEND" "Clearing stale Next.js cache..."
            Remove-Item -Recurse -Force ".next"
        }
        
        # Check if node_modules exists
        if (!(Test-Path "node_modules")) {
            Write-Step "FRONTEND" "Installing Node.js dependencies..."
            npm install
        }
        
        # Create frontend startup script
        $frontendScript = @"
# PropertyAI Frontend - Next.js Server
Write-Host "================================================================================" -ForegroundColor Cyan
Write-Host "  PropertyAI Frontend - Next.js Server" -ForegroundColor Cyan
Write-Host "================================================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Starting Next.js development server on http://localhost:$FRONTEND_PORT" -ForegroundColor Green
Write-Host "Press Ctrl+C to stop the server" -ForegroundColor Yellow
Write-Host ""
Set-Location "$((Get-Location).Path)"
npm run dev
"@
        
        $frontendScript | Out-File -FilePath "start_frontend.ps1" -Encoding UTF8
        
        # Start frontend in new terminal window
        Write-Step "FRONTEND" "Opening frontend terminal window..."
        $Global:FrontendProcess = Start-Process -FilePath "powershell.exe" -ArgumentList "-ExecutionPolicy", "Bypass", "-File", "start_frontend.ps1" -WindowStyle Normal
        
        # Wait for frontend to start
        $timeout = 30
        $elapsed = 0
        while ($elapsed -lt $timeout) {
            if (Test-Port $FRONTEND_PORT) {
                Write-Success "Frontend started successfully on http://localhost:$FRONTEND_PORT"
                Pop-Location
                return $true
            }
            Start-Sleep -Seconds 1
            $elapsed++
        }
        
        Write-Error "Frontend failed to start within $timeout seconds"
        Pop-Location
        return $false
        
    } catch {
        Write-Error "Failed to start frontend: $($_.Exception.Message)"
        Pop-Location
        return $false
    }
}

function Start-Backend-Only {
    Write-Header "Starting Backend Only"
    $backendStarted = Start-Backend
    if ($backendStarted) {
        Write-ColorOutput "Backend is running at http://localhost:$BACKEND_PORT" "Green"
        Write-ColorOutput "API Documentation: http://localhost:$BACKEND_PORT/docs" "Cyan"
    }
}

function Start-Frontend-Only {
    Write-Header "Starting Frontend Only"
    $frontendStarted = Start-Frontend
    if ($frontendStarted) {
        Write-ColorOutput "Frontend is running at http://localhost:$FRONTEND_PORT" "Green"
    }
}

function Stop-Services {
    Write-Step "STOP" "Stopping all services..."
    
    # Stop backend processes more aggressively
    Write-Step "STOP" "Stopping backend processes..."
    Get-Process -Name "uvicorn" -ErrorAction SilentlyContinue | Stop-Process -Force
    Get-Process -Name "python" -ErrorAction SilentlyContinue | Where-Object { $_.CommandLine -like "*uvicorn*" } | Stop-Process -Force
    Get-Process -Name "python" -ErrorAction SilentlyContinue | Where-Object { $_.CommandLine -like "*app.main*" } | Stop-Process -Force
    
    # Stop frontend processes more aggressively
    Write-Step "STOP" "Stopping frontend processes..."
    Get-Process -Name "node" -ErrorAction SilentlyContinue | Where-Object { $_.CommandLine -like "*next*" } | Stop-Process -Force
    Get-Process -Name "node" -ErrorAction SilentlyContinue | Where-Object { $_.CommandLine -like "*npm*" } | Stop-Process -Force
    
    # Stop PowerShell processes running our scripts
    Write-Step "STOP" "Stopping PowerShell script processes..."
    Get-Process -Name "powershell" -ErrorAction SilentlyContinue | Where-Object { 
        $_.CommandLine -like "*start_backend.ps1*" -or 
        $_.CommandLine -like "*start_frontend.ps1*" 
    } | Stop-Process -Force
    
    # Stop terminal windows if they exist
    if ($Global:BackendProcess -and !$Global:BackendProcess.HasExited) {
        Write-Step "STOP" "Closing backend terminal window..."
        $Global:BackendProcess.CloseMainWindow()
        Start-Sleep -Seconds 2
        if (!$Global:BackendProcess.HasExited) {
            $Global:BackendProcess.Kill()
        }
    }
    if ($Global:FrontendProcess -and !$Global:FrontendProcess.HasExited) {
        Write-Step "STOP" "Closing frontend terminal window..."
        $Global:FrontendProcess.CloseMainWindow()
        Start-Sleep -Seconds 2
        if (!$Global:FrontendProcess.HasExited) {
            $Global:FrontendProcess.Kill()
        }
    }
    
    # Keep the repo's startup helper scripts in place so the app can be restarted without
    # leaving tracked files deleted or dirty between local sessions.
    Write-Step "STOP" "Stopping services and leaving the repo clean..."
    
    # Wait a moment for processes to fully stop
    Start-Sleep -Seconds 2
    
    Write-Success "All services stopped"
}

function Show-Status {
    Write-Header "SERVICE STATUS"
    
    # Check MongoDB
    if (Test-Port $MONGO_PORT) {
        Write-ColorOutput "MongoDB: " "White" -NoNewline
        Write-ColorOutput "[RUNNING] Port $MONGO_PORT" "Green"
    } else {
        Write-ColorOutput "MongoDB: " "White" -NoNewline
        Write-ColorOutput "[STOPPED]" "Red"
    }
    
    # Check Backend
    if (Test-Port $BACKEND_PORT) {
        Write-ColorOutput "Backend: " "White" -NoNewline
        Write-ColorOutput "[RUNNING] http://localhost:$BACKEND_PORT" "Green"
    } else {
        Write-ColorOutput "Backend: " "White" -NoNewline
        Write-ColorOutput "[STOPPED]" "Red"
    }
    
    # Check Frontend
    if (Test-Port $FRONTEND_PORT) {
        Write-ColorOutput "Frontend: " "White" -NoNewline
        Write-ColorOutput "[RUNNING] http://localhost:$FRONTEND_PORT" "Green"
    } else {
        Write-ColorOutput "Frontend: " "White" -NoNewline
        Write-ColorOutput "[STOPPED]" "Red"
    }
    
    Write-Host ""
    Write-ColorOutput "Application URLs:" "Cyan"
    Write-Host "  Frontend: http://localhost:$FRONTEND_PORT"
    Write-Host "  Backend API: http://localhost:$BACKEND_PORT"
    Write-Host "  API Docs: http://localhost:$BACKEND_PORT/docs"
}

function Show-Logs {
    Write-Header "RECENT LOGS"
    
    # Show backend logs if available
    if (Test-Path "backend/logs") {
        Write-ColorOutput "Backend Logs:" "Cyan"
        Get-Content "backend/logs/*.log" -Tail 10 -ErrorAction SilentlyContinue
    }
    
    # Show frontend logs if available
    if (Test-Path "frontend/.next") {
        Write-ColorOutput "Frontend Logs:" "Cyan"
        Write-Host "Check the terminal where you started the frontend for logs"
    }
}

# Main execution
Write-Header "PropertyAI Local Development - Multi-Terminal"

switch ($Action) {
    "start" {
        Write-Step "START" "Starting all services with separate terminal windows..."
        
        # Start MongoDB (unless skipped)
        if (!$SkipMongo) {
            $mongoStarted = Start-MongoDB
            if (!$mongoStarted) {
                Write-Warning "Continuing without MongoDB. Some features may not work."
            }
        }
        
        # Start Backend
        $backendStarted = Start-Backend
        if (!$backendStarted) {
            Write-Error "Failed to start backend. Exiting."
            exit 1
        }
        
        # Start Frontend
        $frontendStarted = Start-Frontend
        if (!$frontendStarted) {
            Write-Error "Failed to start frontend. Exiting."
            exit 1
        }
        
        Write-Header "APPLICATION READY"
        Write-ColorOutput "🎉 All services started successfully!" "Green"
        Write-Host ""
        Write-ColorOutput "Each service is running in its own terminal window:" "Cyan"
        Write-Host "  Backend: FastAPI server with hot reload"
        Write-Host "  Frontend: Next.js development server"
        Write-Host ""
        Write-ColorOutput "Access your application:" "Cyan"
        Write-Host "  Frontend: http://localhost:$FRONTEND_PORT"
        Write-Host "  Backend API: http://localhost:$BACKEND_PORT"
        Write-Host "  API Documentation: http://localhost:$BACKEND_PORT/docs"
        Write-Host ""
        Write-ColorOutput "To stop services: .\start-local.ps1 -Action stop" "Yellow"
        Write-ColorOutput "To check status: .\start-local.ps1 -Action status" "Yellow"
    }
    
    "backend" {
        Start-Backend-Only
    }
    
    "frontend" {
        Start-Frontend-Only
    }
    
    "mongo" {
        Start-MongoDB
    }
    
    "stop" {
        Stop-Services
    }
    
    "restart" {
        Stop-Services
        Start-Sleep -Seconds 2
        & $PSCommandPath -Action start
    }
    
    "status" {
        Show-Status
    }
    
    "logs" {
        Show-Logs
    }
    
    default {
        Write-Header "USAGE"
        Write-Host "Usage: .\start-local.ps1 -Action [action]"
        Write-Host ""
        Write-ColorOutput "Available Actions:" "Cyan"
        Write-Host "  start      - Start all services in separate terminals (default)"
        Write-Host "  backend    - Start only the backend service"
        Write-Host "  frontend   - Start only the frontend service"
        Write-Host "  mongo      - Start only MongoDB"
        Write-Host "  stop       - Stop all services"
        Write-Host "  restart    - Restart all services"
        Write-Host "  status     - Show service status"
        Write-Host "  logs       - Show recent logs"
        Write-Host ""
        Write-ColorOutput "Options:" "Cyan"
        Write-Host "  -SkipMongo - Skip MongoDB startup"
        Write-Host ""
        Write-ColorOutput "Examples:" "Cyan"
        Write-Host "  .\start-local.ps1                    # Start all services"
        Write-Host "  .\start-local.ps1 -Action backend   # Start only backend"
        Write-Host "  .\start-local.ps1 -Action status    # Check status"
        Write-Host "  .\start-local.ps1 -Action stop      # Stop services"
    }
}

Write-Host ""











