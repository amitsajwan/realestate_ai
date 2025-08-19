# app/main.py - FastAPI application entrypoint with premium mobile support

import sys
import os
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from contextlib import asynccontextmanager
import logging

# Import your existing config
from core.config import settings

# Try to import database connection
try:
    from app.core.database import connect_to_mongo, close_mongo_connection
    HAS_DATABASE = True
except ImportError:
    # Fallback for existing database setup
    HAS_DATABASE = False
    print("⚠️  Using legacy database setup")

# Import routers that exist
routers_to_include = []

# Check for existing API routers
try:
    from app.api.v1.router import api_router
    routers_to_include.append(("API v1", api_router, "/api/v1"))
except ImportError:
    print("⚠️  API v1 router not found")

# Check for legacy routes
try:
    from app.routes.proxy import router as proxy_router
    routers_to_include.append(("Proxy", proxy_router, ""))
except ImportError:
    print("⚠️  Proxy router not found")

try:
    from app.routes.auth import router as auth_router
    routers_to_include.append(("Auth", auth_router, ""))
except ImportError:
    print("⚠️  Auth router not found")

try:
    from app.routes.leads import router as leads_router
    routers_to_include.append(("Leads", leads_router, ""))
except ImportError:
    print("⚠️  Leads router not found")

try:
    from app.routes.properties import router as properties_router  
    routers_to_include.append(("Properties", properties_router, ""))
except ImportError:
    print("⚠️  Properties router not found")

try:
    from app.routes.system import router as system_router
    routers_to_include.append(("System", system_router, ""))
except ImportError:
    print("⚠️  System router not found")

# Check for agent onboarding routes
try:
    from app.api.endpoints.agent_onboarding import router as agent_onboarding_router
    routers_to_include.append(("Agent Onboarding", agent_onboarding_router, "/api"))
except ImportError:
    print("⚠️  Agent onboarding router not found")

# Check for mobile-specific routes
try:
    from app.api.endpoints.mobile import router as mobile_router
    routers_to_include.append(("Mobile API", mobile_router, "/api/mobile"))
except ImportError:
    print("⚠️  Mobile API router not found")

# Setup logging
logging.basicConfig(
    level=logging.DEBUG if settings.DEBUG else logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting Real Estate AI CRM with Premium Mobile UX...")
    
    if HAS_DATABASE:
        try:
            await connect_to_mongo()
            logger.info("✅ Database connected")
        except Exception as e:
            logger.error(f"❌ Database connection failed: {e}")
    else:
        logger.info("📊 Using existing database setup")
    
    logger.info("🚀 Premium Mobile CRM Application started successfully")
    
    yield
    
    # Shutdown
    if HAS_DATABASE:
        try:
            await close_mongo_connection()
            logger.info("📊 Database connection closed")
        except Exception as e:
            logger.error(f"Database shutdown error: {e}")
    
    logger.info("👋 Application shutdown complete")

# Create FastAPI app
app = FastAPI(
    title="PropertyAI - Premium Mobile CRM",
    version="2.0.0",
    description="World's First Gen AI Property Solution with Premium Mobile UX",
    lifespan=lifespan
)

# Setup templates
templates = Jinja2Templates(directory="templates")

# WebSocket endpoint for chat
@app.websocket("/chat/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_text()
            await websocket.send_text(f"Message text was: {data}")
    except WebSocketDisconnect:
        logger.info(f"Client {client_id} disconnected")

# CORS middleware - Enhanced for mobile
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        settings.FRONTEND_URL, 
        "http://localhost:3000", 
        "http://localhost:8080", 
        "http://localhost:5173",
        "http://localhost:19006",  # Expo dev server
        "exp://localhost:19000",   # Expo mobile
        "*"  # Allow all origins for mobile development
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Global exception: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "detail": str(exc) if settings.DEBUG else "An error occurred"
        }
    )

# Include all available routers
for name, router, prefix in routers_to_include:
    app.include_router(router, prefix=prefix)
    logger.info(f"✅ Included {name} router at {prefix}")

# Health check endpoint
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "version": "2.0.0",
        "features": {
            "premium_mobile_ux": True,
            "dynamic_branding": True,
            "groq_ai_integration": True,
            "agent_onboarding": True,
            "biometric_auth": True
        }
    }

# Mobile app manifest endpoint
@app.get("/manifest.json")
async def mobile_manifest():
    return {
        "name": "PropertyAI - Premium Mobile CRM",
        "short_name": "PropertyAI",
        "description": "World's First Gen AI Property Solution",
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

# Serve static files
try:
    app.mount("/static", StaticFiles(directory="static"), name="static")
    logger.info("✅ Static files mounted")
except Exception as e:
    logger.warning(f"⚠️  Could not mount static files: {e}")

# Root endpoint
@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    try:
        return templates.TemplateResponse("index.html", {"request": request})
    except Exception as e:
        return HTMLResponse("""
        <html>
            <head><title>PropertyAI - Premium Mobile CRM</title></head>
            <body>
                <h1>🏠 PropertyAI - Premium Mobile CRM</h1>
                <p>World's First Gen AI Property Solution</p>
                <p>✨ Premium Mobile UX Ready</p>
                <p>🤖 AI-Powered Features</p>
                <p>🎨 Dynamic Branding System</p>
            </body>
        </html>
        """)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8003,  # Using standard port
        reload=settings.DEBUG,
        log_level="debug" if settings.DEBUG else "info"
    )