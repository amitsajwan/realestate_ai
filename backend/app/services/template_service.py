from typing import List, Optional, Dict, Any
from datetime import datetime
import uuid
from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId

from ..schemas.post_schemas import (
    PostTemplate, TemplateCreateRequest, TemplateUpdateRequest, 
    TemplateResponse, TemplateFilters
)
from ..utils.database import get_database

class TemplateService:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.templates_collection = db.post_templates
        self.posts_collection = db.property_posts

    async def create_template(self, template_data: TemplateCreateRequest, created_by: str) -> TemplateResponse:
        """Create a new post template"""
        try:
            # 1. Validate template data
            if not template_data.name or not template_data.template:
                raise ValueError("Template name and content are required")

            # 2. Create template record
            template_id = str(uuid.uuid4())
            template_doc = PostTemplate(
                id=template_id,
                name=template_data.name,
                description=template_data.description,
                property_type=template_data.property_type,
                language=template_data.language,
                template=template_data.template,
                variables=template_data.variables,
                channels=template_data.channels,
                is_active=True,
                created_by=created_by,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )

            await self.templates_collection.insert_one(template_doc.dict(by_alias=True))

            # 3. Return template response
            return await self._format_template_response(template_doc)

        except Exception as e:
            raise Exception(f"Failed to create template: {str(e)}")

    async def get_templates(self, filters: TemplateFilters) -> List[TemplateResponse]:
        """Get templates with filters"""
        try:
            # 1. Build query from filters
            query = {}
            
            if filters.property_type:
                query["property_type"] = filters.property_type
            if filters.language:
                query["language"] = filters.language
            if filters.is_active is not None:
                query["is_active"] = filters.is_active
            if filters.created_by:
                query["created_by"] = filters.created_by

            # 2. Execute query
            cursor = self.templates_collection.find(query).sort("created_at", -1)
            cursor = cursor.skip(filters.skip).limit(filters.limit)
            
            templates = []
            async for doc in cursor:
                template = PostTemplate(**doc)
                templates.append(await self._format_template_response(template))

            # 3. Return formatted response
            return templates

        except Exception as e:
            raise Exception(f"Failed to get templates: {str(e)}")

    async def get_template(self, template_id: str) -> TemplateResponse:
        """Get a specific template by ID"""
        try:
            doc = await self.templates_collection.find_one({"_id": template_id})
            if not doc:
                raise ValueError(f"Template {template_id} not found")
            
            template = PostTemplate(**doc)
            return await self._format_template_response(template)

        except Exception as e:
            raise Exception(f"Failed to get template: {str(e)}")

    async def update_template(self, template_id: str, updates: TemplateUpdateRequest, user_id: str) -> TemplateResponse:
        """Update an existing template"""
        try:
            # 1. Validate template exists and user has access
            existing_template = await self.templates_collection.find_one({"_id": template_id})
            if not existing_template:
                raise ValueError(f"Template {template_id} not found")

            # Check if user has permission to update (creator or admin)
            if existing_template.get("created_by") != user_id:
                # In a real app, you'd check if user is admin
                raise ValueError("You don't have permission to update this template")

            # 2. Apply updates
            update_data = {k: v for k, v in updates.dict().items() if v is not None}
            update_data["updated_at"] = datetime.utcnow()
            
            if update_data:
                await self.templates_collection.update_one(
                    {"_id": template_id},
                    {"$set": update_data}
                )

            # 3. Return updated template
            updated_doc = await self.templates_collection.find_one({"_id": template_id})
            template = PostTemplate(**updated_doc)
            return await self._format_template_response(template)

        except Exception as e:
            raise Exception(f"Failed to update template: {str(e)}")

    async def delete_template(self, template_id: str, user_id: str) -> bool:
        """Delete a template"""
        try:
            # 1. Validate template exists and user has access
            template = await self.templates_collection.find_one({"_id": template_id})
            if not template:
                raise ValueError(f"Template {template_id} not found")

            # Check if user has permission to delete (creator or admin)
            if template.get("created_by") != user_id:
                # In a real app, you'd check if user is admin
                raise ValueError("You don't have permission to delete this template")

            # 2. Check if template is being used by any posts
            posts_using_template = await self.posts_collection.count_documents({"template_id": template_id})
            if posts_using_template > 0:
                raise ValueError(f"Cannot delete template. It is being used by {posts_using_template} posts")

            # 3. Delete template
            result = await self.templates_collection.delete_one({"_id": template_id})
            return result.deleted_count > 0

        except Exception as e:
            raise Exception(f"Failed to delete template: {str(e)}")

    async def get_available_property_types(self) -> List[str]:
        """Get list of available property types"""
        try:
            pipeline = [
                {"$group": {"_id": "$property_type"}},
                {"$sort": {"_id": 1}}
            ]
            
            cursor = self.templates_collection.aggregate(pipeline)
            property_types = []
            async for doc in cursor:
                property_types.append(doc["_id"])
            
            return property_types

        except Exception as e:
            raise Exception(f"Failed to get property types: {str(e)}")

    async def get_available_languages(self) -> List[str]:
        """Get list of available languages in templates"""
        try:
            pipeline = [
                {"$group": {"_id": "$language"}},
                {"$sort": {"_id": 1}}
            ]
            
            cursor = self.templates_collection.aggregate(pipeline)
            languages = []
            async for doc in cursor:
                languages.append(doc["_id"])
            
            return languages

        except Exception as e:
            raise Exception(f"Failed to get languages: {str(e)}")

    async def duplicate_template(self, template_id: str, new_name: str, user_id: str) -> TemplateResponse:
        """Duplicate an existing template"""
        try:
            # 1. Get original template
            original_template = await self.templates_collection.find_one({"_id": template_id})
            if not original_template:
                raise ValueError(f"Template {template_id} not found")

            # 2. Create duplicate
            duplicate_id = str(uuid.uuid4())
            duplicate_doc = PostTemplate(
                id=duplicate_id,
                name=new_name,
                description=f"Copy of {original_template['name']}",
                property_type=original_template["property_type"],
                language=original_template["language"],
                template=original_template["template"],
                variables=original_template["variables"],
                channels=original_template["channels"],
                is_active=True,
                created_by=user_id,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )

            await self.templates_collection.insert_one(duplicate_doc.dict(by_alias=True))

            # 3. Return duplicate template
            return await self._format_template_response(duplicate_doc)

        except Exception as e:
            raise Exception(f"Failed to duplicate template: {str(e)}")

    async def activate_template(self, template_id: str, user_id: str) -> bool:
        """Activate a template"""
        try:
            # Check if user has permission
            template = await self.templates_collection.find_one({"_id": template_id})
            if not template:
                raise ValueError(f"Template {template_id} not found")

            if template.get("created_by") != user_id:
                raise ValueError("You don't have permission to modify this template")

            # Activate template
            result = await self.templates_collection.update_one(
                {"_id": template_id},
                {
                    "$set": {
                        "is_active": True,
                        "updated_at": datetime.utcnow()
                    }
                }
            )
            return result.modified_count > 0

        except Exception as e:
            raise Exception(f"Failed to activate template: {str(e)}")

    async def deactivate_template(self, template_id: str, user_id: str) -> bool:
        """Deactivate a template"""
        try:
            # Check if user has permission
            template = await self.templates_collection.find_one({"_id": template_id})
            if not template:
                raise ValueError(f"Template {template_id} not found")

            if template.get("created_by") != user_id:
                raise ValueError("You don't have permission to modify this template")

            # Deactivate template
            result = await self.templates_collection.update_one(
                {"_id": template_id},
                {
                    "$set": {
                        "is_active": False,
                        "updated_at": datetime.utcnow()
                    }
                }
            )
            return result.modified_count > 0

        except Exception as e:
            raise Exception(f"Failed to deactivate template: {str(e)}")

    async def get_template_usage_stats(self, template_id: str) -> Dict[str, Any]:
        """Get usage statistics for a template"""
        try:
            # Check if template exists
            template = await self.templates_collection.find_one({"_id": template_id})
            if not template:
                raise ValueError(f"Template {template_id} not found")

            # Get usage statistics
            total_usage = await self.posts_collection.count_documents({"template_id": template_id})
            
            # Get usage by status
            status_pipeline = [
                {"$match": {"template_id": template_id}},
                {"$group": {"_id": "$status", "count": {"$sum": 1}}}
            ]
            
            status_stats = {}
            cursor = self.posts_collection.aggregate(status_pipeline)
            async for doc in cursor:
                status_stats[doc["_id"]] = doc["count"]

            # Get usage by language
            language_pipeline = [
                {"$match": {"template_id": template_id}},
                {"$group": {"_id": "$language", "count": {"$sum": 1}}}
            ]
            
            language_stats = {}
            cursor = self.posts_collection.aggregate(language_pipeline)
            async for doc in cursor:
                language_stats[doc["_id"]] = doc["count"]

            return {
                "template_id": template_id,
                "template_name": template["name"],
                "total_usage": total_usage,
                "status_breakdown": status_stats,
                "language_breakdown": language_stats,
                "last_used": template.get("updated_at")
            }

        except Exception as e:
            raise Exception(f"Failed to get template usage stats: {str(e)}")

    async def search_templates(self, query: str, filters: TemplateFilters) -> List[TemplateResponse]:
        """Search templates by name or description"""
        try:
            # Build search query
            search_query = {
                "$or": [
                    {"name": {"$regex": query, "$options": "i"}},
                    {"description": {"$regex": query, "$options": "i"}},
                    {"template": {"$regex": query, "$options": "i"}}
                ]
            }

            # Add additional filters
            if filters.property_type:
                search_query["property_type"] = filters.property_type
            if filters.language:
                search_query["language"] = filters.language
            if filters.is_active is not None:
                search_query["is_active"] = filters.is_active
            if filters.created_by:
                search_query["created_by"] = filters.created_by

            # Execute search
            cursor = self.templates_collection.find(search_query).sort("created_at", -1)
            cursor = cursor.skip(filters.skip).limit(filters.limit)
            
            templates = []
            async for doc in cursor:
                template = PostTemplate(**doc)
                templates.append(await self._format_template_response(template))

            return templates

        except Exception as e:
            raise Exception(f"Failed to search templates: {str(e)}")

    async def _format_template_response(self, template: PostTemplate) -> TemplateResponse:
        """Format template for API response"""
        return TemplateResponse(
            id=template.id,
            name=template.name,
            description=template.description,
            property_type=template.property_type,
            language=template.language,
            template=template.template,
            variables=template.variables,
            channels=template.channels,
            is_active=template.is_active,
            created_by=template.created_by,
            created_at=template.created_at,
            updated_at=template.updated_at
        )
