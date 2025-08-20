#!/bin/bash

# PropertyAI Mobile App Setup Script
echo "🚀 Setting up PropertyAI Mobile App..."

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo "❌ Node.js is not installed. Please install Node.js 18+ first."
    echo "   Download from: https://nodejs.org/"
    exit 1
fi

# Check Node.js version
NODE_VERSION=$(node --version | cut -d'.' -f1 | cut -d'v' -f2)
if [ "$NODE_VERSION" -lt 18 ]; then
    echo "❌ Node.js version 18+ is required. Current version: $(node --version)"
    exit 1
fi

echo "✅ Node.js $(node --version) detected"

# Install Expo CLI globally if not already installed
if ! command -v expo &> /dev/null; then
    echo "📦 Installing Expo CLI..."
    npm install -g @expo/cli
else
    echo "✅ Expo CLI already installed"
fi

# Clear npm cache and node_modules
echo "🧹 Cleaning up existing installation..."
rm -rf node_modules
rm -f package-lock.json
npm cache clean --force

# Install dependencies
echo "📦 Installing dependencies..."
npm install

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo "📝 Creating .env file from template..."
    cp .env.example .env
    echo ""
    echo "⚠️  IMPORTANT: Edit .env file and add your GROQ_API_KEY"
    echo "   1. Get your API key from: https://console.groq.com"
    echo "   2. Replace 'your_groq_api_key_here' with your actual key"
    echo ""
fi

# Create necessary directories
mkdir -p assets
mkdir -p src/screens
mkdir -p src/components
mkdir -p src/utils

# Create placeholder assets if they don't exist
if [ ! -f assets/icon.png ]; then
    echo "📱 Creating placeholder app icon..."
    # Create a simple colored square as placeholder
    # You should replace this with your actual app icon
    echo "Placeholder icon needed at assets/icon.png (1024x1024 px)"
fi

if [ ! -f assets/splash.png ]; then
    echo "🎨 Creating placeholder splash screen..."
    echo "Placeholder splash needed at assets/splash.png (1242x2436 px)"
fi

echo ""
echo "✅ Setup complete!"
echo ""
echo "📖 Next steps:"
echo "   1. Edit .env file and add your GROQ_API_KEY"
echo "   2. Make sure backend server is running on port 8003"
echo "   3. Run 'npm start' to start the development server"
echo ""
echo "🔧 Troubleshooting:"
echo "   • If you get Metro bundler errors, try: npx expo start --clear"
echo "   • For iOS simulator: npx expo start --ios"
echo "   • For Android emulator: npx expo start --android"
echo "   • For web browser: npx expo start --web"