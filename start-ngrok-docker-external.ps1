# =============================================================================
# NGROK + DOCKER DEPLOYMENT SCRIPT - EXTERNAL CONFIGURATION APPROACH
# =============================================================================
# This script handles ngrok setup and Docker deployment with EXTERNAL URL mapping
# Application stays clean - no ngrok URLs inside the app configuration

param(
    [Parameter(Mandatory=$false)]
    [ValidateSet("start", "stop", "restart", "status", "logs", "build", "clean", "setup", "oneclick")]
    [string]$Action = "oneclick",
    
    [Parameter(Mandatory=$false)]
    [switch]$Force = $false
)

# Configuration
$DOCKER_COMPOSE_FILE = "docker-compose.yml"
$NGROK_CONFIG_FILE = "ngrok.yml"
$NGROK_ENV_FILE = ".env.ngrok"

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

function Setup-NgrokEnvironment {
    Write-Step "SETUP" "Setting up external ngrok + Docker environment..."
    
    # Create docker-compose override for ngrok
    $overrideContent = @"
# =============================================================================
# DOCKER COMPOSE OVERRIDE FOR NGROK DEPLOYMENT
# =============================================================================
# This file extends docker-compose.yml for ngrok deployment
# Application services remain unchanged - only nginx configuration changes

version: '3.8'

services:
  # Override nginx configuration for ngrok
  nginx:
    image: nginx:alpine
    container_name: real-estate-nginx-ngrok
    restart: unless-stopped
    ports:
      - "80:80"
    volumes:
      - ./docker/nginx-ngrok.conf:/etc/nginx/nginx.conf:ro
    depends_on:
      - frontend
      - backend
    networks:
      - real-estate-network

  # Frontend remains unchanged - uses relative API URLs
  frontend:
    environment:
      # API Configuration - Use relative paths (unchanged)
      - NEXT_PUBLIC_API_BASE_URL=
      - NEXT_PUBLIC_APP_URL=
      
      # Environment
      - NODE_ENV=production

  # Backend remains unchanged - nginx handles CORS
  backend:
    environment:
      # CORS - nginx handles external origins
      - ALLOWED_ORIGINS=http://frontend:3000,http://nginx:80
      
      # Debug mode for ngrok testing
      - DEBUG=True
"@

    $overrideContent | Out-File -FilePath "docker-compose.ngrok.yml" -Encoding UTF8
    Write-Success "Created Docker Compose override: docker-compose.ngrok.yml"
    
    # Create nginx configuration for ngrok
    $nginxConfig = @"
events {
    worker_connections 1024;
}

http {
    include       /etc/nginx/mime.types;
    default_type  application/octet-stream;
    
    # CORS origin mapping for ngrok domains
    map `$http_origin `$cors_origin {
        default "";
        # ngrok domains (all tiers)
        "~^https://.*\.ngrok-free\.app$" `$http_origin;
        "~^https://.*\.ngrok\.io$" `$http_origin;
        "~^https://.*\.ngrok\.app$" `$http_origin;
        
        # Development domains
        "~^http://localhost:3000$" `$http_origin;
        "~^http://127\.0\.0\.1:3000$" `$http_origin;
        
        # Docker internal networks
        "~^http://frontend:3000$" `$http_origin;
        "~^http://nginx:80$" `$http_origin;
    }
    
    # Logging
    log_format main '`$remote_addr - `$remote_user [`$time_local] "`$request" '
                    '`$status `$body_bytes_sent "`$http_referer" '
                    '"`$http_user_agent" "`$http_x_forwarded_for"';
    
    access_log /var/log/nginx/access.log main;
    error_log /var/log/nginx/error.log;
    
    # Gzip compression
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_proxied any;
    gzip_comp_level 6;
    gzip_types
        text/plain
        text/css
        text/xml
        text/javascript
        application/json
        application/javascript
        application/xml+rss
        application/atom+xml
        image/svg+xml;
    
    # Rate limiting
    limit_req_zone `$binary_remote_addr zone=api:10m rate=10r/s;
    limit_req_zone `$binary_remote_addr zone=login:10m rate=1r/s;
    
    # Upstream servers
    upstream backend {
        server backend:8000;
    }
    
    upstream frontend {
        server frontend:3000;
    }
    
    # Main server block
    server {
        listen 80;
        server_name localhost;
        
        # Security headers
        add_header X-Frame-Options "DENY" always;
        add_header X-Content-Type-Options "nosniff" always;
        add_header X-XSS-Protection "1; mode=block" always;
        add_header Referrer-Policy "strict-origin-when-cross-origin" always;
        
        # API routes
        location /api/ {
            limit_req zone=api burst=20 nodelay;
            
            proxy_pass http://backend;
            proxy_set_header Host `$host;
            proxy_set_header X-Real-IP `$remote_addr;
            proxy_set_header X-Forwarded-For `$proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto `$scheme;
            
            # CORS headers - Secure origin whitelist
            add_header Access-Control-Allow-Origin `$cors_origin always;
            add_header Access-Control-Allow-Methods "GET, POST, PUT, DELETE, OPTIONS" always;
            add_header Access-Control-Allow-Headers "DNT,User-Agent,X-Requested-With,If-Modified-Since,Cache-Control,Content-Type,Range,Authorization" always;
            add_header Access-Control-Allow-Credentials "true" always;
            
            if (`$request_method = 'OPTIONS') {
                add_header Access-Control-Allow-Origin `$cors_origin;
                add_header Access-Control-Allow-Methods "GET, POST, PUT, DELETE, OPTIONS";
                add_header Access-Control-Allow-Headers "DNT,User-Agent,X-Requested-With,If-Modified-Since,Cache-Control,Content-Type,Range,Authorization";
                add_header Access-Control-Allow-Credentials "true";
                add_header Access-Control-Max-Age 1728000;
                add_header Content-Type "text/plain; charset=utf-8";
                add_header Content-Length 0;
                return 204;
            }
        }
        
        # Login rate limiting
        location /api/v1/auth/login {
            limit_req zone=login burst=5 nodelay;
            
            proxy_pass http://backend;
            proxy_set_header Host `$host;
            proxy_set_header X-Real-IP `$remote_addr;
            proxy_set_header X-Forwarded-For `$proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto `$scheme;
        }
        
        # Health check
        location /health {
            proxy_pass http://backend;
            proxy_set_header Host `$host;
            proxy_set_header X-Real-IP `$remote_addr;
            proxy_set_header X-Forwarded-For `$proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto `$scheme;
        }
        
        # Frontend routes
        location / {
            proxy_pass http://frontend;
            proxy_set_header Host `$host;
            proxy_set_header X-Real-IP `$remote_addr;
            proxy_set_header X-Forwarded-For `$proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto `$scheme;
            
            # Cache static assets
            location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg)$ {
                expires 1y;
                add_header Cache-Control "public, immutable";
            }
        }
        
        # Error pages
        error_page 404 /404.html;
        error_page 500 502 503 504 /50x.html;
        
        location = /50x.html {
            root /usr/share/nginx/html;
        }
    }
}
"@

    $nginxConfig | Out-File -FilePath "docker/nginx-ngrok.conf" -Encoding UTF8
    Write-Success "Created nginx configuration for ngrok: docker/nginx-ngrok.conf"
}

function Start-DockerWithNgrok {
    Write-Step "DOCKER" "Starting Docker services with external ngrok configuration..."
    
    try {
        # Start Docker services with ngrok override
        Write-Step "DOCKER" "Starting services with ngrok configuration..."
        docker-compose -f docker-compose.yml -f docker-compose.ngrok.yml up -d
        
        # Wait for services to be healthy
        Write-Step "DOCKER" "Waiting for services to be healthy..."
        Start-Sleep -Seconds 30
        
        Write-Success "Docker services started successfully with external ngrok configuration"
        return $true
        
    } catch {
        Write-Error "Failed to start Docker services: $($_.Exception.Message)"
        return $false
    }
}

function Stop-DockerServices {
    Write-Step "DOCKER" "Stopping Docker services..."
    
    try {
        docker-compose -f docker-compose.yml -f docker-compose.ngrok.yml down
        Write-Success "Docker services stopped"
        return $true
    } catch {
        Write-Error "Failed to stop Docker services: $($_.Exception.Message)"
        return $false
    }
}

function Show-Status {
    Write-Header "EXTERNAL NGROK + DOCKER STATUS"
    
    try {
        # Show Docker container status
        Write-ColorOutput "Docker Container Status:" "Cyan"
        docker-compose -f docker-compose.yml -f docker-compose.ngrok.yml ps
        
        Write-Host ""
        Write-ColorOutput "Application URLs:" "Cyan"
        Write-Host "  Local Access (via nginx): http://localhost:80"
        Write-Host "  Direct Frontend: http://localhost:3000"
        Write-Host "  Direct Backend: http://localhost:8000"
        Write-Host "  API Documentation: http://localhost:80/docs"
        Write-Host "  Health Check: http://localhost:80/health"
        Write-Host ""
        Write-ColorOutput "External Access:" "Cyan"
        Write-Host "  Start ngrok: ngrok start app --config ngrok.yml"
        Write-Host "  ngrok will expose: http://localhost:80"
        Write-Host "  Your ngrok URL will be: https://[random].ngrok.io"
        
    } catch {
        Write-Error "Failed to get status: $($_.Exception.Message)"
    }
}

function Start-Ngrok {
    Write-Step "NGROK" "Starting ngrok tunnel..."
    
    try {
        # Start ngrok in background
        Start-Process -FilePath "ngrok" -ArgumentList "start", "app", "--config", "ngrok.yml" -WindowStyle Minimized
        Start-Sleep -Seconds 5
        
        Write-Success "ngrok tunnel started"
        Write-Host ""
        Write-ColorOutput "ngrok is now running in the background" "Green"
        Write-Host "Check ngrok dashboard at: http://localhost:4040"
        Write-Host "Your public URL will be displayed there"
        
        return $true
    } catch {
        Write-Error "Failed to start ngrok: $($_.Exception.Message)"
        return $false
    }
}

function OneClick-Deploy {
    Write-Header "ONE-CLICK NGROK + DOCKER DEPLOYMENT"
    
    # Check prerequisites
    if (!(Test-Command "docker")) {
        Write-Error "Docker is not installed or not in PATH"
        Write-Host "Please install Docker Desktop from https://www.docker.com/products/docker-desktop/"
        exit 1
    }
    
    if (!(Test-DockerRunning)) {
        Write-Error "Docker is not running. Please start Docker Desktop."
        exit 1
    }
    
    if (!(Test-Command "ngrok")) {
        Write-Error "ngrok is not installed or not in PATH"
        Write-Host "Please install ngrok from https://ngrok.com/download"
        exit 1
    }
    
    Write-Step "ONE-CLICK" "Starting one-click deployment process..."
    
    # Step 1: Setup environment
    Write-Step "SETUP" "Setting up external ngrok + Docker environment..."
    Setup-NgrokEnvironment
    
    # Step 2: Start Docker services
    Write-Step "DOCKER" "Starting Docker services..."
    $dockerSuccess = Start-DockerWithNgrok
    if (!$dockerSuccess) {
        Write-Error "Failed to start Docker services. Exiting."
        exit 1
    }
    
    # Step 3: Start ngrok
    Write-Step "NGROK" "Starting ngrok tunnel..."
    $ngrokSuccess = Start-Ngrok
    if (!$ngrokSuccess) {
        Write-Warning "Failed to start ngrok. Docker services are still running."
        Write-Host "You can start ngrok manually: ngrok start app --config ngrok.yml"
    }
    
    # Step 4: Show final status
    Write-Header "DEPLOYMENT COMPLETE"
    Write-ColorOutput "🎉 One-click deployment completed successfully!" "Green"
    Write-Host ""
    Write-ColorOutput "Architecture:" "Cyan"
    Write-Host "  ngrok (external) → nginx:80 → internal services"
    Write-Host "  Application configuration: UNCHANGED (clean)"
    Write-Host "  CORS handling: EXTERNAL (nginx)"
    Write-Host ""
    Write-ColorOutput "Access your application:" "Cyan"
    Write-Host "  Local: http://localhost:80"
    Write-Host "  ngrok Dashboard: http://localhost:4040"
    Write-Host "  API Documentation: http://localhost:80/docs"
    Write-Host "  Health Check: http://localhost:80/health"
    Write-Host ""
    Write-ColorOutput "Next steps:" "Yellow"
    Write-Host "1. Check ngrok dashboard at http://localhost:4040 for your public URL"
    Write-Host "2. Use the ngrok URL to access your application externally"
    Write-Host "3. To stop: .\start-ngrok-docker-external.ps1 -Action stop"
    Write-Host "4. To check status: .\start-ngrok-docker-external.ps1 -Action status"
}

# Main execution
Write-Header "PropertyAI External ngrok + Docker Deployment"

switch ($Action) {
    "setup" {
        Write-Step "SETUP" "Setting up external ngrok + Docker environment..."
        Setup-NgrokEnvironment
        Write-Success "Setup complete! Architecture:"
        Write-Host ""
        Write-ColorOutput "External Configuration Architecture:" "Cyan"
        Write-Host "  ngrok → nginx:80 → internal services"
        Write-Host "  Application stays clean (no ngrok URLs inside)"
        Write-Host "  CORS handled by nginx (external mapping)"
        Write-Host ""
        Write-Success "Next steps:"
        Write-Host "1. Start ngrok: ngrok start app --config ngrok.yml"
        Write-Host "2. Start Docker: .\start-ngrok-docker-external.ps1 -Action start"
        Write-Host "3. Access via ngrok URL: https://[your-ngrok-url].ngrok.io"
    }
    
    "start" {
        if (!(Test-Path "docker-compose.ngrok.yml")) {
            Write-Error "ngrok configuration not found. Run setup first: .\start-ngrok-docker-external.ps1 -Action setup"
            exit 1
        }
        
        $startSuccess = Start-DockerWithNgrok
        if ($startSuccess) {
            Write-Header "EXTERNAL DEPLOYMENT COMPLETE"
            Write-ColorOutput "🎉 Application deployed with external ngrok configuration!" "Green"
            Write-Host ""
            Write-ColorOutput "Architecture:" "Cyan"
            Write-Host "  ngrok (external) → nginx:80 → internal services"
            Write-Host "  Application configuration: UNCHANGED"
            Write-Host "  CORS handling: EXTERNAL (nginx)"
            Write-Host ""
            Write-ColorOutput "Access your application:" "Cyan"
            Write-Host "  Local: http://localhost:80"
            Write-Host "  External: Start ngrok and use your ngrok URL"
            Write-Host "  API Documentation: http://localhost:80/docs"
            Write-Host "  Health Check: http://localhost:80/health"
        }
    }
    
    "oneclick" {
        OneClick-Deploy
    }
    
    "stop" {
        Stop-DockerServices
    }
    
    "restart" {
        Stop-DockerServices
        Start-Sleep -Seconds 2
        & $PSCommandPath -Action start
    }
    
    "status" {
        Show-Status
    }
    
    "logs" {
        Write-Header "CONTAINER LOGS"
        docker-compose -f docker-compose.yml -f docker-compose.ngrok.yml logs --tail=50
    }
    
    "clean" {
        Stop-DockerServices
        if ($Force) {
            docker-compose -f docker-compose.yml -f docker-compose.ngrok.yml down -v --rmi all
            docker system prune -f
        }
        Write-Success "Cleanup complete"
    }
    
    default {
        Write-Header "USAGE"
        Write-Host "Usage: .\start-ngrok-docker-external.ps1 -Action [action]"
        Write-Host ""
        Write-ColorOutput "Available Actions:" "Cyan"
        Write-Host "  oneclick     - One-click deployment (default)"
        Write-Host "  setup        - Setup external ngrok + Docker environment"
        Write-Host "  start        - Start Docker with external ngrok configuration"
        Write-Host "  stop         - Stop Docker services"
        Write-Host "  restart      - Restart Docker services"
        Write-Host "  status       - Show status"
        Write-Host "  logs         - Show logs"
        Write-Host "  clean        - Clean up resources"
        Write-Host ""
        Write-ColorOutput "External Configuration Benefits:" "Cyan"
        Write-Host "  ✅ Application stays clean (no ngrok URLs inside)"
        Write-Host "  ✅ CORS handled externally by nginx"
        Write-Host "  ✅ Easy switching between local/ngrok deployment"
        Write-Host "  ✅ Production-ready architecture"
        Write-Host ""
        Write-ColorOutput "Examples:" "Cyan"
        Write-Host "  .\start-ngrok-docker-external.ps1                    # One-click deployment"
        Write-Host "  .\start-ngrok-docker-external.ps1 -Action setup     # Setup only"
        Write-Host "  .\start-ngrok-docker-external.ps1 -Action start     # Start Docker only"
        Write-Host "  .\start-ngrok-docker-external.ps1 -Action status    # Check status"
    }
}

Write-Host ""
