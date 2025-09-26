"""
Image Inheritance API Endpoints
===============================
API endpoints for testing and managing image inheritance from properties to posts
"""

from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel

from app.services.enhanced_post_management_service import EnhancedPostManagementService
from app.core.database import get_database

router = APIRouter()

class ImageInheritanceRequest(BaseModel):
    property_id: str
    platforms: List[str]
    max_images: Optional[int] = None

class ImageInheritanceResponse(BaseModel):
    property_id: str
    available_images: List[str]
    selected_images: List[str]
    max_allowed: int
    platforms: List[str]
    inheritance_successful: bool

@router.post("/inherit-images", response_model=ImageInheritanceResponse)
async def inherit_property_images(
    request: ImageInheritanceRequest,
    db = Depends(get_database)
):
    """
    Test image inheritance from property to post
    """
    try:
        service = EnhancedPostManagementService(db)
        
        # Get property data
        property_data = await service._get_property_data(request.property_id)
        if not property_data:
            raise HTTPException(status_code=404, detail="Property not found")
        
        # Get available images
        available_images = getattr(property_data, 'images', []) or []
        
        # Calculate max images based on platforms
        platform_limits = {
            'instagram': 10,
            'facebook': 20,
            'linkedin': 9,
            'twitter': 4,
            'website': 50
        }
        
        max_allowed = min(
            platform_limits.get(platform, 10) 
            for platform in request.platforms
        ) if request.platforms else 10
        
        if request.max_images:
            max_allowed = min(max_allowed, request.max_images)
        
        # Select images (simple selection for Phase 1)
        selected_images = available_images[:max_allowed]
        
        return ImageInheritanceResponse(
            property_id=request.property_id,
            available_images=available_images,
            selected_images=selected_images,
            max_allowed=max_allowed,
            platforms=request.platforms,
            inheritance_successful=len(selected_images) > 0
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Image inheritance failed: {str(e)}")

@router.get("/platform-limits")
async def get_platform_limits():
    """
    Get image limits for different platforms
    """
    return {
        "instagram": {"max_images": 10, "preferred_aspect_ratio": "1:1"},
        "facebook": {"max_images": 20, "preferred_aspect_ratio": "16:9"},
        "linkedin": {"max_images": 9, "preferred_aspect_ratio": "4:3"},
        "twitter": {"max_images": 4, "preferred_aspect_ratio": "16:9"},
        "website": {"max_images": 50, "preferred_aspect_ratio": "any"}
    }