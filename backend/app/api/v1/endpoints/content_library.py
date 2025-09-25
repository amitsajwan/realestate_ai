"""
Content Library API
==================
API for managing content library (posts, templates, etc.)
"""

from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional
from app.schemas.content_library import ContentItem, ContentItemCreate, ContentItemUpdate, ContentItemResponse
from app.services.content_library_service import ContentLibraryService
from app.services.unified_content_service import UnifiedContentService
from app.core.database import get_database
from app.core.unified_auth import get_current_user_token, get_current_agent_token
from motor.motor_asyncio import AsyncIOMotorDatabase
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

def get_content_library_service(db: AsyncIOMotorDatabase = Depends(get_database)) -> ContentLibraryService:
    """Get content library service instance"""
    return ContentLibraryService(db)

def get_unified_content_service(db: AsyncIOMotorDatabase = Depends(get_database)) -> UnifiedContentService:
    """Get unified content service instance"""
    return UnifiedContentService(db)

@router.get("/")
async def get_content_items(
    property_id: Optional[str] = None,
    content_type: Optional[str] = None,
    status: Optional[str] = None,
    current_user: dict = Depends(get_current_user_token),
    service: UnifiedContentService = Depends(get_unified_content_service)
):
    """Get unified content items with optional filtering - includes both content library and social drafts"""
    try:
        # Get unified content items (content library + social drafts)
        unified_items = await service.get_unified_content_items(
            user_id=current_user["_id"],
            property_id=property_id, 
            content_type=content_type, 
            status=status
        )
        return unified_items
    except Exception as e:
        logger.error(f"Error getting content items: {e}")
        raise HTTPException(status_code=500, detail="Failed to get content items")

@router.post("/", response_model=ContentItemResponse)
async def create_content_item(
    content_data: ContentItemCreate,
    current_user: dict = Depends(get_current_user_token),
    service: ContentLibraryService = Depends(get_content_library_service)
):
    """Create new content item"""
    try:
        return await service.create_content_item(content_data, current_user["_id"])
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

@router.post("/publish-drafts")
async def publish_drafts(
    draft_ids: List[str],
    current_user: dict = Depends(get_current_user_token),
    service: UnifiedContentService = Depends(get_unified_content_service)
):
    """Publish drafts from content library"""
    try:
        result = await service.publish_drafts_from_content_library(
            draft_ids=draft_ids,
            user_id=current_user["_id"]
        )
        
        logger.info(f"Published {result.published_count} drafts successfully")
        return result
        
    except Exception as e:
        logger.error(f"Error publishing drafts: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to publish drafts: {str(e)}")

@router.get("/stats")
async def get_content_stats(
    current_user: dict = Depends(get_current_user_token),
    service: UnifiedContentService = Depends(get_unified_content_service)
):
    """Get unified content statistics"""
    try:
        stats = await service.get_content_stats(current_user["_id"])
        return stats
    except Exception as e:
        logger.error(f"Error getting content stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to get content stats")

@router.post("/generate-test-content")
async def generate_test_content(
    current_user: dict = Depends(get_current_user_token),
    service: ContentLibraryService = Depends(get_content_library_service)
):
    """Generate test content for demonstration purposes"""
    try:
        from app.schemas.content_library import ContentItemCreate
        
        # Create a test content item
        test_content = ContentItemCreate(
            property_id="68d4e0ae823db62f27689cf3",  # Use existing property ID
            content_type="social_post",
            title="Test Facebook Post",
            content="🏠 Beautiful 3BHK apartment in prime location! Perfect for families looking for comfort and convenience. Contact us for more details! #RealEstate #Property #Home",
            language="en",
            channels=["facebook", "instagram"],
            hashtags=["#RealEstate", "#Property", "#Home", "#Apartment"],
            status="draft"
        )
        
        result = await service.create_content_item(test_content, current_user["_id"])
        
        logger.info(f"Generated test content: {result.content_id}")
        return {"message": "Test content generated successfully", "content_id": result.content_id}
        
    except Exception as e:
        logger.error(f"Error generating test content: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate test content")
