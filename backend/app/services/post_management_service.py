from typing import List, Optional, Dict, Any
from datetime import datetime
import uuid
from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId

from ..schemas.post_schemas import (
    PropertyPost, PostCreateRequest, PostUpdateRequest, PostResponse, 
    PostFilters, PostStatus, PostAnalytics
)
from ..services.ai_content_service import AIContentService
from ..utils.database import get_database

class PostManagementService:
    def __init__(self, db: AsyncIOMotorDatabase, ai_service: AIContentService):
        self.db = db
        self.ai_service = ai_service
        self.posts_collection = db.property_posts
        self.properties_collection = db.properties

    async def create_post(self, post_data: PostCreateRequest, agent_id: str) -> PostResponse:
        """Create a new post with AI content generation"""
        try:
            # 1. Validate property exists
            property_obj = await self.properties_collection.find_one({"_id": ObjectId(post_data.property_id)})
            if not property_obj:
                raise ValueError(f"Property {post_data.property_id} not found")

            # 2. Generate AI content if requested
            content = post_data.content
            if post_data.ai_generated and post_data.ai_prompt:
                property_data = {
                    "title": property_obj.get("title", ""),
                    "description": property_obj.get("description", ""),
                    "price": property_obj.get("price", 0),
                    "location": property_obj.get("location", ""),
                    "property_type": property_obj.get("property_type", ""),
                    "features": property_obj.get("features", [])
                }
                content = await self.ai_service.generate_content(
                    property_data, 
                    post_data.ai_prompt, 
                    post_data.language
                )

            # 3. Create post record
            post_id = str(uuid.uuid4())
            post_doc = PropertyPost(
                id=post_id,
                property_id=post_data.property_id,
                agent_id=agent_id,
                title=post_data.title,
                content=content,
                language=post_data.language,
                template_id=post_data.template_id,
                status=PostStatus.DRAFT,
                channels=post_data.channels,
                scheduled_at=post_data.scheduled_at,
                ai_generated=post_data.ai_generated,
                ai_prompt=post_data.ai_prompt,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )

            await self.posts_collection.insert_one(post_doc.dict(by_alias=True))

            # 4. Update property post count
            await self.properties_collection.update_one(
                {"_id": ObjectId(post_data.property_id)},
                {
                    "$inc": {"post_count": 1},
                    "$set": {"last_post_created": datetime.utcnow()}
                }
            )

            # 5. Return post response
            return await self._format_post_response(post_doc)

        except Exception as e:
            raise Exception(f"Failed to create post: {str(e)}")

    async def get_posts(self, filters: PostFilters, agent_id: str) -> List[PostResponse]:
        """Get posts with filters and pagination"""
        try:
            # 1. Build MongoDB query from filters
            query = {"agent_id": agent_id}
            
            if filters.property_id:
                query["property_id"] = filters.property_id
            if filters.status:
                query["status"] = filters.status.value
            if filters.language:
                query["language"] = filters.language
            if filters.channels:
                query["channels"] = {"$in": filters.channels}
            if filters.ai_generated is not None:
                query["ai_generated"] = filters.ai_generated
            if filters.date_from:
                query["created_at"] = {"$gte": filters.date_from}
            if filters.date_to:
                if "created_at" in query:
                    query["created_at"]["$lte"] = filters.date_to
                else:
                    query["created_at"] = {"$lte": filters.date_to}

            # 2. Execute query with pagination
            cursor = self.posts_collection.find(query).sort("created_at", -1)
            cursor = cursor.skip(filters.skip).limit(filters.limit)
            
            posts = []
            async for doc in cursor:
                post = PropertyPost(**doc)
                posts.append(await self._format_post_response(post))

            # 3. Return formatted response
            return posts

        except Exception as e:
            raise Exception(f"Failed to get posts: {str(e)}")

    async def get_post(self, post_id: str, agent_id: str) -> PostResponse:
        """Get a specific post by ID"""
        try:
            doc = await self.posts_collection.find_one({"_id": post_id, "agent_id": agent_id})
            if not doc:
                raise ValueError(f"Post {post_id} not found")
            
            post = PropertyPost(**doc)
            return await self._format_post_response(post)

        except Exception as e:
            raise Exception(f"Failed to get post: {str(e)}")

    async def update_post(self, post_id: str, updates: PostUpdateRequest, agent_id: str) -> PostResponse:
        """Update an existing post"""
        try:
            # 1. Validate post exists and user has access
            existing_post = await self.posts_collection.find_one({"_id": post_id, "agent_id": agent_id})
            if not existing_post:
                raise ValueError(f"Post {post_id} not found")

            # 2. Apply updates
            update_data = {k: v for k, v in updates.dict().items() if v is not None}
            update_data["updated_at"] = datetime.utcnow()
            
            if update_data:
                update_data["version"] = existing_post.get("version", 1) + 1
                await self.posts_collection.update_one(
                    {"_id": post_id},
                    {"$set": update_data}
                )

            # 3. Return updated post
            updated_doc = await self.posts_collection.find_one({"_id": post_id})
            post = PropertyPost(**updated_doc)
            return await self._format_post_response(post)

        except Exception as e:
            raise Exception(f"Failed to update post: {str(e)}")

    async def delete_post(self, post_id: str, agent_id: str) -> bool:
        """Delete a post and update property count"""
        try:
            # 1. Validate post exists
            post = await self.posts_collection.find_one({"_id": post_id, "agent_id": agent_id})
            if not post:
                raise ValueError(f"Post {post_id} not found")

            # 2. Delete post
            result = await self.posts_collection.delete_one({"_id": post_id})
            if result.deleted_count == 0:
                return False

            # 3. Update property post count
            await self.properties_collection.update_one(
                {"_id": ObjectId(post["property_id"])},
                {
                    "$inc": {"post_count": -1},
                    "$set": {"last_post_created": datetime.utcnow()}
                }
            )

            # 4. Return success status
            return True

        except Exception as e:
            raise Exception(f"Failed to delete post: {str(e)}")

    async def get_property_posts(self, property_id: str, agent_id: str) -> List[PostResponse]:
        """Get all posts for a specific property"""
        try:
            cursor = self.posts_collection.find({
                "property_id": property_id,
                "agent_id": agent_id
            }).sort("created_at", -1)
            
            posts = []
            async for doc in cursor:
                post = PropertyPost(**doc)
                posts.append(await self._format_post_response(post))
            
            return posts

        except Exception as e:
            raise Exception(f"Failed to get property posts: {str(e)}")

    async def get_posts_by_status(self, status: PostStatus, agent_id: str) -> List[PostResponse]:
        """Get posts by status"""
        try:
            cursor = self.posts_collection.find({
                "status": status.value,
                "agent_id": agent_id
            }).sort("created_at", -1)
            
            posts = []
            async for doc in cursor:
                post = PropertyPost(**doc)
                posts.append(await self._format_post_response(post))
            
            return posts

        except Exception as e:
            raise Exception(f"Failed to get posts by status: {str(e)}")

    async def _format_post_response(self, post: PropertyPost) -> PostResponse:
        """Format post for API response"""
        return PostResponse(
            id=post.id,
            property_id=post.property_id,
            agent_id=post.agent_id,
            title=post.title,
            content=post.content,
            language=post.language,
            template_id=post.template_id,
            status=post.status,
            channels=post.channels,
            scheduled_at=post.scheduled_at,
            published_at=post.published_at,
            facebook_post_id=post.facebook_post_id,
            instagram_post_id=post.instagram_post_id,
            linkedin_post_id=post.linkedin_post_id,
            website_post_id=post.website_post_id,
            email_campaign_id=post.email_campaign_id,
            ai_generated=post.ai_generated,
            ai_prompt=post.ai_prompt,
            version=post.version,
            created_at=post.created_at,
            updated_at=post.updated_at,
            analytics=post.analytics
        )

    async def get_post_analytics(self, post_id: str, agent_id: str) -> Dict[str, Any]:
        """Get analytics for a specific post"""
        try:
            post = await self.posts_collection.find_one({"_id": post_id, "agent_id": agent_id})
            if not post:
                raise ValueError(f"Post {post_id} not found")
            
            analytics = post.get("analytics", {})
            return {
                "post_id": post_id,
                "total_views": analytics.get("views", 0),
                "total_likes": analytics.get("likes", 0),
                "total_shares": analytics.get("shares", 0),
                "total_comments": analytics.get("comments", 0),
                "total_clicks": analytics.get("clicks", 0),
                "total_conversions": analytics.get("conversions", 0),
                "engagement_rate": analytics.get("engagement_rate", 0.0),
                "reach": analytics.get("reach", 0),
                "impressions": analytics.get("impressions", 0)
            }

        except Exception as e:
            raise Exception(f"Failed to get post analytics: {str(e)}")

    async def update_post_analytics(self, post_id: str, analytics_data: Dict[str, Any]) -> bool:
        """Update analytics for a post"""
        try:
            result = await self.posts_collection.update_one(
                {"_id": post_id},
                {
                    "$set": {
                        "analytics": analytics_data,
                        "updated_at": datetime.utcnow()
                    }
                }
            )
            return result.modified_count > 0

        except Exception as e:
            raise Exception(f"Failed to update post analytics: {str(e)}")
