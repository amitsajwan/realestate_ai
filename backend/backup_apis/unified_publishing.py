"""
Unified Publishing API Endpoints
===============================
Single API interface for all publishing operations
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from app.core.database import get_database
from app.core.auth_backend import current_active_user
from app.models.user import User
from app.services.unified_publishing_orchestrator import (
    UnifiedPublishingOrchestrator,
    UnifiedPublishingRequest,
    ContentType,
    PublishingStatus
)

logger = logging.getLogger(__name__)
router = APIRouter(tags=["unified-publishing"])


# Request/Response Models
class PublishContentRequest(BaseModel):
    """Request model for publishing any type of content"""
    content_type: ContentType = Field(..., description="Type of content to publish")
    content_id: str = Field(..., description="ID of the content to publish")
    channels: List[str] = Field(..., description="Channels to publish to")
    schedule_at: Optional[datetime] = Field(None, description="Schedule publishing for later")
    auto_translate: bool = Field(True, description="Enable auto-translation")
    target_languages: List[str] = Field(["en"], description="Target languages")
    facebook_page_mappings: Dict[str, str] = Field({}, description="Facebook page mappings")


class PublishContentResponse(BaseModel):
    """Response model for publishing operations"""
    success: bool
    content_type: str
    content_id: str
    status: str
    published_channels: List[str]
    failed_channels: List[str]
    message: str
    error: Optional[str] = None
    published_at: Optional[datetime] = None
    publishing_results: Dict[str, Any] = {}


class BatchPublishRequest(BaseModel):
    """Request model for batch publishing multiple items"""
    items: List[PublishContentRequest] = Field(..., description="List of items to publish")


class BatchPublishResponse(BaseModel):
    """Response model for batch publishing operations"""
    total_items: int
    successful_items: int
    failed_items: int
    results: List[PublishContentResponse]


class ContentStatusResponse(BaseModel):
    """Response model for content status"""
    content_type: str
    content_id: str
    status: str
    published_at: Optional[datetime] = None
    channels: List[str] = []
    publishing_status: Dict[str, str] = {}


# Dependency injection
def get_publishing_orchestrator(db=Depends(get_database)) -> UnifiedPublishingOrchestrator:
    """Get unified publishing orchestrator instance"""
    return UnifiedPublishingOrchestrator(db)


# API Endpoints
@router.post("/publish", response_model=PublishContentResponse)
async def publish_content(
    request: PublishContentRequest,
    current_user: User = Depends(current_active_user),
    orchestrator: UnifiedPublishingOrchestrator = Depends(get_publishing_orchestrator)
):
    """
    Universal publishing endpoint that handles all content types.
    
    This endpoint replaces the need for separate publishing endpoints
    and automatically routes content to the appropriate service.
    """
    try:
        user_id = getattr(current_user, "id", "anonymous")
        logger.info(f"Publishing {request.content_type} content {request.content_id} for user {user_id}")
        
        # Create unified publishing request
        publishing_request = UnifiedPublishingRequest(
            content_type=request.content_type,
            content_id=request.content_id,
            channels=request.channels,
            agent_id=str(user_id),
            schedule_at=request.schedule_at,
            auto_translate=request.auto_translate,
            target_languages=request.target_languages,
            facebook_page_mappings=request.facebook_page_mappings
        )
        
        # Publish content
        if request.schedule_at:
            result = await orchestrator.schedule_content(publishing_request, request.schedule_at)
        else:
            result = await orchestrator.publish_content(publishing_request)
        
        # Convert to response model
        response = PublishContentResponse(
            success=result.success,
            content_type=result.content_type.value,
            content_id=result.content_id,
            status=result.status.value,
            published_channels=result.published_channels,
            failed_channels=result.failed_channels,
            message=result.message,
            error=result.error if result.error else None,
            published_at=result.published_at,
            publishing_results=result.publishing_results
        )
        
        if not result.success:
            logger.warning(f"Publishing failed: {result.error}")
            # Don't raise HTTPException, return the response with success=False
            # This allows the frontend to handle the error gracefully
        
        return response
        
    except Exception as e:
        logger.error(f"Error in publish endpoint: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to publish content: {str(e)}"
        )


@router.post("/publish/batch", response_model=BatchPublishResponse)
async def batch_publish_content(
    request: BatchPublishRequest,
    current_user: User = Depends(current_active_user),
    orchestrator: UnifiedPublishingOrchestrator = Depends(get_publishing_orchestrator)
):
    """
    Batch publish multiple pieces of content at once.
    Useful for publishing multiple posts, properties, or mixed content types.
    """
    try:
        user_id = getattr(current_user, "id", "anonymous")
        logger.info(f"Batch publishing {len(request.items)} items for user {user_id}")
        
        results = []
        successful_count = 0
        failed_count = 0
        
        for item in request.items:
            try:
                # Create publishing request
                publishing_request = UnifiedPublishingRequest(
                    content_type=item.content_type,
                    content_id=item.content_id,
                    channels=item.channels,
                    agent_id=str(user_id),
                    schedule_at=item.schedule_at,
                    auto_translate=item.auto_translate,
                    target_languages=item.target_languages,
                    facebook_page_mappings=item.facebook_page_mappings
                )
                
                # Publish content
                if item.schedule_at:
                    result = await orchestrator.schedule_content(publishing_request, item.schedule_at)
                else:
                    result = await orchestrator.publish_content(publishing_request)
                
                # Convert to response
                response = PublishContentResponse(
                    success=result.success,
                    content_type=result.content_type.value,
                    content_id=result.content_id,
                    status=result.status.value,
                    published_channels=result.published_channels,
                    failed_channels=result.failed_channels,
                    message=result.message,
                    error=result.error if result.error else None,
                    published_at=result.published_at,
                    publishing_results=result.publishing_results
                )
                
                results.append(response)
                
                if result.success:
                    successful_count += 1
                else:
                    failed_count += 1
                    
            except Exception as e:
                logger.error(f"Error publishing item {item.content_id}: {e}")
                failed_count += 1
                results.append(PublishContentResponse(
                    success=False,
                    content_type=item.content_type.value,
                    content_id=item.content_id,
                    status=PublishingStatus.FAILED.value,
                    published_channels=[],
                    failed_channels=item.channels,
                    message="",
                    error=str(e)
                ))
        
        return BatchPublishResponse(
            total_items=len(request.items),
            successful_items=successful_count,
            failed_items=failed_count,
            results=results
        )
        
    except Exception as e:
        logger.error(f"Error in batch publish endpoint: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to batch publish content: {str(e)}"
        )


@router.get("/status/{content_type}/{content_id}", response_model=ContentStatusResponse)
async def get_content_status(
    content_type: ContentType,
    content_id: str,
    current_user: User = Depends(current_active_user),
    orchestrator: UnifiedPublishingOrchestrator = Depends(get_publishing_orchestrator)
):
    """
    Get publishing status for any content type.
    Provides unified status checking across all content types.
    """
    try:
        user_id = getattr(current_user, "id", "anonymous")
        logger.info(f"Getting status for {content_type} {content_id} for user {user_id}")
        
        status_data = await orchestrator.get_publishing_status(content_type, content_id)
        
        return ContentStatusResponse(
            content_type=content_type.value,
            content_id=content_id,
            status=status_data.get("status", "unknown"),
            published_at=status_data.get("published_at"),
            channels=status_data.get("channels", []),
            publishing_status=status_data.get("publishing_status", {})
        )
        
    except Exception as e:
        logger.error(f"Error getting content status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get content status: {str(e)}"
        )


@router.get("/health")
async def health_check():
    """Health check endpoint for the unified publishing service"""
    return {
        "status": "healthy",
        "service": "unified-publishing",
        "timestamp": datetime.utcnow().isoformat(),
        "supported_content_types": [ct.value for ct in ContentType],
        "version": "1.0.0"
    }
