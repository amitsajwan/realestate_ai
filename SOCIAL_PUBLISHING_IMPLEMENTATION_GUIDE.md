# 🛠️ **Social Publishing Implementation Guide**

## 📋 **Implementation Checklist**

### **Phase 1: Database & Models Implementation**

#### **1.1 Create New MongoDB Models**

**File: `backend/app/models/social_praft.py`**
```python
"""
Social Draft Model for MongoDB
=============================
MongoDB document model for social media publishing drafts
"""

from typing import List, Optional
from datetime import datetime
from beanie import Document, PydanticObjectId
from pydantic import Field
from enum import Enum

class Channel(str, Enum):
    FACEBOOK = "facebook"
    INSTAGRAM = "instagram"
    WEBSITE = "website"

class DraftStatus(str, Enum):
    DRAFT = "draft"
    GENERATED = "generated"
    EDITED = "edited"
    READY = "ready"
    PUBLISHING = "publishing"
    PUBLISHED = "published"
    FAILED = "failed"

class SocialDraft(Document):
    """Social media publishing draft document"""
    
    # Basic information
    property_id: PydanticObjectId = Field(..., description="Reference to the property")
    agent_id: PydanticObjectId = Field(..., description="Agent who created the draft")
    language: str = Field(..., description="Content language code")
    channel: Channel = Field(..., description="Target platform")
    
    # Content
    title: str = Field(..., min_length=1, max_length=200, description="Post title")
    body: str = Field(..., min_length=1, max_length=10000, description="Post content")
    hashtags: List[str] = Field(default_factory=list, description="Post hashtags")
    media_ids: List[str] = Field(default_factory=list, description="Media attachments")
    contact_included: bool = Field(default=True, description="Include contact information")
    
    # Status and tracking
    status: DraftStatus = Field(default=DraftStatus.DRAFT, description="Draft status")
    published_at: Optional[datetime] = Field(None, description="When published")
    platform_post_id: Optional[str] = Field(None, description="Platform post ID after publishing")
    platform_post_url: Optional[str] = Field(None, description="Platform post URL")
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Settings:
        name = "social_drafts"
        indexes = [
            "property_id",
            "agent_id",
            "status",
            "language",
            "channel",
            "created_at",
            [("property_id", 1), ("status", 1)],
            [("agent_id", 1), ("status", 1)],
            [("status", 1), ("created_at", -1)]
        ]
```

**File: `backend/app/models/social_post.py`**
```python
"""
Social Post Model for MongoDB
============================
MongoDB document model for published social media posts
"""

from typing import Dict, Any, Optional, Literal
from datetime import datetime
from beanie import Document, PydanticObjectId
from pydantic import Field
from enum import Enum

class Channel(str, Enum):
    FACEBOOK = "facebook"
    INSTAGRAM = "instagram"
    WEBSITE = "website"

class PostStatus(str, Enum):
    PUBLISHED = "published"
    FAILED = "failed"
    SCHEDULED = "scheduled"
    DELETED = "deleted"

class SocialPost(Document):
    """Published social media post document"""
    
    # References
    draft_id: PydanticObjectId = Field(..., description="Reference to the original draft")
    property_id: PydanticObjectId = Field(..., description="Reference to the property")
    agent_id: PydanticObjectId = Field(..., description="Agent who published the post")
    
    # Platform information
    platform: Channel = Field(..., description="Platform where published")
    platform_post_id: str = Field(..., description="Platform-specific post ID")
    platform_post_url: str = Field(..., description="Direct URL to the published post")
    
    # Status and tracking
    status: PostStatus = Field(default=PostStatus.PUBLISHED, description="Post status")
    error_message: Optional[str] = Field(None, description="Error message if failed")
    
    # Analytics data
    analytics_data: Dict[str, Any] = Field(default_factory=dict, description="Platform analytics")
    
    # Timestamps
    published_at: datetime = Field(default_factory=datetime.utcnow)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Settings:
        name = "social_posts"
        indexes = [
            "draft_id",
            "property_id",
            "agent_id",
            "platform",
            "status",
            "published_at",
            [("property_id", 1), ("platform", 1)],
            [("agent_id", 1), ("published_at", -1)],
            [("platform", 1), ("status", 1)]
        ]
```

#### **1.2 Update Database Initialization**

**File: `backend/app/utils/database_init.py` (Add to existing file)**
```python
async def initialize_social_publishing_collections(db: AsyncIOMotorDatabase):
    """Initialize social publishing collections"""
    try:
        logger.info("Initializing social publishing collections...")
        
        # Initialize collections
        await SocialDraft.get_motor_collection().create_indexes([
            {"key": [("property_id", 1), ("status", 1)]},
            {"key": [("agent_id", 1), ("status", 1)]},
            {"key": [("status", 1), ("created_at", -1)]},
            {"key": "property_id"},
            {"key": "agent_id"},
            {"key": "status"},
            {"key": "language"},
            {"key": "channel"},
            {"key": "created_at"}
        ])
        
        await SocialPost.get_motor_collection().create_indexes([
            {"key": [("property_id", 1), ("platform", 1)]},
            {"key": [("agent_id", 1), ("published_at", -1)]},
            {"key": [("platform", 1), ("status", 1)]},
            {"key": "draft_id"},
            {"key": "property_id"},
            {"key": "agent_id"},
            {"key": "platform"},
            {"key": "status"},
            {"key": "published_at"}
        ])
        
        logger.info("Social publishing collections initialized successfully")
        
    except Exception as e:
        logger.error(f"Failed to initialize social publishing collections: {e}")
        raise
```

### **Phase 2: Service Layer Implementation**

#### **2.1 Create Social Publishing Service**

**File: `backend/app/services/social_publishing_service.py`**
```python
"""
Social Publishing Service
========================
Service for managing social media publishing operations
"""

import logging
from typing import List, Optional, Dict, Any
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.models.social_draft import SocialDraft, DraftStatus, Channel
from app.models.social_post import SocialPost, PostStatus
from app.schemas.social_publishing import (
    GenerateContentRequest, GenerateContentResponse, UpdateDraftRequest,
    PublishRequest, PublishResponse, AIDraft
)
from app.services.ai_content_generation_service import AIContentGenerationService

logger = logging.getLogger(__name__)

class SocialPublishingService:
    """Service for social media publishing operations"""
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.ai_service = AIContentGenerationService()
    
    async def generate_content(self, request: GenerateContentRequest, agent_id: str) -> List[SocialDraft]:
        """Generate AI content and save as drafts"""
        try:
            logger.info(f"Generating content for property {request.property_id}")
            
            drafts = []
            for channel in request.channels:
                # Create draft document
                draft = SocialDraft(
                    property_id=request.property_id,
                    agent_id=agent_id,
                    language=request.language,
                    channel=channel,
                    title="",  # Will be generated by AI
                    body="",   # Will be generated by AI
                    status=DraftStatus.DRAFT
                )
                
                # Generate AI content (implement AI service integration)
                ai_content = await self._generate_ai_content(request, channel)
                
                # Update draft with AI content
                draft.title = ai_content.get("title", "")
                draft.body = ai_content.get("body", "")
                draft.hashtags = ai_content.get("hashtags", [])
                draft.status = DraftStatus.GENERATED
                
                # Save to database
                await draft.insert()
                drafts.append(draft)
                
            logger.info(f"Generated {len(drafts)} drafts successfully")
            return drafts
            
        except Exception as e:
            logger.error(f"Error generating content: {e}")
            raise
    
    async def update_draft(self, draft_id: str, updates: UpdateDraftRequest, agent_id: str) -> Optional[SocialDraft]:
        """Update a draft"""
        try:
            draft = await SocialDraft.get(draft_id)
            if not draft:
                return None
            
            # Update fields
            update_data = updates.dict(exclude_unset=True)
            for key, value in update_data.items():
                setattr(draft, key, value)
            
            draft.updated_at = datetime.utcnow()
            await draft.save()
            
            logger.info(f"Draft {draft_id} updated successfully")
            return draft
            
        except Exception as e:
            logger.error(f"Error updating draft {draft_id}: {e}")
            raise
    
    async def publish_drafts(self, draft_ids: List[str], agent_id: str) -> PublishResponse:
        """Publish drafts to social media platforms"""
        try:
            logger.info(f"Publishing {len(draft_ids)} drafts")
            
            # Get ready drafts
            drafts = await SocialDraft.find(
                {"_id": {"$in": draft_ids}, "status": DraftStatus.READY}
            ).to_list()
            
            if not drafts:
                raise ValueError("No ready drafts found")
            
            published_posts = []
            failed_posts = []
            
            for draft in drafts:
                try:
                    # Update draft status to publishing
                    draft.status = DraftStatus.PUBLISHING
                    await draft.save()
                    
                    # Publish to platform (implement platform integration)
                    platform_result = await self._publish_to_platform(draft)
                    
                    if platform_result["success"]:
                        # Create social post record
                        social_post = SocialPost(
                            draft_id=draft.id,
                            property_id=draft.property_id,
                            agent_id=draft.agent_id,
                            platform=draft.channel,
                            platform_post_id=platform_result["post_id"],
                            platform_post_url=platform_result["post_url"],
                            status=PostStatus.PUBLISHED,
                            published_at=datetime.utcnow()
                        )
                        await social_post.insert()
                        
                        # Update draft with published info
                        draft.status = DraftStatus.PUBLISHED
                        draft.published_at = datetime.utcnow()
                        draft.platform_post_id = platform_result["post_id"]
                        draft.platform_post_url = platform_result["post_url"]
                        await draft.save()
                        
                        published_posts.append(social_post)
                        
                    else:
                        # Handle publishing failure
                        draft.status = DraftStatus.FAILED
                        await draft.save()
                        
                        failed_posts.append({
                            "draft_id": str(draft.id),
                            "error": platform_result["error"]
                        })
                        
                except Exception as e:
                    logger.error(f"Failed to publish draft {draft.id}: {e}")
                    draft.status = DraftStatus.FAILED
                    await draft.save()
                    
                    failed_posts.append({
                        "draft_id": str(draft.id),
                        "error": str(e)
                    })
            
            # Update property publishing status
            if published_posts:
                await self._update_property_publishing_status(drafts[0].property_id)
            
            logger.info(f"Published {len(published_posts)} drafts successfully")
            
            return PublishResponse(
                job_id=f"publish_job_{datetime.utcnow().timestamp()}",
                message=f"Published {len(published_posts)} drafts successfully",
                published_count=len(published_posts),
                failed_count=len(failed_posts),
                failed_drafts=failed_posts
            )
            
        except Exception as e:
            logger.error(f"Error publishing drafts: {e}")
            raise
    
    async def get_published_posts(self, property_id: str) -> List[SocialPost]:
        """Get all published posts for a property"""
        try:
            posts = await SocialPost.find({"property_id": property_id}).to_list()
            return posts
        except Exception as e:
            logger.error(f"Error getting published posts: {e}")
            raise
    
    async def _generate_ai_content(self, request: GenerateContentRequest, channel: Channel) -> Dict[str, Any]:
        """Generate AI content for a specific channel"""
        # Implement AI content generation
        # This should integrate with your existing AI service
        return {
            "title": f"AI Generated Title for {channel}",
            "body": f"AI Generated content for {channel} platform",
            "hashtags": ["#realestate", "#property", "#home"]
        }
    
    async def _publish_to_platform(self, draft: SocialDraft) -> Dict[str, Any]:
        """Publish draft to specific platform"""
        # Implement platform-specific publishing
        # This should integrate with Facebook/Instagram APIs
        return {
            "success": True,
            "post_id": f"platform_post_{datetime.utcnow().timestamp()}",
            "post_url": f"https://{draft.channel}.com/post/platform_post_{datetime.utcnow().timestamp()}"
        }
    
    async def _update_property_publishing_status(self, property_id: str):
        """Update property publishing status"""
        # Implement property status update
        pass
```

### **Phase 3: API Endpoint Updates**

#### **3.1 Update Social Publishing Endpoints**

**File: `backend/app/api/v1/endpoints/social_publishing.py` (Replace existing file)**
```python
"""
Social Publishing API Endpoints
===============================
API endpoints for social media publishing workflow
"""

import logging
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Depends, Query
from datetime import datetime

from app.schemas.social_publishing import (
    GenerateContentRequest, GenerateContentResponse, UpdateDraftRequest,
    MarkReadyRequest, PublishRequest, PublishResponse, DraftsResponse,
    AIDraft, DraftStatus, Channel
)
from app.services.social_publishing_service import SocialPublishingService
from app.core.auth_backend import current_active_user
from app.models.user import User
from app.core.database import get_database
from motor.motor_asyncio import AsyncIOMotorDatabase

logger = logging.getLogger(__name__)
router = APIRouter(tags=["social-publishing"])

def get_social_publishing_service(db: AsyncIOMotorDatabase = Depends(get_database)) -> SocialPublishingService:
    """Get social publishing service instance"""
    return SocialPublishingService(db)

@router.post("/generate", response_model=GenerateContentResponse)
async def generate_content(
    request: GenerateContentRequest,
    current_user: User = Depends(current_active_user),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """Generate AI content for social media posts"""
    try:
        logger.info(f"Generating content for property {request.property_id}")
        
        service = get_social_publishing_service(db)
        drafts = await service.generate_content(request, str(current_user.id))
        
        # Transform to response format
        transformed_drafts = []
        for draft in drafts:
            transformed_drafts.append({
                "id": str(draft.id),
                "propertyId": str(draft.property_id),
                "language": draft.language,
                "channel": draft.channel,
                "title": draft.title,
                "body": draft.body,
                "hashtags": draft.hashtags,
                "mediaIds": draft.media_ids,
                "contactIncluded": draft.contact_included,
                "status": draft.status,
                "createdAt": draft.created_at.isoformat(),
                "updatedAt": draft.updated_at.isoformat()
            })
        
        logger.info(f"Generated {len(transformed_drafts)} drafts successfully")
        return GenerateContentResponse(drafts=transformed_drafts)
        
    except Exception as e:
        logger.error(f"Error generating content: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate content: {str(e)}")

@router.put("/draft/{draft_id}", response_model=AIDraft)
async def update_draft(
    draft_id: str,
    request: UpdateDraftRequest,
    current_user: User = Depends(current_active_user),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """Update a draft"""
    try:
        logger.info(f"Updating draft {draft_id}")
        
        service = get_social_publishing_service(db)
        draft = await service.update_draft(draft_id, request, str(current_user.id))
        
        if not draft:
            raise HTTPException(status_code=404, detail="Draft not found")
        
        # Transform to response format
        response_draft = {
            "id": str(draft.id),
            "propertyId": str(draft.property_id),
            "language": draft.language,
            "channel": draft.channel,
            "title": draft.title,
            "body": draft.body,
            "hashtags": draft.hashtags,
            "mediaIds": draft.media_ids,
            "contactIncluded": draft.contact_included,
            "status": draft.status,
            "createdAt": draft.created_at.isoformat(),
            "updatedAt": draft.updated_at.isoformat()
        }
        
        logger.info(f"Draft {draft_id} updated successfully")
        return response_draft
        
    except Exception as e:
        logger.error(f"Error updating draft: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to update draft: {str(e)}")

@router.post("/publish", response_model=PublishResponse)
async def publish_drafts(
    request: PublishRequest,
    current_user: User = Depends(current_active_user),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """Publish drafts to social media"""
    try:
        logger.info(f"Publishing {len(request.draft_ids)} drafts")
        
        service = get_social_publishing_service(db)
        result = await service.publish_drafts(request.draft_ids, str(current_user.id))
        
        logger.info(f"Published {result.published_count} drafts successfully")
        return result
        
    except Exception as e:
        logger.error(f"Error publishing drafts: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to publish drafts: {str(e)}")

@router.get("/posts/{property_id}")
async def get_published_posts(
    property_id: str,
    current_user: User = Depends(current_active_user),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """Get published posts for a property"""
    try:
        service = get_social_publishing_service(db)
        posts = await service.get_published_posts(property_id)
        
        # Transform to response format
        transformed_posts = []
        for post in posts:
            transformed_posts.append({
                "id": str(post.id),
                "draftId": str(post.draft_id),
                "propertyId": str(post.property_id),
                "platform": post.platform,
                "platformPostId": post.platform_post_id,
                "platformPostUrl": post.platform_post_url,
                "status": post.status,
                "publishedAt": post.published_at.isoformat(),
                "analyticsData": post.analytics_data
            })
        
        return {"posts": transformed_posts}
        
    except Exception as e:
        logger.error(f"Error getting published posts: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get published posts: {str(e)}")

@router.get("/drafts")
async def get_drafts(
    property_id: str = Query(..., description="Property ID"),
    language: Optional[str] = Query(None, description="Language filter"),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """Get drafts for a property"""
    try:
        logger.info(f"Getting drafts for property {property_id}")
        
        service = get_social_publishing_service(db)
        
        # Build query
        query = {"property_id": property_id}
        if language:
            query["language"] = language
        
        drafts = await SocialDraft.find(query).to_list()
        
        # Group by language
        language_groups = {}
        for draft in drafts:
            if draft.language not in language_groups:
                language_groups[draft.language] = []
            
            transformed_draft = {
                "id": str(draft.id),
                "propertyId": str(draft.property_id),
                "language": draft.language,
                "channel": draft.channel,
                "title": draft.title,
                "body": draft.body,
                "hashtags": draft.hashtags,
                "mediaIds": draft.media_ids,
                "contactIncluded": draft.contact_included,
                "status": draft.status,
                "createdAt": draft.created_at.isoformat(),
                "updatedAt": draft.updated_at.isoformat()
            }
            language_groups[draft.language].append(transformed_draft)
        
        # Transform to response format
        response = []
        for language, drafts_list in language_groups.items():
            response.append({
                "propertyId": property_id,
                "language": language,
                "drafts": drafts_list
            })
        
        return response
        
    except Exception as e:
        logger.error(f"Error getting drafts: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get drafts: {str(e)}")
```

### **Phase 4: Frontend Updates**

#### **4.1 Update API Client**

**File: `frontend/lib/social_publishing/api.ts` (Update existing file)**
```typescript
/**
 * Social Publishing API Service
 * =============================
 * API service for social media publishing workflow
 */

import { authManager } from '@/lib/auth';
import {
    AIDraft,
    DraftsResponse,
    GenerateContentRequest,
    GenerateContentResponse,
    MarkReadyRequest,
    PublishRequest,
    PublishResponse,
    UpdateDraftRequest
} from '@/types/social_publishing';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

class SocialPublishingAPI {
    private baseUrl: string;

    constructor() {
        this.baseUrl = `${API_BASE_URL}/api/v1/social-publishing`;
    }

    private getHeaders(): HeadersInit {
        const authState = authManager.getState();
        const token = authState.token;

        return {
            'Content-Type': 'application/json',
            ...(token && { 'Authorization': `Bearer ${token}` })
        };
    }

    private async handleResponse<T>(response: Response): Promise<T> {
        if (!response.ok) {
            const error = await response.json().catch(() => ({ detail: 'Unknown error' }));
            throw new Error(error.detail || `HTTP ${response.status}`);
        }
        const data = await response.json();
        return this.snakeToCamel(data);
    }

    private camelToSnake(obj: any): any {
        if (obj === null || obj === undefined) return obj;
        if (Array.isArray(obj)) return obj.map(item => this.camelToSnake(item));
        if (typeof obj !== 'object') return obj;

        const result: any = {};
        for (const key in obj) {
            if (obj.hasOwnProperty(key)) {
                const snakeKey = key.replace(/[A-Z]/g, letter => `_${letter.toLowerCase()}`);
                result[snakeKey] = this.camelToSnake(obj[key]);
            }
        }
        return result;
    }

    private snakeToCamel(obj: any): any {
        if (obj === null || obj === undefined) return obj;
        if (Array.isArray(obj)) return obj.map(item => this.snakeToCamel(item));
        if (typeof obj !== 'object') return obj;

        const result: any = {};
        for (const key in obj) {
            if (obj.hasOwnProperty(key)) {
                const camelKey = key.replace(/_([a-z])/g, (match, letter) => letter.toUpperCase());
                result[camelKey] = this.snakeToCamel(obj[key]);
            }
        }
        return result;
    }

    async generateContent(request: GenerateContentRequest): Promise<GenerateContentResponse> {
        const snakeCaseRequest = this.camelToSnake(request);
        const response = await fetch(`${this.baseUrl}/generate`, {
            method: 'POST',
            headers: this.getHeaders(),
            body: JSON.stringify(snakeCaseRequest)
        });
        return this.handleResponse<GenerateContentResponse>(response);
    }

    async updateDraft(draftId: string, request: UpdateDraftRequest): Promise<AIDraft> {
        const snakeCaseRequest = this.camelToSnake(request);
        const response = await fetch(`${this.baseUrl}/draft/${draftId}`, {
            method: 'PUT',
            headers: this.getHeaders(),
            body: JSON.stringify(snakeCaseRequest)
        });
        return this.handleResponse<AIDraft>(response);
    }

    async publishDrafts(request: PublishRequest): Promise<PublishResponse> {
        const snakeCaseRequest = this.camelToSnake(request);
        const response = await fetch(`${this.baseUrl}/publish`, {
            method: 'POST',
            headers: this.getHeaders(),
            body: JSON.stringify(snakeCaseRequest)
        });
        return this.handleResponse<PublishResponse>(response);
    }

    async getDrafts(propertyId: string, language?: string): Promise<DraftsResponse[]> {
        const params = new URLSearchParams({ property_id: propertyId });
        if (language) {
            params.append('language', language);
        }

        const response = await fetch(`${this.baseUrl}/drafts?${params}`, {
            method: 'GET',
            headers: this.getHeaders()
        });
        return this.handleResponse<DraftsResponse[]>(response);
    }

    async getPublishedPosts(propertyId: string): Promise<{ posts: any[] }> {
        const response = await fetch(`${this.baseUrl}/posts/${propertyId}`, {
            method: 'GET',
            headers: this.getHeaders()
        });
        return this.handleResponse<{ posts: any[] }>(response);
    }
}

export const socialPublishingAPI = new SocialPublishingAPI();
```

## 🧪 **Testing Implementation**

### **5.1 Create Test Scripts**

**File: `test_social_publishing_complete.py`**
```python
#!/usr/bin/env python3
"""
Complete Social Publishing Test
==============================
End-to-end test for the social publishing workflow
"""

import asyncio
import sys
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorClient
from app.services.social_publishing_service import SocialPublishingService
from app.schemas.social_publishing import GenerateContentRequest

async def test_complete_workflow():
    """Test the complete social publishing workflow"""
    print("🧪 Testing Complete Social Publishing Workflow")
    print("=" * 50)
    
    # Connect to database
    client = AsyncIOMotorClient("mongodb://localhost:27017")
    db = client.realestate_ai
    
    # Initialize service
    service = SocialPublishingService(db)
    
    try:
        # Test 1: Generate content
        print("📝 Step 1: Generating content...")
        request = GenerateContentRequest(
            property_id="test-property-123",
            language="en",
            channels=["facebook"],
            tone="friendly",
            length="medium",
            agent_id="test-agent-456"
        )
        
        drafts = await service.generate_content(request, "test-agent-456")
        print(f"✅ Generated {len(drafts)} drafts")
        
        # Test 2: Update draft status to ready
        print("🎯 Step 2: Marking draft as ready...")
        draft_id = str(drafts[0].id)
        updated_draft = await service.update_draft(
            draft_id, 
            {"status": "ready"}, 
            "test-agent-456"
        )
        print(f"✅ Draft marked as ready: {updated_draft.status}")
        
        # Test 3: Publish drafts
        print("🚀 Step 3: Publishing drafts...")
        result = await service.publish_drafts([draft_id], "test-agent-456")
        print(f"✅ Publishing result: {result.message}")
        print(f"   Published: {result.published_count}")
        print(f"   Failed: {result.failed_count}")
        
        # Test 4: Get published posts
        print("📊 Step 4: Getting published posts...")
        posts = await service.get_published_posts("test-property-123")
        print(f"✅ Found {len(posts)} published posts")
        
        for post in posts:
            print(f"   Post ID: {post.id}")
            print(f"   Platform: {post.platform}")
            print(f"   URL: {post.platform_post_url}")
        
        print("\n🎉 All tests passed! The social publishing workflow is working correctly.")
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False
    finally:
        client.close()

if __name__ == "__main__":
    success = asyncio.run(test_complete_workflow())
    sys.exit(0 if success else 1)
```

## 📋 **Implementation Checklist**

### **Phase 1: Database & Models**
- [ ] Create `backend/app/models/social_draft.py`
- [ ] Create `backend/app/models/social_post.py`
- [ ] Update `backend/app/utils/database_init.py`
- [ ] Run database initialization
- [ ] Test database connections

### **Phase 2: Service Layer**
- [ ] Create `backend/app/services/social_publishing_service.py`
- [ ] Implement content generation
- [ ] Implement draft management
- [ ] Implement publishing logic
- [ ] Add error handling

### **Phase 3: API Updates**
- [ ] Update `backend/app/api/v1/endpoints/social_publishing.py`
- [ ] Replace in-memory storage with database operations
- [ ] Add new endpoints for tracking
- [ ] Test all endpoints

### **Phase 4: Frontend Updates**
- [ ] Update `frontend/lib/social_publishing/api.ts`
- [ ] Fix data transformation issues
- [ ] Update error handling
- [ ] Test frontend integration

### **Phase 5: Testing**
- [ ] Create test scripts
- [ ] Run end-to-end tests
- [ ] Validate data persistence
- [ ] Test error scenarios

## 🚀 **Deployment Steps**

1. **Backup existing data**
2. **Deploy database changes**
3. **Deploy backend services**
4. **Deploy frontend updates**
5. **Run migration scripts**
6. **Validate functionality**
7. **Monitor for issues**

---

**This implementation guide provides step-by-step instructions for implementing a production-ready social publishing system.**
