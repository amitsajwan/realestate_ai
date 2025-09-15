#!/bin/bash

# 🚀 QUICK START SCRIPT FOR ALL DEVELOPERS
# Run this script to get started immediately

echo "🚀 Starting PropertyAI Development - All Teams Begin!"

# Create necessary directories
mkdir -p /workspace/designs
mkdir -p /workspace/tests

# Backend Team - Fix Dependencies
echo "📦 Backend Team: Fixing dependencies..."
cd /workspace/backend

# Create requirements.txt
cat > requirements.txt << 'EOF'
fastapi==0.104.1
uvicorn[standard]==0.24.0
motor==3.3.2
beanie==1.23.6
pymongo==4.6.0
redis==5.0.1
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
httpx==0.25.2
aiofiles==23.2.1
python-multipart==0.0.6
pydantic==2.5.0
python-dotenv==1.0.0
celery==5.3.4
prometheus-client==0.19.0
structlog==23.2.0
groq==0.4.1
EOF

# Install dependencies
pip install -r requirements.txt

# Test critical imports
echo "🧪 Testing critical imports..."
python -c "from app.services.post_service import PostService; print('✅ PostService import successful')" || echo "❌ PostService import failed"
python -c "from app.services.ai_content_service import AIContentService; print('✅ AIContentService import successful')" || echo "❌ AIContentService import failed"
python -c "from app.services.multi_channel_publishing_service import MultiChannelPublishingService; print('✅ MultiChannelPublishingService import successful')" || echo "❌ MultiChannelPublishingService import failed"

# Frontend Team - Install Dependencies
echo "📦 Frontend Team: Installing dependencies..."
cd /workspace/frontend
npm install

# Test frontend build
echo "🧪 Testing frontend build..."
npm run build || echo "❌ Frontend build failed"

# Create UX design directories
echo "🎨 UX Team: Creating design directories..."
mkdir -p /workspace/designs/{navigation,search,user-flows,content-management,ai-tools,publishing,analytics,mobile,accessibility}

# Create test directories
echo "🧪 QA Team: Creating test directories..."
mkdir -p /workspace/tests/{integration,e2e,performance,ai,publishing,social-media,accessibility,security}

# Start backend server
echo "🚀 Starting backend server..."
cd /workspace/backend
uvicorn app.main:app --reload &
BACKEND_PID=$!

# Wait for backend to start
sleep 5

# Test backend health
echo "🧪 Testing backend health..."
curl -f http://localhost:8000/health || echo "❌ Backend health check failed"

# Start frontend server
echo "🚀 Starting frontend server..."
cd /workspace/frontend
npm run dev &
FRONTEND_PID=$!

# Wait for frontend to start
sleep 10

# Test frontend
echo "🧪 Testing frontend..."
curl -f http://localhost:3000 || echo "❌ Frontend health check failed"

echo "✅ All systems started!"
echo "🌐 Backend: http://localhost:8000"
echo "🌐 Frontend: http://localhost:3000"
echo "📊 Backend PID: $BACKEND_PID"
echo "📊 Frontend PID: $FRONTEND_PID"

echo ""
echo "🎯 TEAM ASSIGNMENTS:"
echo "Backend Dev 1-2: Core Integration"
echo "Backend Dev 3-4: AI Content Service"
echo "Backend Dev 5-6: Multi-Channel Publishing"
echo "Backend Dev 7-8: Analytics & Performance"
echo "Backend Dev 9-10: Testing & Documentation"
echo ""
echo "Frontend Dev 1-2: Core Integration"
echo "Frontend Dev 3-4: AI Content Generation UI"
echo "Frontend Dev 5-6: Multi-Channel Publishing UI"
echo "Frontend Dev 7-8: Analytics Dashboard"
echo "Frontend Dev 9-10: UX Enhancements"
echo ""
echo "UX Designers: Navigation, Content Management, Analytics"
echo "QA Testers: Backend, Frontend, Integration, AI/Publishing, Accessibility"
echo "Architects: System Architecture, Security & DevOps"
echo ""
echo "🚀 All teams can start working now!"
echo "📞 Daily standup at 9 AM"
echo "💬 Communication: #development-team"

# Keep script running
echo "Press Ctrl+C to stop all services"
trap "kill $BACKEND_PID $FRONTEND_PID; exit" INT
wait