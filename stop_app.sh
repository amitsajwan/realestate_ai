#!/bin/bash

# Real Estate Platform Stop Script
# ================================

echo "🛑 Stopping Real Estate Platform..."
echo "================================="

# Stop backend server
echo "🔧 Stopping backend server..."
pkill -f "uvicorn app.main:app"

# Stop frontend server
echo "🌐 Stopping frontend server..."
pkill -f "npm run dev"

# Wait a moment for processes to stop
sleep 2

# Check if processes are still running
if pgrep -f "uvicorn app.main:app" > /dev/null; then
    echo "⚠️  Backend server still running, force stopping..."
    pkill -9 -f "uvicorn app.main:app"
fi

if pgrep -f "npm run dev" > /dev/null; then
    echo "⚠️  Frontend server still running, force stopping..."
    pkill -9 -f "npm run dev"
fi

echo "✅ All services stopped successfully"
echo "================================="