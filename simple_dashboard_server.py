"""Simple FastAPI server for dashboard testing only."""

import asyncio
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Setup basic logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("dashboard-server")

# FastAPI app
app = FastAPI(title="Real Estate Dashboard API")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mock current user dependency for testing
def get_current_user():
    return {"agent_id": "agent_rajesh_kumar", "username": "rajesh"}

# Import and include dashboard router
from api.endpoints.dashboard import router as dashboard_router
app.include_router(dashboard_router, prefix="/api/dashboard", tags=["dashboard"])

@app.get("/")
def root():
    return {"message": "Dashboard API Server is running!", "status": "ok"}

@app.get("/health")
def health_check():
    return {"status": "healthy", "service": "dashboard-api"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("simple_dashboard_server:app", host="0.0.0.0", port=8000, reload=True)
