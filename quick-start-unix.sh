#!/bin/bash

echo "🚀 PropertyAI Quick Start for Mac/Linux"
echo "======================================"

echo ""
echo "📋 Checking prerequisites..."

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python not found. Please install Python 3.8+ from https://www.python.org/downloads/"
    exit 1
fi
echo "✅ Python found"

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo "❌ Node.js not found. Please install Node.js 18+ from https://nodejs.org/"
    exit 1
fi
echo "✅ Node.js found"

# Check if Git is installed
if ! command -v git &> /dev/null; then
    echo "❌ Git not found. Please install Git from https://git-scm.com/downloads"
    exit 1
fi
echo "✅ Git found"

echo ""
echo "🔧 Setting up backend..."

# Navigate to backend directory
cd backend

# Create virtual environment
echo "Creating Python virtual environment..."
python3 -m venv venv

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install Python dependencies
echo "Installing Python dependencies..."
pip install -r requirements.txt

# Create environment file
echo "Creating environment configuration..."
if [ ! -f .env ]; then
    cp .env.template .env
    echo "✅ Environment file created. Please edit .env with your settings."
else
    echo "✅ Environment file already exists."
fi

echo ""
echo "⚛️ Setting up frontend..."

# Navigate to frontend directory
cd ../frontend

# Install Node.js dependencies
echo "Installing Node.js dependencies..."
npm install

# Create environment file
echo "Creating frontend environment configuration..."
if [ ! -f .env.local ]; then
    cp .env.local.example .env.local
    echo "✅ Frontend environment file created."
else
    echo "✅ Frontend environment file already exists."
fi

echo ""
echo "🎯 Starting services..."

# Start backend in background
echo "Starting backend server..."
cd ../backend
source venv/bin/activate
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload &
BACKEND_PID=$!

# Wait a moment for backend to start
sleep 5

# Start frontend in background
echo "Starting frontend server..."
cd ../frontend
npm run dev &
FRONTEND_PID=$!

echo ""
echo "🎉 Setup complete!"
echo ""
echo "✅ Backend running at: http://localhost:8000"
echo "✅ Frontend running at: http://localhost:3000"
echo "✅ API Documentation: http://localhost:8000/docs"
echo ""
echo "📝 Next steps:"
echo "1. Make sure MongoDB is running (install from https://www.mongodb.com/try/download/community)"
echo "2. Edit backend/.env with your MongoDB URL and secret key"
echo "3. Open http://localhost:3000 in your browser"
echo "4. Register a new user and start using the platform!"
echo ""
echo "Press Ctrl+C to stop all services"

# Function to cleanup on exit
cleanup() {
    echo ""
    echo "🛑 Stopping services..."
    kill $BACKEND_PID 2>/dev/null
    kill $FRONTEND_PID 2>/dev/null
    echo "✅ Services stopped."
    exit 0
}

# Set trap to cleanup on script exit
trap cleanup SIGINT SIGTERM

# Open browser (if possible)
if command -v open &> /dev/null; then
    # macOS
    open http://localhost:3000
elif command -v xdg-open &> /dev/null; then
    # Linux
    xdg-open http://localhost:3000
fi

echo ""
echo "🚀 PropertyAI is now running! Check the terminal for any errors."
echo ""

# Wait for user to stop
wait