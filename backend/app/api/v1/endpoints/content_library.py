"""
Content Library API
==================
API for managing content library (posts, templates, etc.)
"""

from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional
from app.schemas.content_library import ContentItem, ContentItemCreate, ContentItemUpdate, ContentItemResponse
from app.services.content_library_service import ContentLibraryService
from app.core.database import get_database
from app.models.user import User
from app.core.auth_backend import current_active_user
from motor.motor_asyncio import AsyncIOMotorDatabase
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

def get_content_library_service(db: AsyncIOMotorDatabase = Depends(get_database)) -> ContentLibraryService:
    """Get content library service instance"""
    return ContentLibraryService(db)

@router.get("/", response_model=List[ContentItemResponse])
async def get_content_items(
    property_id: Optional[str] = None,
    content_type: Optional[str] = None,
    status: Optional[str] = None,
    current_user: User = Depends(current_active_user),
    service: ContentLibraryService = Depends(get_content_library_service)
):
    """Get content items with optional filtering - only returns user's own content"""
    try:
        # Always filter by current user to ensure agents only see their own content
        return await service.get_content_items(
            property_id=property_id, 
            content_type=content_type, 
            status=status,
            user_id=str(current_user.id)
        )
    except Exception as e:
        logger.error(f"Error getting content items: {e}")
        raise HTTPException(status_code=500, detail="Failed to get content items")

@router.post("/", response_model=ContentItemResponse)
async def create_content_item(
    content_data: ContentItemCreate,
    current_user: User = Depends(current_active_user),
    service: ContentLibraryService = Depends(get_content_library_service)
):
    """Create new content item"""
    try:
        return await service.create_content_item(content_data, str(current_user.id))
    except Exception as e:
        logger.error(f"Error creating content item: {e}")
        raise HTTPException(status_code=500, detail="Failed to create content item")

@router.put("/{content_id}", response_model=ContentItemResponse)
async def update_content_item(
    content_id: str,
    content_data: ContentItemUpdate,
    service: ContentLibraryService = Depends(get_content_library_service)
):
    """Update content item"""
    try:
        return await service.update_content_item(content_id, content_data)
    except Exception as e:
        logger.error(f"Error updating content item: {e}")
        raise HTTPException(status_code=500, detail="Failed to update content item")

@router.delete("/{content_id}")
async def delete_content_item(
    content_id: str,
    service: ContentLibraryService = Depends(get_content_library_service)
):
    """Delete content item"""
    try:
        await service.delete_content_item(content_id)
        return {"message": "Content item deleted successfully"}
    except Exception as e:
        logger.error(f"Error deleting content item: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete content item")
