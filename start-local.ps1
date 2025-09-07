# =============================================================================
# SIMPLE LOCAL DEVELOPMENT SCRIPT
# =============================================================================
# This script starts the application locally without Docker or ngrok complexity
# Perfect for development and testing

param(
    [Parameter(Mandatory=$false)]
    [ValidateSet("start", "stop", "restart", "status", "logs")]
    [string]$Action = "start",
    
    [Parameter(Mandatory=$false)]
    [switch]$SkipMongo = $false
)

# Configuration
$BACKEND_PORT = 8000
$FRONTEND_PORT = 3000
$MONGO_PORT = 27017

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
        Write-Success "Backend is already running on port $BACKEND_PORT"
        return $true
    }
    
    try {
        Push-Location backend
        
        # Check if virtual environment exists
        if (!(Test-Path ".venv")) {
            Write-Step "BACKEND" "Creating Python virtual environment..."
            python -m venv .venv
        }
        
        # Activate virtual environment
        Write-Step "BACKEND" "Activating virtual environment..."
        & .\.venv\Scripts\Activate.ps1
        
        # Install dependencies
        Write-Step "BACKEND" "Installing Python dependencies..."
        pip install -r requirements.txt
        
        # Start the backend
        Write-Step "BACKEND" "Starting FastAPI server..."
        $backendJob = Start-Job -ScriptBlock {
            Set-Location $using:PWD
            & .\.venv\Scripts\Activate.ps1
            uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
        }
        
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
        Write-Success "Frontend is already running on port $FRONTEND_PORT"
        return $true
    }
    
    try {
        Push-Location frontend
        
        # Check if node_modules exists
        if (!(Test-Path "node_modules")) {
            Write-Step "FRONTEND" "Installing Node.js dependencies..."
            npm install
        }
        
        # Start the frontend
        Write-Step "FRONTEND" "Starting Next.js development server..."
        $frontendJob = Start-Job -ScriptBlock {
            Set-Location $using:PWD
            npm run dev
        }
        
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

function Stop-Services {
    Write-Step "STOP" "Stopping all services..."
    
    # Stop backend
    Get-Process -Name "uvicorn" -ErrorAction SilentlyContinue | Stop-Process -Force
    Get-Process -Name "python" -ErrorAction SilentlyContinue | Where-Object { $_.CommandLine -like "*uvicorn*" } | Stop-Process -Force
    
    # Stop frontend
    Get-Process -Name "node" -ErrorAction SilentlyContinue | Where-Object { $_.CommandLine -like "*next*" } | Stop-Process -Force
    
    # Stop background jobs
    Get-Job | Stop-Job
    Get-Job | Remove-Job
    
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
Write-Header "PropertyAI Local Development"

switch ($Action) {
    "start" {
        Write-Step "START" "Starting all services for local development..."
        
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
        Write-ColorOutput "Access your application:" "Cyan"
        Write-Host "  Frontend: http://localhost:$FRONTEND_PORT"
        Write-Host "  Backend API: http://localhost:$BACKEND_PORT"
        Write-Host "  API Documentation: http://localhost:$BACKEND_PORT/docs"
        Write-Host ""
        Write-ColorOutput "Press Ctrl+C to stop all services" "Yellow"
        
        # Keep script running
        try {
            while ($true) {
                Start-Sleep -Seconds 1
            }
        } catch {
            Write-Host ""
            Write-Step "STOP" "Shutting down services..."
            Stop-Services
        }
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
        Write-Host "  start    - Start all services (default)"
        Write-Host "  stop     - Stop all services"
        Write-Host "  restart  - Restart all services"
        Write-Host "  status   - Show service status"
        Write-Host "  logs     - Show recent logs"
        Write-Host ""
        Write-ColorOutput "Options:" "Cyan"
        Write-Host "  -SkipMongo - Skip MongoDB startup"
        Write-Host ""
        Write-ColorOutput "Examples:" "Cyan"
        Write-Host "  .\start-local.ps1                    # Start all services"
        Write-Host "  .\start-local.ps1 -Action status     # Check status"
        Write-Host "  .\start-local.ps1 -Action stop       # Stop services"
    }
}

Write-Host ""











