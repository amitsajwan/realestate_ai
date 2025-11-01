"""
API Router
=========
Main API router that includes all endpoint routers
"""

from fastapi import APIRouter
from app.api.v1.endpoints import agent

api_router = APIRouter()

# Include all endpoint routers
api_router.include_router(agent.router, prefix="/agent", tags=["agent"])