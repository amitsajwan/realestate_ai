#!/usr/bin/env python3
"""
PropertyAI - Main Application Entry Point
========================================
FastAPI application for AI-powered real estate platform
"""

from app.core.application import create_application
from app.api.v1.api import api_router

# Create FastAPI application
app = create_application()
app.include_router(api_router, prefix="/api/v1")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)




