#!/bin/bash

# Real Estate Platform Startup Script - IMPROVED VERSION
# =====================================================
# Based on lessons learned from troubleshooting

set -e  # Exit on any error

echo "🏗️  Starting Real Estate Platform..."
echo "=================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check if port is in use
check_port() {
    local port=$1
    local service=$2
    
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
        print_error "$service is already running on port $port"
        print_status "Stopping existing $service process..."
        pkill -f "$service" || true
        sleep 2
    fi
}

# Function to wait for service to be ready
wait_for_service() {
    local url=$1
    local service_name=$2
    local max_attempts=30
    local attempt=1
    
    print_status "Waiting for $service_name to be ready..."
    
    while [ $attempt -le $max_attempts ]; do
        if curl -s "$url" > /dev/null 2>&1; then
            print_success "$service_name is ready!"
            return 0
        fi
        
        print_status "Attempt $attempt/$max_attempts - $service_name not ready yet..."
        sleep 2
        ((attempt++))
    done
    
    print_error "$service_name failed to start after $max_attempts attempts"
    return 1
}

# Function to check dependencies
check_dependencies() {
    print_status "Checking dependencies..."
    
    # Check Python
    if ! command -v python3 &> /dev/null; then
        print_error "Python3 is not installed"
        exit 1
    fi
    
    # Check Node.js
    if ! command -v node &> /dev/null; then
        print_error "Node.js is not installed"
        exit 1
    fi
    
    # Check npm
    if ! command -v npm &> /dev/null; then
        print_error "npm is not installed"
        exit 1
    fi
    
    print_success "All dependencies are available"
}

# Function to setup environment
setup_environment() {
    print_status "Setting up environment..."
    
    # Check if virtual environment exists
    if [ ! -d "venv" ]; then
        print_error "Virtual environment not found. Please run setup first."
        print_status "Run: ./setup.sh"
        exit 1
    fi
    
    # Check if .env files exist
    if [ ! -f ".env" ]; then
        print_warning ".env file not found. Creating from template..."
        if [ -f "env.template" ]; then
            cp env.template .env
            print_status "Created .env from template. Please update with your values."
        else
            print_warning "No env.template found. Using default values."
        fi
    fi
    
    # Check if frontend .env exists
    if [ ! -f "frontend/.env.local" ]; then
        print_warning "Frontend .env.local not found. Creating from template..."
        if [ -f "frontend/env.template" ]; then
            cp frontend/env.template frontend/.env.local
            print_status "Created frontend/.env.local from template."
        fi
    fi
}

# Function to install missing dependencies
install_dependencies() {
    print_status "Checking and installing dependencies..."
    
    # Activate virtual environment
    source venv/bin/activate
    
    # Check if pydantic-settings is installed
    if ! python -c "import pydantic_settings" 2>/dev/null; then
        print_status "Installing pydantic-settings..."
        pip install pydantic-settings
    fi
    
    # Check if requests is installed
    if ! python -c "import requests" 2>/dev/null; then
        print_status "Installing requests..."
        pip install requests
    fi
    
    print_success "Dependencies are ready"
}

# Function to start backend
start_backend() {
    print_status "Starting backend server..."
    
    # Check if port 8000 is available
    check_port 8000 "uvicorn"
    
    # Activate virtual environment
    source venv/bin/activate
    
    # Start backend
    cd backend
    python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload > ../backend.log 2>&1 &
    BACKEND_PID=$!
    
    # Wait for backend to be ready
    if wait_for_service "http://localhost:8000/health" "Backend"; then
        print_success "Backend server started successfully (PID: $BACKEND_PID)"
        cd ..
    else
        print_error "Backend server failed to start"
        print_status "Backend logs:"
        cat backend.log | tail -20
        kill $BACKEND_PID 2>/dev/null || true
        exit 1
    fi
}

# Function to start frontend
start_frontend() {
    print_status "Starting frontend server..."
    
    # Check if port 3000 is available
    check_port 3000 "next"
    
    # Start frontend
    cd frontend
    npm run dev > ../frontend.log 2>&1 &
    FRONTEND_PID=$!
    
    # Wait for frontend to be ready
    if wait_for_service "http://localhost:3000" "Frontend"; then
        print_success "Frontend server started successfully (PID: $FRONTEND_PID)"
        cd ..
    else
        print_error "Frontend server failed to start"
        print_status "Frontend logs:"
        cat frontend.log | tail -20
        kill $FRONTEND_PID 2>/dev/null || true
        exit 1
    fi
}

# Function to run health checks
run_health_checks() {
    print_status "Running health checks..."
    
    # Test backend health
    if curl -s http://localhost:8000/health > /dev/null; then
        print_success "Backend health check passed"
    else
        print_warning "Backend health check failed"
    fi
    
    # Test frontend
    if curl -s http://localhost:3000 > /dev/null; then
        print_success "Frontend health check passed"
    else
        print_warning "Frontend health check failed"
    fi
}

# Function to cleanup on exit
cleanup() {
    echo ""
    print_status "Stopping services..."
    
    if [ ! -z "$BACKEND_PID" ]; then
        print_status "Stopping backend (PID: $BACKEND_PID)..."
        kill $BACKEND_PID 2>/dev/null || true
    fi
    
    if [ ! -z "$FRONTEND_PID" ]; then
        print_status "Stopping frontend (PID: $FRONTEND_PID)..."
        kill $FRONTEND_PID 2>/dev/null || true
    fi
    
    # Also kill by process name as backup
    pkill -f "uvicorn app.main:app" 2>/dev/null || true
    pkill -f "npm run dev" 2>/dev/null || true
    
    print_success "All services stopped"
    exit 0
}

# Main execution
main() {
    # Set trap to cleanup on script exit
    trap cleanup SIGINT SIGTERM EXIT
    
    # Run setup steps
    check_dependencies
    setup_environment
    install_dependencies
    
    # Start services
    start_backend
    start_frontend
    
    # Run health checks
    run_health_checks
    
    # Display success message
    echo ""
    print_success "🎉 Application started successfully!"
    echo "=================================="
    echo "🌐 Frontend: http://localhost:3000"
    echo "🔧 Backend:  http://localhost:8000"
    echo "📚 API Docs: http://localhost:8000/docs"
    echo "📊 Health:   http://localhost:8000/health"
    echo ""
    print_status "Logs are available in:"
    echo "  - Backend:  backend.log"
    echo "  - Frontend: frontend.log"
    echo ""
    print_status "Press Ctrl+C to stop all services"
    
    # Wait for user to stop
    wait
}

# Run main function
main "$@"