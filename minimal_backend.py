#!/usr/bin/env python3
"""
Minimal backend for testing Premium Mobile UX
Run this if you're having venv issues
"""

try:
    from fastapi import FastAPI
    from fastapi.middleware.cors import CORSMiddleware
    from fastapi.responses import JSONResponse
    import uvicorn
    HAS_FASTAPI = True
except ImportError:
    print("❌ FastAPI not installed. Run: pip install fastapi uvicorn")
    HAS_FASTAPI = False

if HAS_FASTAPI:
    # Create minimal FastAPI app
    app = FastAPI(
        title="PropertyAI - Premium Mobile CRM",
        version="2.0.0",
        description="Minimal backend for mobile UX testing"
    )

    # CORS for mobile development
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:3000",
            "http://localhost:19006",  # Expo
            "exp://localhost:19000",   # Expo mobile
            "*"
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/health")
    async def health_check():
        return {
            "status": "healthy",
            "version": "2.0.0",
            "mode": "minimal_testing",
            "features": {
                "premium_mobile_ux": True,
                "dynamic_branding": True,
                "groq_ai_integration": True,
                "agent_onboarding": True,
                "biometric_auth": True
            }
        }

    @app.get("/manifest.json")
    async def mobile_manifest():
        return {
            "name": "PropertyAI - Premium Mobile CRM",
            "short_name": "PropertyAI",
            "description": "World's First Gen AI Property Solution",
            "start_url": "/",
            "display": "standalone",
            "background_color": "#2E86AB",
            "theme_color": "#2E86AB"
        }

    @app.get("/api")
    async def api_root():
        return {
            "message": "PropertyAI Premium Mobile CRM API",
            "version": "2.0.0",
            "mode": "minimal_testing",
            "docs": "/docs",
            "health": "/health"
        }

    # Mock auth endpoints for mobile testing
    @app.post("/auth/login")
    async def mock_login():
        return {
            "success": True,
            "token": "mock_token_for_testing",
            "user": {
                "id": 1,
                "firstName": "Demo",
                "lastName": "Agent",
                "email": "demo@propertyai.com",
                "onboardingCompleted": False
            }
        }

    @app.post("/auth/register")
    async def mock_register():
        return {
            "success": True,
            "token": "mock_token_for_testing",
            "user": {
                "id": 1,
                "firstName": "New",
                "lastName": "Agent",
                "email": "new@propertyai.com",
                "onboardingCompleted": False
            }
        }

    # Mock GROQ AI endpoint for testing
    @app.post("/api/ai/generate")
    async def mock_ai_generate():
        return {
            "content": "This is a beautiful 3-bedroom property with modern amenities, perfect for families looking for comfort and style. The spacious layout includes updated kitchen, hardwood floors, and a private backyard ideal for entertaining."
        }

    if __name__ == "__main__":
        print("🚀 Starting Minimal PropertyAI Backend for Mobile UX Testing...")
        print("📱 This provides basic endpoints for mobile app testing")
        print("🔧 For full functionality, fix the main backend dependencies")
        print("")
        
        uvicorn.run(
            app,
            host="0.0.0.0",
            port=8003,
            reload=True
        )
else:
    print("Please install FastAPI: pip install fastapi uvicorn")