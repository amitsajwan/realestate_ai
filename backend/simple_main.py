#!/usr/bin/env python3
"""
Simplified main application for testing
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.error_handlers import register_error_handlers
from app.core.logging_config import setup_logging, get_logger
from app.api.v1.endpoints.health import router as health_router

# Initialize logging
setup_logging(environment="development")
logger = get_logger("core")

# Create FastAPI app
app = FastAPI(
    title="PropertyAI API",
    description="AI-powered real estate platform API",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Register error handlers
register_error_handlers(app)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add health check endpoints
app.include_router(health_router, prefix="/api/v1", tags=["health"])

@app.get("/")
async def root():
    return {"message": "PropertyAI API is running!", "status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
