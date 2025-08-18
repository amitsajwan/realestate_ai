"""
Real Estate AI CRM - Main Application
=====================================
Unified entry point for the Real Estate CRM system.
Consolidates functionality from multiple duplicate files.
"""
import os
import uvicorn
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from contextlib import asynccontextmanager

from app.config import settings
from app.core.database import init_database
from app.core.exceptions import setup_exception_handlers
from app.api.v1.router import api_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup
    await init_database()
    print(f"🚀 Real Estate CRM starting in {settings.MODE} mode")
    print(f"📍 Server: http://localhost:{settings.PORT}")
    print(f"📚 Docs: http://localhost:{settings.PORT}/docs")
    
    yield
    
    # Shutdown
    print("🛑 Real Estate CRM shutting down")


def create_app() -> FastAPI:
    """Create and configure FastAPI application."""
    app = FastAPI(
        title="Real Estate AI CRM",
        description="AI-powered CRM for real estate agents",
        version="2.0.0",
        lifespan=lifespan,
    )
    
    # Setup exception handlers
    setup_exception_handlers(app)
    
    # Include API router
    app.include_router(api_router, prefix="/api/v1")
    
    # Static files and templates
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    ROOT_DIR = os.path.dirname(BASE_DIR)
    
    app.mount("/static", StaticFiles(directory=os.path.join(ROOT_DIR, "static")), name="static")
    templates = Jinja2Templates(directory=os.path.join(ROOT_DIR, "templates"))
    
    @app.get("/", response_class=HTMLResponse)
    async def login_page(request: Request):
        """Login page."""
        return templates.TemplateResponse("login.html", {"request": request})
    
    @app.get("/dashboard", response_class=HTMLResponse)
    async def dashboard_page(request: Request):
        """Dashboard page."""
        return templates.TemplateResponse("dashboard.html", {"request": request})
    
    @app.get("/health")
    async def health_check():
        """Health check endpoint."""
        return {
            "status": "healthy",
            "mode": settings.MODE,
            "version": "2.0.0"
        }
    
    return app


app = create_app()


if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        workers=1 if settings.DEBUG else 4
    )
