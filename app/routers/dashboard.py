#!/usr/bin/env python3
"""
Dashboard Router
===============
Handles dashboard-related endpoints and statistics
"""

import logging
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from typing import Dict, Any

logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/stats")
async def get_dashboard_stats(request: Request):
    """Get dashboard statistics"""
    try:
        # For now, return demo stats
        # In production, this should fetch from database based on user
        stats = {
            "totalProperties": 12,
            "aiGenerated": 8,
            "facebookPosts": 15,
            "totalLeads": 24
        }
        
        return JSONResponse(content=stats)
        
    except Exception as e:
        logger.error(f"Error getting dashboard stats: {e}")
        return JSONResponse(
            status_code=500,
            content={"error": "Failed to load dashboard statistics"}
        )

@router.get("/metrics")
async def get_dashboard_metrics(request: Request):
    """Get detailed dashboard metrics"""
    try:
        # For now, return demo metrics
        metrics = {
            "active_listings": 12,
            "total_leads": 24,
            "ai_pages": 8,
            "whatsapp_engagement": 15
        }
        
        return JSONResponse(content=metrics)
        
    except Exception as e:
        logger.error(f"Error getting dashboard metrics: {e}")
        return JSONResponse(
            status_code=500,
            content={"error": "Failed to load dashboard metrics"}
        )
