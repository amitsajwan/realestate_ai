#!/usr/bin/env python3
"""
Avasetu - Main Application Entry Point
========================================
FastAPI application for AI-powered real estate platform.
All API v1 routers are mounted once, in app/core/routes.py (setup_routes).
"""

from app.core.application import create_application

app = create_application()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
