# app/main.py - Fixed imports to work with your existing structure

import sys
import os
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from app.routes import agent_routes
from app.dependencies import init_db
from app.config import settings
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="World Glass Gen AI Property CRM Solution",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(agent_routes.router, prefix="/api")

# Mount static files
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

@app.on_event("startup")
async def startup_event():
    """Initialize application on startup."""
    try:
        # Initialize database
        init_db()
        logger.info("Application started successfully")
    except Exception as e:
        logger.error(f"Error during startup: {e}")
        raise

@app.get("/", response_class=HTMLResponse)
async def root():
    """Root endpoint with basic information."""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>World Glass Gen AI Property CRM</title>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            body { 
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                margin: 0; padding: 40px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white; min-height: 100vh;
            }
            .container { max-width: 800px; margin: 0 auto; text-align: center; }
            h1 { font-size: 3rem; margin-bottom: 20px; font-weight: 300; }
            .subtitle { font-size: 1.5rem; margin-bottom: 40px; opacity: 0.9; }
            .features { display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 30px; margin: 40px 0; }
            .feature { background: rgba(255,255,255,0.1); padding: 30px; border-radius: 15px; backdrop-filter: blur(10px); }
            .feature h3 { margin-bottom: 15px; color: #fff; }
            .feature p { opacity: 0.8; line-height: 1.6; }
            .cta { margin-top: 40px; }
            .btn { display: inline-block; padding: 15px 30px; background: rgba(255,255,255,0.2); 
                   color: white; text-decoration: none; border-radius: 25px; transition: all 0.3s; }
            .btn:hover { background: rgba(255,255,255,0.3); transform: translateY(-2px); }
            .api-links { margin-top: 40px; }
            .api-links a { color: #fff; margin: 0 15px; text-decoration: none; opacity: 0.8; }
            .api-links a:hover { opacity: 1; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🌍 World Glass Gen AI</h1>
            <div class="subtitle">Property CRM Solution</div>
            
            <div class="features">
                <div class="feature">
                    <h3>🤖 AI-Powered Onboarding</h3>
                    <p>Intelligent agent onboarding with GROQ AI for personalized branding and CRM optimization</p>
                </div>
                <div class="feature">
                    <h3>🎨 Dynamic Branding</h3>
                    <p>Customizable visual identity that reflects in every UI component and page</p>
                </div>
                <div class="feature">
                    <h3>📱 Mobile-First Design</h3>
                    <p>Responsive, modern interface optimized for mobile devices and excellent UX</p>
                </div>
                <div class="feature">
                    <h3>📊 Smart CRM</h3>
                    <p>AI-driven customer relationship management with automated insights and strategies</p>
                </div>
            </div>
            
            <div class="cta">
                <a href="/docs" class="btn">View API Documentation</a>
            </div>
            
            <div class="api-links">
                <a href="/docs">API Docs</a>
                <a href="/redoc">ReDoc</a>
                <a href="/api/agents/onboarding/start">Start Onboarding</a>
            </div>
        </div>
    </body>
    </html>
    """

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION
    }

@app.get("/api/health")
async def api_health_check():
    """API health check endpoint."""
    return {
        "status": "healthy",
        "api": "World Glass Gen AI Property CRM API",
        "version": settings.APP_VERSION,
        "features": [
            "Agent Onboarding",
            "AI-Powered Branding",
            "Dynamic CRM",
            "Mobile-First Design"
        ]
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )