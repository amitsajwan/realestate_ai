#!/bin/bash

echo "🚀 Starting UI Authentication Tests with Playwright"
echo "=================================================="

# Create screenshots directory
mkdir -p screenshots

# Check if frontend is running
echo "🔍 Checking if frontend is running on localhost:3000..."
if curl -s http://localhost:3000 > /dev/null; then
    echo "✅ Frontend is running"
else
    echo "❌ Frontend is not running. Please start it first with: npm run dev"
    exit 1
fi

# Check if backend is running
echo "🔍 Checking if backend is running on localhost:8000..."
if curl -s http://localhost:8000/health > /dev/null; then
    echo "✅ Backend is running"
else
    echo "❌ Backend is not running. Please start it first"
    exit 1
fi

# Install Playwright if not already installed
echo "📦 Installing Playwright dependencies..."
npx playwright install --with-deps

# Run the UI tests
echo "🧪 Running UI Authentication Tests..."
echo "====================================="

# Run the simple UI test runner
npx playwright test ui-test-runner.spec.ts --headed --project=chromium

echo ""
echo "📸 Screenshots saved to: screenshots/"
echo "📊 Test report available at: playwright-report/index.html"
echo "✅ UI Authentication Tests completed!"