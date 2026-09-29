"""
API Router
=========
Main API router that includes all endpoint routers
"""

from fastapi import APIRouter
from app.api.v1.endpoints import (
    agent,
    stats,
    unified_properties,
    unified_publishing
)

api_router = APIRouter()

# Include all endpoint routers
api_router.include_router(agent.router, prefix="/agent", tags=["agent"])
api_router.include_router(stats.router, prefix="/stats", tags=["stats"])
api_router.include_router(unified_properties.router, prefix="/properties", tags=["properties"])
api_router.include_router(unified_publishing.router, prefix="/publishing", tags=["publishing"])