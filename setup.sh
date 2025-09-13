#!/bin/bash

# Real Estate Platform - Complete Setup Script
# ===========================================
# This script sets up the entire development environment safely

set -e  # Exit on any error

echo "🏗️  Setting up Real Estate Platform Development Environment"
echo "=========================================================="

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

# Check if we're in the right directory
if [ ! -f "README.md" ] || [ ! -d "backend" ] || [ ! -d "frontend" ]; then
    print_error "Please run this script from the project root directory"
    exit 1
fi

# Check system requirements
print_status "Checking system requirements..."

# Check Python version
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version 2>&1 | cut -d' ' -f2)
    print_success "Python $PYTHON_VERSION found"
else
    print_error "Python 3 is required but not installed"
    exit 1
fi

# Check Node.js version
if command -v node &> /dev/null; then
    NODE_VERSION=$(node --version)
    print_success "Node.js $NODE_VERSION found"
else
    print_error "Node.js is required but not installed"
    exit 1
fi

# Check if MongoDB is available (optional)
if command -v mongod &> /dev/null; then
    print_success "MongoDB found"
else
    print_warning "MongoDB not found - will use mock database for development"
fi

# Create virtual environment
print_status "Creating Python virtual environment..."
if [ -d "venv" ]; then
    print_warning "Virtual environment already exists, removing old one..."
    rm -rf venv
fi

python3 -m venv venv
print_success "Virtual environment created"

# Activate virtual environment
print_status "Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
print_status "Upgrading pip..."
pip install --upgrade pip

# Install Python dependencies
print_status "Installing Python dependencies..."
pip install -r backend/requirements.txt
print_success "Python dependencies installed"

# Install Node.js dependencies
print_status "Installing Node.js dependencies..."
cd frontend
npm install
print_success "Node.js dependencies installed"

# Install Playwright browsers
print_status "Installing Playwright browsers..."
npx playwright install
print_success "Playwright browsers installed"

cd ..

# Create environment files
print_status "Creating environment configuration files..."

# Backend environment file
cat > backend/.env << EOF
# Database Configuration
MONGODB_URL=mongodb://localhost:27017
DATABASE_NAME=real_estate_platform

# Authentication
JWT_SECRET_KEY=your-super-secret-jwt-key-change-in-production
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=30

# Facebook Integration (Optional)
FACEBOOK_APP_ID=your-facebook-app-id
FACEBOOK_APP_SECRET=your-facebook-app-secret

# Server Configuration
HOST=0.0.0.0
PORT=8000
DEBUG=True

# CORS Settings
ALLOWED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000

# Rate Limiting
RATE_LIMIT_REQUESTS=100
RATE_LIMIT_WINDOW=60
EOF

# Frontend environment file
cat > frontend/.env.local << EOF
# API Configuration
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_APP_URL=http://localhost:3000

# Feature Flags
NEXT_PUBLIC_ENABLE_MULTILANGUAGE=true
NEXT_PUBLIC_ENABLE_FACEBOOK_INTEGRATION=true

# Facebook Integration (Optional)
NEXT_PUBLIC_FACEBOOK_APP_ID=your-facebook-app-id

# Development Settings
NODE_ENV=development
EOF

print_success "Environment files created"

# Create startup scripts
print_status "Creating startup scripts..."

# Enhanced start script
cat > start_app.sh << 'EOF'
#!/bin/bash

# Real Estate Platform Startup Script
# ===================================

set -e

echo "🏗️  Starting Real Estate Platform..."
echo "=================================="

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found. Please run ./setup.sh first."
    exit 1
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Check if MongoDB is running (optional)
if command -v mongod &> /dev/null; then
    if ! pgrep -x "mongod" > /dev/null; then
        echo "⚠️  MongoDB is not running. Starting with mock database..."
    else
        echo "✅ MongoDB is running"
    fi
else
    echo "⚠️  MongoDB not found. Using mock database..."
fi

# Start backend server
echo "🚀 Starting backend server..."
cd backend
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload &
BACKEND_PID=$!

# Wait for backend to start
echo "⏳ Waiting for backend to start..."
sleep 5

# Check if backend is running
if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo "✅ Backend server started successfully"
else
    echo "❌ Backend server failed to start"
    kill $BACKEND_PID 2>/dev/null || true
    exit 1
fi

# Start frontend server
echo "🌐 Starting frontend server..."
cd ../frontend
npm run dev &
FRONTEND_PID=$!

# Wait for frontend to start
echo "⏳ Waiting for frontend to start..."
sleep 5

echo ""
echo "🎉 Application started successfully!"
echo "=================================="
echo "🌐 Frontend: http://localhost:3000"
echo "🔧 Backend:  http://localhost:8000"
echo "📚 API Docs: http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop all services"

# Function to cleanup on exit
cleanup() {
    echo ""
    echo "🛑 Stopping services..."
    kill $BACKEND_PID 2>/dev/null || true
    kill $FRONTEND_PID 2>/dev/null || true
    echo "✅ All services stopped"
    exit 0
}

# Set trap to cleanup on script exit
trap cleanup SIGINT SIGTERM

# Wait for user to stop
wait
EOF

chmod +x start_app.sh

# Enhanced stop script
cat > stop_app.sh << 'EOF'
#!/bin/bash

# Real Estate Platform Stop Script
# ================================

echo "🛑 Stopping Real Estate Platform..."
echo "================================="

# Stop backend server
echo "🔧 Stopping backend server..."
pkill -f "uvicorn app.main:app" || true

# Stop frontend server
echo "🌐 Stopping frontend server..."
pkill -f "npm run dev" || true

# Wait a moment for processes to stop
sleep 2

# Check if processes are still running
if pgrep -f "uvicorn app.main:app" > /dev/null; then
    echo "⚠️  Backend server still running, force stopping..."
    pkill -9 -f "uvicorn app.main:app" || true
fi

if pgrep -f "npm run dev" > /dev/null; then
    echo "⚠️  Frontend server still running, force stopping..."
    pkill -9 -f "npm run dev" || true
fi

echo "✅ All services stopped successfully"
echo "================================="
EOF

chmod +x stop_app.sh

# Create test script
cat > test_app.sh << 'EOF'
#!/bin/bash

# Real Estate Platform Test Script
# ================================

echo "🧪 Running Real Estate Platform Tests..."
echo "======================================"

# Activate virtual environment
source venv/bin/activate

# Run Python tests
echo "🐍 Running Python tests..."
cd backend
python -m pytest tests/ -v --tb=short
cd ..

# Run frontend tests
echo "⚛️  Running frontend tests..."
cd frontend
npm test -- --watchAll=false
cd ..

# Run Playwright tests
echo "🎭 Running Playwright tests..."
npx playwright test --headed

echo "✅ All tests completed!"
EOF

chmod +x test_app.sh

print_success "Startup scripts created"

# Create Docker configuration
print_status "Creating Docker configuration..."

# Dockerfile for backend
cat > backend/Dockerfile << 'EOF'
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
EOF

# Dockerfile for frontend
cat > frontend/Dockerfile << 'EOF'
FROM node:18-alpine

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm ci --only=production

# Copy source code
COPY . .

# Build the application
RUN npm run build

# Expose port
EXPOSE 3000

# Start the application
CMD ["npm", "start"]
EOF

# Docker Compose file
cat > docker-compose.yml << 'EOF'
version: '3.8'

services:
  mongodb:
    image: mongo:7
    container_name: real-estate-mongodb
    restart: unless-stopped
    ports:
      - "27017:27017"
    environment:
      MONGO_INITDB_DATABASE: real_estate_platform
    volumes:
      - mongodb_data:/data/db
    networks:
      - real-estate-network

  backend:
    build: ./backend
    container_name: real-estate-backend
    restart: unless-stopped
    ports:
      - "8000:8000"
    environment:
      - MONGODB_URL=mongodb://mongodb:27017
      - DATABASE_NAME=real_estate_platform
      - JWT_SECRET_KEY=your-super-secret-jwt-key-change-in-production
      - JWT_ALGORITHM=HS256
      - JWT_EXPIRE_MINUTES=30
      - HOST=0.0.0.0
      - PORT=8000
      - DEBUG=False
    depends_on:
      - mongodb
    networks:
      - real-estate-network
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  frontend:
    build: ./frontend
    container_name: real-estate-frontend
    restart: unless-stopped
    ports:
      - "3000:3000"
    environment:
      - NEXT_PUBLIC_API_URL=http://localhost:8000
      - NEXT_PUBLIC_APP_URL=http://localhost:3000
      - NODE_ENV=production
    depends_on:
      - backend
    networks:
      - real-estate-network

volumes:
  mongodb_data:

networks:
  real-estate-network:
    driver: bridge
EOF

print_success "Docker configuration created"

# Create development tools
print_status "Creating development tools..."

# Pre-commit hook
cat > .pre-commit-config.yaml << 'EOF'
repos:
  - repo: https://github.com/psf/black
    rev: 23.3.0
    hooks:
      - id: black
        language_version: python3
  - repo: https://github.com/pycqa/isort
    rev: 5.12.0
    hooks:
      - id: isort
  - repo: https://github.com/pycqa/flake8
    rev: 6.0.0
    hooks:
      - id: flake8
  - repo: local
    hooks:
      - id: frontend-lint
        name: Frontend Lint
        entry: bash -c 'cd frontend && npm run lint'
        language: system
        files: \.(ts|tsx|js|jsx)$
        pass_filenames: false
EOF

# Git ignore updates
cat >> .gitignore << 'EOF'

# Environment files
.env
.env.local
.env.production
.env.staging

# Virtual environment
venv/
env/

# IDE files
.vscode/
.idea/
*.swp
*.swo

# OS files
.DS_Store
Thumbs.db

# Logs
*.log
logs/

# Database
*.db
*.sqlite

# Docker
.dockerignore

# Test coverage
coverage/
.nyc_output/

# Build outputs
dist/
build/
.next/
out/
EOF

print_success "Development tools created"

# Final setup
print_status "Running final setup checks..."

# Test Python imports
print_status "Testing Python imports..."
cd backend
python -c "
import sys
sys.path.append('.')
try:
    from app.main import app
    print('✅ Backend imports successful')
except Exception as e:
    print(f'❌ Backend import error: {e}')
    sys.exit(1)
"
cd ..

# Test frontend build
print_status "Testing frontend build..."
cd frontend
npm run build
print_success "Frontend build successful"
cd ..

print_success "Setup completed successfully!"
echo ""
echo "🎉 Real Estate Platform is ready!"
echo "================================"
echo ""
echo "Quick Start:"
echo "  ./start_app.sh    - Start the application"
echo "  ./stop_app.sh     - Stop the application"
echo "  ./test_app.sh     - Run all tests"
echo ""
echo "Docker:"
echo "  docker-compose up -d    - Start with Docker"
echo "  docker-compose down     - Stop Docker services"
echo ""
echo "Development:"
echo "  source venv/bin/activate  - Activate Python environment"
echo "  cd frontend && npm run dev  - Start frontend development"
echo "  cd backend && python -m uvicorn app.main:app --reload  - Start backend development"
echo ""
echo "Access the application:"
echo "  Frontend: http://localhost:3000"
echo "  Backend:  http://localhost:8000"
echo "  API Docs: http://localhost:8000/docs"
echo ""