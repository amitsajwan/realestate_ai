#!/usr/bin/env python3
"""
API Cleanup Script
=================
This script will:
1. Remove unnecessary API endpoints
2. Keep only essential APIs for Property Marketing Hub
3. Update API documentation
"""

import os
import shutil
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class APICleaner:
    def __init__(self, backend_path: str):
        self.backend_path = Path(backend_path)
        self.api_path = self.backend_path / "app" / "api" / "v1" / "endpoints"
        self.backup_path = self.backend_path / "backup_apis"
        
    def create_backup(self):
        """Create backup of existing APIs"""
        try:
            if self.backup_path.exists():
                shutil.rmtree(self.backup_path)
            
            shutil.copytree(self.api_path, self.backup_path)
            logger.info(f"✅ Created backup at: {self.backup_path}")
        except Exception as e:
            logger.error(f"❌ Failed to create backup: {e}")
            raise
    
    def remove_unnecessary_apis(self):
        """Remove APIs that don't make sense for Property Marketing Hub"""
        try:
            # APIs to remove (these are redundant or not needed)
            apis_to_remove = [
                "posts.py",  # Replaced by content_library
                "post_templates.py",  # Replaced by content_library
                "publishing_history.py",  # Replaced by publishing_logs
                "property_analytics.py",  # Replaced by analytics_data
                "social_media.py",  # Integrated into unified_properties
                "content_generation.py",  # Integrated into unified_properties
                "property_management.py",  # Replaced by unified_properties
                "lead_management.py",  # Simplified to basic lead tracking
                "agent_management.py",  # Simplified to user_profiles
            ]
            
            removed_count = 0
            for api_file in apis_to_remove:
                api_path = self.api_path / api_file
                if api_path.exists():
                    api_path.unlink()
                    logger.info(f"🗑️ Removed: {api_file}")
                    removed_count += 1
                else:
                    logger.info(f"ℹ️ Not found: {api_file}")
            
            logger.info(f"✅ Removed {removed_count} unnecessary API files")
            
        except Exception as e:
            logger.error(f"❌ Failed to remove APIs: {e}")
            raise
    
    def keep_essential_apis(self):
        """Keep only essential APIs for Property Marketing Hub"""
        try:
            # Essential APIs to keep
            essential_apis = [
                "unified_properties.py",  # Main property marketing API
                "content_library.py",  # Content management API
                "publishing_logs.py",  # Publishing tracking API
                "analytics_data.py",  # Analytics API
                "user_profiles.py",  # User management API
                "auth.py",  # Authentication API
                "health.py",  # Health check API
            ]
            
            # Check which essential APIs exist
            existing_apis = []
            for api_file in essential_apis:
                api_path = self.api_path / api_file
                if api_path.exists():
                    existing_apis.append(api_file)
                    logger.info(f"✅ Keeping: {api_file}")
                else:
                    logger.warning(f"⚠️ Missing essential API: {api_file}")
            
            logger.info(f"✅ Kept {len(existing_apis)} essential API files")
            return existing_apis
            
        except Exception as e:
            logger.error(f"❌ Failed to check essential APIs: {e}")
            raise
    
    def update_api_router(self):
        """Update the main API router to include only essential endpoints"""
        try:
            router_path = self.backend_path / "app" / "api" / "v1" / "api.py"
            
            if not router_path.exists():
                logger.warning("⚠️ API router file not found")
                return
            
            # Read current router
            with open(router_path, 'r') as f:
                content = f.read()
            
            # Create new router content
            new_router_content = '''"""
Property Marketing Hub API Router
================================
Unified API router for Property Marketing Hub
"""

from fastapi import APIRouter
from app.api.v1.endpoints import (
    unified_properties,
    content_library,
    publishing_logs,
    analytics_data,
    user_profiles,
    auth,
    health
)

api_router = APIRouter()

# Health check
api_router.include_router(health.router, prefix="/health", tags=["health"])

# Authentication
api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])

# User management
api_router.include_router(user_profiles.router, prefix="/users", tags=["user-profiles"])

# Property Marketing Hub - Main APIs
api_router.include_router(unified_properties.router, prefix="/properties", tags=["property-marketing"])
api_router.include_router(content_library.router, prefix="/content", tags=["content-library"])
api_router.include_router(publishing_logs.router, prefix="/publishing", tags=["publishing-logs"])
api_router.include_router(analytics_data.router, prefix="/analytics", tags=["analytics"])

# Legacy endpoints (for backward compatibility)
# These will be deprecated in future versions
from app.api.v1.endpoints import leads
api_router.include_router(leads.router, prefix="/leads", tags=["leads-legacy"])
'''
            
            # Write new router
            with open(router_path, 'w') as f:
                f.write(new_router_content)
            
            logger.info("✅ Updated API router")
            
        except Exception as e:
            logger.error(f"❌ Failed to update API router: {e}")
            raise
    
    def create_missing_apis(self):
        """Create missing essential APIs"""
        try:
            # Create content_library.py if it doesn't exist
            content_library_path = self.api_path / "content_library.py"
            if not content_library_path.exists():
                content_library_content = '''"""
Content Library API
==================
API for managing content library (posts, templates, etc.)
"""

from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional
from app.schemas.content_library import ContentItem, ContentItemCreate, ContentItemUpdate
from app.services.content_library_service import ContentLibraryService
from app.core.database import get_database
from motor.motor_asyncio import AsyncIOMotorDatabase
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

def get_content_library_service(db: AsyncIOMotorDatabase = Depends(get_database)) -> ContentLibraryService:
    """Get content library service instance"""
    return ContentLibraryService(db)

@router.get("/", response_model=List[ContentItem])
async def get_content_items(
    property_id: Optional[str] = None,
    content_type: Optional[str] = None,
    status: Optional[str] = None,
    service: ContentLibraryService = Depends(get_content_library_service)
):
    """Get content items with optional filtering"""
    try:
        return await service.get_content_items(property_id, content_type, status)
    except Exception as e:
        logger.error(f"Error getting content items: {e}")
        raise HTTPException(status_code=500, detail="Failed to get content items")

@router.post("/", response_model=ContentItem)
async def create_content_item(
    content_data: ContentItemCreate,
    service: ContentLibraryService = Depends(get_content_library_service)
):
    """Create new content item"""
    try:
        return await service.create_content_item(content_data)
    except Exception as e:
        logger.error(f"Error creating content item: {e}")
        raise HTTPException(status_code=500, detail="Failed to create content item")

@router.put("/{content_id}", response_model=ContentItem)
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
'''
                with open(content_library_path, 'w') as f:
                    f.write(content_library_content)
                logger.info("✅ Created content_library.py")
            
            # Create publishing_logs.py if it doesn't exist
            publishing_logs_path = self.api_path / "publishing_logs.py"
            if not publishing_logs_path.exists():
                publishing_logs_content = '''"""
Publishing Logs API
==================
API for tracking publishing history and status
"""

from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional
from app.schemas.publishing_logs import PublishingLog, PublishingLogCreate
from app.services.publishing_logs_service import PublishingLogsService
from app.core.database import get_database
from motor.motor_asyncio import AsyncIOMotorDatabase
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

def get_publishing_logs_service(db: AsyncIOMotorDatabase = Depends(get_database)) -> PublishingLogsService:
    """Get publishing logs service instance"""
    return PublishingLogsService(db)

@router.get("/", response_model=List[PublishingLog])
async def get_publishing_logs(
    property_id: Optional[str] = None,
    content_id: Optional[str] = None,
    channel: Optional[str] = None,
    status: Optional[str] = None,
    service: PublishingLogsService = Depends(get_publishing_logs_service)
):
    """Get publishing logs with optional filtering"""
    try:
        return await service.get_publishing_logs(property_id, content_id, channel, status)
    except Exception as e:
        logger.error(f"Error getting publishing logs: {e}")
        raise HTTPException(status_code=500, detail="Failed to get publishing logs")

@router.post("/", response_model=PublishingLog)
async def create_publishing_log(
    log_data: PublishingLogCreate,
    service: PublishingLogsService = Depends(get_publishing_logs_service)
):
    """Create new publishing log"""
    try:
        return await service.create_publishing_log(log_data)
    except Exception as e:
        logger.error(f"Error creating publishing log: {e}")
        raise HTTPException(status_code=500, detail="Failed to create publishing log")
'''
                with open(publishing_logs_path, 'w') as f:
                    f.write(publishing_logs_content)
                logger.info("✅ Created publishing_logs.py")
            
            # Create analytics_data.py if it doesn't exist
            analytics_data_path = self.api_path / "analytics_data.py"
            if not analytics_data_path.exists():
                analytics_data_content = '''"""
Analytics Data API
=================
API for property and content analytics
"""

from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional, Dict, Any
from app.schemas.analytics_data import AnalyticsData, AnalyticsDataCreate
from app.services.analytics_data_service import AnalyticsDataService
from app.core.database import get_database
from motor.motor_asyncio import AsyncIOMotorDatabase
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

def get_analytics_data_service(db: AsyncIOMotorDatabase = Depends(get_database)) -> AnalyticsDataService:
    """Get analytics data service instance"""
    return AnalyticsDataService(db)

@router.get("/", response_model=List[AnalyticsData])
async def get_analytics_data(
    property_id: Optional[str] = None,
    content_id: Optional[str] = None,
    metric_type: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    service: AnalyticsDataService = Depends(get_analytics_data_service)
):
    """Get analytics data with optional filtering"""
    try:
        return await service.get_analytics_data(property_id, content_id, metric_type, date_from, date_to)
    except Exception as e:
        logger.error(f"Error getting analytics data: {e}")
        raise HTTPException(status_code=500, detail="Failed to get analytics data")

@router.post("/", response_model=AnalyticsData)
async def create_analytics_data(
    analytics_data: AnalyticsDataCreate,
    service: AnalyticsDataService = Depends(get_analytics_data_service)
):
    """Create new analytics data"""
    try:
        return await service.create_analytics_data(analytics_data)
    except Exception as e:
        logger.error(f"Error creating analytics data: {e}")
        raise HTTPException(status_code=500, detail="Failed to create analytics data")

@router.get("/summary", response_model=Dict[str, Any])
async def get_analytics_summary(
    property_id: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    service: AnalyticsDataService = Depends(get_analytics_data_service)
):
    """Get analytics summary"""
    try:
        return await service.get_analytics_summary(property_id, date_from, date_to)
    except Exception as e:
        logger.error(f"Error getting analytics summary: {e}")
        raise HTTPException(status_code=500, detail="Failed to get analytics summary")
'''
                with open(analytics_data_path, 'w') as f:
                    f.write(analytics_data_content)
                logger.info("✅ Created analytics_data.py")
            
            logger.info("✅ Created missing essential APIs")
            
        except Exception as e:
            logger.error(f"❌ Failed to create missing APIs: {e}")
            raise

def main():
    """Main function to cleanup APIs"""
    backend_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    cleaner = APICleaner(backend_path)
    
    try:
        logger.info("🚀 Starting API cleanup...")
        
        # Create backup
        cleaner.create_backup()
        
        # Remove unnecessary APIs
        cleaner.remove_unnecessary_apis()
        
        # Keep essential APIs
        essential_apis = cleaner.keep_essential_apis()
        
        # Create missing APIs
        cleaner.create_missing_apis()
        
        # Update API router
        cleaner.update_api_router()
        
        logger.info("🎉 API cleanup completed successfully!")
        logger.info(f"📋 Essential APIs kept: {len(essential_apis)}")
        
    except Exception as e:
        logger.error(f"❌ API cleanup failed: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())
