#!/bin/bash

# PropertyAI Mobile App Startup Script
echo "🚀 Starting PropertyAI Mobile App..."

# Check if .env file exists
if [ ! -f .env ]; then
    echo "📝 Creating .env file from template..."
    cp .env.example .env
    echo "⚠️  Please edit .env file and add your GROQ_API_KEY before running the app"
    echo "   You can get your GROQ API key from: https://console.groq.com"
    exit 1
fi

# Check if GROQ_API_KEY is set
if ! grep -q "GROQ_API_KEY=your_groq_api_key_here" .env; then
    echo "✅ GROQ API key configured"
else
    echo "⚠️  Please set your GROQ_API_KEY in the .env file"
    echo "   You can get your GROQ API key from: https://console.groq.com"
    exit 1
fi

# Start the backend server if not running
echo "🔧 Checking backend server..."
if ! curl -s http://127.0.0.1:8003/health > /dev/null; then
    echo "🚨 Backend server not running. Please start the backend first:"
    echo "   cd ../backend && python start.py"
    exit 1
else
    echo "✅ Backend server is running"
fi

# Start the mobile app
echo "📱 Starting Expo development server..."
npx expo start

echo "🎉 PropertyAI Mobile App is ready!"
echo ""
echo "📖 Next steps:"
echo "   1. Scan the QR code with Expo Go app (iOS/Android)"
echo "   2. Or press 'w' to open in web browser"
echo "   3. Or press 'i' for iOS Simulator"
echo "   4. Or press 'a' for Android Emulator"