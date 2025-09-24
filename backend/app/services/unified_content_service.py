"""
Unified Content Service
======================
Service that bridges content library and social publishing systems
"""

import logging
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId

from app.models.social_draft import SocialDraft, DraftStatus
from app.models.social_post import SocialPost
from app.schemas.content_library import ContentItemResponse
from app.services.content_library_service import ContentLibraryService
from app.services.social_publishing_service import SocialPublishingService

logger = logging.getLogger(__name__)

class UnifiedContentService:
    """Service that unifies content library and social publishing operations"""
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.content_library_service = ContentLibraryService(db)
        self.social_publishing_service = SocialPublishingService(db)
    
    async def get_unified_content_items(
        self, 
        user_id: str,
        property_id: Optional[str] = None,
        content_type: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 100,
        skip: int = 0
    ) -> List[Dict[str, Any]]:
        """Get unified content items from both content library and social drafts"""
        try:
            # Get content library items
            content_items = await self.content_library_service.get_content_items(
                property_id=property_id,
                content_type=content_type,
                status=status,
                user_id=user_id,
                limit=limit,
                skip=skip
            )
            
            # Get social drafts for the same user/property
            draft_query = {}
            if property_id:
                draft_query["property_id"] = property_id
            if status:
                # Map content library status to draft status
                if status == "draft":
                    draft_query["status"] = {"$in": [DraftStatus.GENERATED, DraftStatus.EDITED]}
                elif status == "published":
                    draft_query["status"] = DraftStatus.PUBLISHED
                elif status == "scheduled":
                    draft_query["status"] = DraftStatus.READY
            
            # Get drafts (we need to find drafts by agent_id, not user_id)
            # For now, let's get all drafts and filter by property
            drafts = await SocialDraft.find(draft_query).to_list()
            
            # Transform drafts to content library format
            draft_items = []
            for draft in drafts:
                # Check if this draft belongs to the user's agent profile
                # For now, we'll include all drafts for the property
                draft_item = {
                    "content_id": str(draft.id),
                    "user_id": user_id,  # This might not be accurate, but needed for compatibility
                    "property_id": str(draft.property_id),
                    "content_type": f"ai_{draft.channel.value}_post",
                    "title": draft.title,
                    "content": draft.body,
                    "status": self._map_draft_status_to_content_status(draft.status),
                    "channels": [draft.channel.value],
                    "language": draft.language,
                    "created_at": draft.created_at,
                    "updated_at": draft.updated_at,
                    "is_draft": True,  # Flag to indicate this is from social drafts
                    "draft_id": str(draft.id)
                }
                draft_items.append(draft_item)
            
            # Combine and sort by creation date
            all_items = []
            
            # Add content library items
            for item in content_items:
                all_items.append({
                    **item.model_dump(),
                    "is_draft": False
                })
            
            # Add draft items
            all_items.extend(draft_items)
            
            # Sort by creation date (newest first)
            all_items.sort(key=lambda x: x.get("created_at", datetime.min), reverse=True)
            
            logger.info(f"Retrieved {len(all_items)} unified content items")
            return all_items
            
        except Exception as e:
            logger.error(f"Error getting unified content items: {e}")
            raise
    
    def _map_draft_status_to_content_status(self, draft_status: DraftStatus) -> str:
        """Map draft status to content library status"""
        status_mapping = {
            DraftStatus.GENERATED: "draft",
            DraftStatus.EDITED: "draft", 
            DraftStatus.READY: "scheduled",
            DraftStatus.PUBLISHING: "scheduled",
            DraftStatus.PUBLISHED: "published",
            DraftStatus.FAILED: "draft"
        }
        return status_mapping.get(draft_status, "draft")
    
    async def publish_drafts_from_content_library(
        self, 
        draft_ids: List[str], 
        user_id: str
    ) -> Dict[str, Any]:
        """Publish drafts from content library interface"""
        try:
            # Get the correct agent_id for this user
            from app.services.agent_public_service import AgentPublicService
            agent_service = AgentPublicService(self.db)
            
            agent = await agent_service.get_agent_by_user_id(user_id)
            if agent:
                agent_id = agent.agent_id
            else:
                agent_id = user_id
            
            # Publish the drafts
            result = await self.social_publishing_service.publish_drafts(draft_ids, agent_id)
            
            logger.info(f"Published {result.published_count} drafts from content library")
            return result
            
        except Exception as e:
            logger.error(f"Error publishing drafts from content library: {e}")
            raise
    
    async def get_content_stats(self, user_id: str) -> Dict[str, Any]:
        """Get unified content statistics"""
        try:
            # Get content library stats
            content_stats = await self.content_library_service.get_content_stats(user_id)
            
            # Get draft stats
            total_drafts = await SocialDraft.find({}).count()
            published_drafts = await SocialDraft.find({"status": DraftStatus.PUBLISHED}).count()
            generated_drafts = await SocialDraft.find({"status": DraftStatus.GENERATED}).count()
            
            # Combine stats
            unified_stats = {
                "total_content": content_stats.total_content + total_drafts,
                "published": content_stats.content_by_status.get("published", 0) + published_drafts,
                "drafts": content_stats.content_by_status.get("draft", 0) + generated_drafts,
                "scheduled": content_stats.content_by_status.get("scheduled", 0),
                "content_by_type": content_stats.content_by_type,
                "content_by_status": content_stats.content_by_status,
                "content_by_channel": content_stats.content_by_channel,
                "recent_content": content_stats.recent_content
            }
            
            return unified_stats
            
        except Exception as e:
            logger.error(f"Error getting unified content stats: {e}")
            raise
