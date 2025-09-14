#!/bin/bash

echo "🐳 PropertyAI Docker Quick Start"
echo "================================"

echo ""
echo "📋 Checking prerequisites..."

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker not found. Please install Docker Desktop from https://www.docker.com/products/docker-desktop/"
    exit 1
fi
echo "✅ Docker found"

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose not found. Please install Docker Compose."
    exit 1
fi
echo "✅ Docker Compose found"

echo ""
echo "🔧 Setting up environment..."

# Create environment file if it doesn't exist
if [ ! -f .env ]; then
    cp .env.template .env
    echo "✅ Environment file created. Please edit .env with your settings."
    echo "📝 Important: Update MONGODB_URL, SECRET_KEY, and GROQ_API_KEY in .env"
else
    echo "✅ Environment file already exists."
fi

echo ""
echo "🐳 Building and starting Docker containers..."

# Build and start services
docker-compose up --build -d

echo ""
echo "⏳ Waiting for services to start..."
sleep 10

echo ""
echo "🎉 Setup complete!"
echo ""
echo "✅ Frontend: http://localhost:3000"
echo "✅ Backend: http://localhost:8000"
echo "✅ Single URL: http://localhost:80 (Recommended)"
echo "✅ API Documentation: http://localhost:8000/docs"
echo "✅ MongoDB: localhost:27017"
echo ""
echo "📝 Services running:"
docker-compose ps

echo ""
echo "🔍 View logs:"
echo "  docker-compose logs -f"
echo ""
echo "🛑 Stop services:"
echo "  docker-compose down"
echo ""
echo "🔄 Restart services:"
echo "  docker-compose restart"
echo ""

# Open browser (if possible)
if command -v open &> /dev/null; then
    # macOS
    open http://localhost:80
elif command -v xdg-open &> /dev/null; then
    # Linux
    xdg-open http://localhost:80
fi

echo "🚀 PropertyAI is now running with Docker!"
echo "Open http://localhost:80 in your browser to get started."