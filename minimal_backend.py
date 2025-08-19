#!/usr/bin/env python3
"""
Minimal PropertyAI Backend for Testing Premium Mobile UX
Run this if you're having virtual environment issues
"""

import sys
import os

# Check for FastAPI availability
try:
    from fastapi import FastAPI, Request
    from fastapi.middleware.cors import CORSMiddleware
    from fastapi.responses import JSONResponse, HTMLResponse
    import uvicorn
    HAS_FASTAPI = True
    print("✅ FastAPI available")
except ImportError:
    print("❌ FastAPI not available. Install with: pip install fastapi uvicorn")
    HAS_FASTAPI = False

if HAS_FASTAPI:
    # Create minimal FastAPI app
    app = FastAPI(
        title="PropertyAI - Premium Mobile CRM (Minimal)",
        version="2.0.0",
        description="Minimal backend for testing premium mobile UX"
    )

    # Enhanced CORS for mobile development
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:3000",      # React dev
            "http://localhost:5173",      # Vite dev
            "http://localhost:8080",      # Alternative dev
            "http://localhost:19006",     # Expo web
            "exp://localhost:19000",      # Expo mobile
            "exp://localhost:19006",      # Expo alternative
            "*"  # Allow all for development
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/")
    async def root():
        return HTMLResponse("""
        <html>
            <head>
                <title>PropertyAI - Premium Mobile CRM</title>
                <meta name="viewport" content="width=device-width, initial-scale=1">
            </head>
            <body style="font-family: Arial, sans-serif; text-align: center; padding: 50px;">
                <h1>🏠 PropertyAI - Premium Mobile CRM</h1>
                <p>✅ Backend is running successfully!</p>
                <p>🤖 AI-Powered Features Ready</p>
                <p>📱 Premium Mobile UX Enabled</p>
                <p>🎨 Dynamic Branding System Active</p>
                <br>
                <h3>API Endpoints:</h3>
                <p><a href="/health">/health</a> - Health check</p>
                <p><a href="/manifest.json">/manifest.json</a> - Mobile manifest</p>
                <p><a href="/docs">/docs</a> - API documentation</p>
                <p><a href="/api">/api</a> - API overview</p>
            </body>
        </html>
        """)

    @app.get("/health")
    async def health_check():
        return {
            "status": "healthy",
            "service": "PropertyAI Premium Mobile CRM",
            "version": "2.0.0",
            "mode": "minimal_testing",
            "features": {
                "premium_mobile_ux": True,
                "dynamic_branding": True,
                "groq_ai_integration": True,
                "agent_onboarding": True,
                "biometric_auth": True,
                "haptic_feedback": True,
                "gesture_navigation": True,
                "ai_content_generation": True
            },
            "endpoints": {
                "auth": "/auth/*",
                "mobile": "/api/mobile/*",
                "ai": "/api/ai/*",
                "branding": "/api/branding/*"
            }
        }

    @app.get("/manifest.json")
    async def mobile_manifest():
        return {
            "name": "PropertyAI - Premium Mobile CRM",
            "short_name": "PropertyAI",
            "description": "World's First Gen AI Property Solution with Premium Mobile UX",
            "start_url": "/",
            "display": "standalone",
            "background_color": "#2E86AB",
            "theme_color": "#2E86AB",
            "icons": [
                {
                    "src": "/static/icons/icon-192.png",
                    "sizes": "192x192",
                    "type": "image/png"
                },
                {
                    "src": "/static/icons/icon-512.png",
                    "sizes": "512x512",
                    "type": "image/png"
                }
            ]
        }

    @app.get("/api")
    async def api_root():
        return {
            "message": "PropertyAI Premium Mobile CRM API",
            "version": "2.0.0",
            "mode": "minimal_testing",
            "docs": "/docs",
            "health": "/health",
            "features": [
                "Premium Mobile UX",
                "Dynamic Branding System",
                "GROQ AI Integration",
                "Agent Onboarding Flow",
                "Biometric Authentication",
                "Haptic Feedback System",
                "Gesture Navigation",
                "6-Step Posting Wizard"
            ]
        }

    # Mock authentication endpoints for mobile testing
    @app.post("/auth/login")
    async def mock_login(request: Request):
        try:
            body = await request.json()
            email = body.get("email", "demo@propertyai.com")
            return {
                "success": True,
                "token": "mock_jwt_token_for_testing",
                "user": {
                    "id": 1,
                    "firstName": "Demo",
                    "lastName": "Agent",
                    "email": email,
                    "profileImage": None,
                    "onboardingCompleted": False,
                    "companyName": "Demo Realty",
                    "primaryColor": "#2E86AB"
                }
            }
        except:
            return {"success": False, "error": "Invalid request"}

    @app.post("/auth/register")
    async def mock_register(request: Request):
        try:
            body = await request.json()
            email = body.get("email", "new@propertyai.com")
            return {
                "success": True,
                "token": "mock_jwt_token_for_testing",
                "user": {
                    "id": 2,
                    "firstName": "New",
                    "lastName": "Agent",
                    "email": email,
                    "profileImage": None,
                    "onboardingCompleted": False,
                    "companyName": "",
                    "primaryColor": "#2E86AB"
                }
            }
        except:
            return {"success": False, "error": "Invalid request"}

    # Mock AI content generation for testing
    @app.post("/api/ai/generate")
    async def mock_ai_generate(request: Request):
        try:
            body = await request.json()
            property_type = body.get("type", "property")
            
            # Simulate AI-generated content
            descriptions = {
                "house": "This stunning single-family home offers the perfect blend of modern comfort and classic charm. Featuring spacious rooms, updated kitchen with granite countertops, and a beautifully landscaped backyard perfect for entertaining.",
                "condo": "Discover urban living at its finest in this sophisticated condominium. Floor-to-ceiling windows flood the space with natural light, while premium finishes and amenities provide the ultimate in modern convenience.",
                "apartment": "Experience luxury apartment living with this beautifully appointed residence. Open-concept design, premium appliances, and breathtaking views create an unparalleled living experience.",
                "default": "This exceptional property represents an outstanding opportunity for discerning buyers. With its prime location, quality construction, and thoughtful design, it offers both comfort and investment potential."
            }
            
            content = descriptions.get(property_type, descriptions["default"])
            
            return {
                "success": True,
                "content": content,
                "generated_by": "PropertyAI Mock AI",
                "timestamp": "2025-01-01T00:00:00Z"
            }
        except:
            return {"success": False, "error": "AI generation failed"}

    # Mock branding suggestions
    @app.post("/api/branding/suggest")
    async def mock_branding_suggest(request: Request):
        try:
            body = await request.json()
            business_name = body.get("business_name", "Your Realty")
            
            return {
                "brand_name_options": [
                    f"{business_name}",
                    f"{business_name} Properties",
                    f"{business_name} Realty Group"
                ],
                "tagline": f"Your Trusted {business_name} Partner",
                "colors": {
                    "primary": "#2E86AB",
                    "secondary": "#A23B72", 
                    "accent": "#F18F01"
                },
                "notes": "Mock branding suggestions for testing"
            }
        except:
            return {"success": False, "error": "Branding generation failed"}

    if __name__ == "__main__":
        print("🚀 Starting PropertyAI Minimal Backend...")
        print("📱 Optimized for Premium Mobile UX Testing")
        print("🔧 For full functionality, fix main backend dependencies")
        print("")
        print("🌟 Features enabled:")
        print("   ✅ Premium Mobile UX support")
        print("   ✅ Mock authentication")
        print("   ✅ AI content generation")
        print("   ✅ Branding suggestions")
        print("   ✅ Mobile CORS configuration")
        print("")
        
        try:
            uvicorn.run(
                app,
                host="0.0.0.0",
                port=8003,
                reload=True,
                log_level="info"
            )
        except Exception as e:
            print(f"❌ Error starting server: {e}")
            print("💡 Try: pip install fastapi uvicorn")
else:
    print("")
    print("🚨 FastAPI not installed!")
    print("📦 Quick fix: pip install fastapi uvicorn")
    print("🔄 Then run: python minimal_backend.py")
    print("")
    sys.exit(1)