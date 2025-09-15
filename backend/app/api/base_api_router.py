"""
Base API Router for Consistent Endpoint Patterns
===============================================
This class provides standardized CRUD endpoints and patterns to eliminate
code duplication across all API routers.
"""

from typing import Dict, List, Optional, Any, Type
from fastapi import APIRouter, HTTPException, Depends, Query, Path
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import logging
from app.services.base_service import BaseService
from app.core.auth_backend import current_active_user
from app.models.user import User

logger = logging.getLogger(__name__)


class BaseAPIRouter:
    """
    Base API router providing common CRUD endpoints
    and patterns for all API routers.
    """
    
    def __init__(self, 
                 prefix: str, 
                 service: BaseService,
                 create_schema: Type[BaseModel],
                 update_schema: Type[BaseModel],
                 response_schema: Type[BaseModel],
                 tags: List[str] = None):
        """
        Initialize the base API router.
        
        Args:
            prefix (str): API route prefix
            service (BaseService): Service instance
            create_schema (Type[BaseModel]): Pydantic model for creation
            update_schema (Type[BaseModel]): Pydantic model for updates
            response_schema (Type[BaseModel]): Pydantic model for responses
            tags (List[str]): OpenAPI tags
        """
        self.prefix = prefix
        self.service = service
        self.create_schema = create_schema
        self.update_schema = update_schema
        self.response_schema = response_schema
        self.tags = tags or [prefix.strip('/')]
        
        # Create router
        self.router = APIRouter(prefix=prefix, tags=self.tags)
        
        # Setup routes
        self._setup_routes()
        
        logger.info(f"Initialized BaseAPIRouter for {prefix}")
    
    def _setup_routes(self):
        """Setup common CRUD routes."""
        
        @self.router.post("/", response_model=self.response_schema, status_code=201)
        async def create_item(
            item_data: self.create_schema,
            current_user: User = Depends(current_active_user)
        ):
            """Create a new item."""
            try:
                # Convert Pydantic model to dict
                data = item_data.dict()
                
                # Add user context if needed
                data["created_by"] = str(current_user.id)
                
                # Create item
                result = await self.service.create(data)
                
                logger.info(f"Created item in {self.service.collection_name}: {result.get('_id')}")
                return JSONResponse(
                    status_code=201,
                    content={
                        "success": True,
                        "message": f"Item created successfully",
                        "data": result
                    }
                )
                
            except Exception as e:
                logger.error(f"Failed to create item in {self.service.collection_name}: {e}")
                raise HTTPException(
                    status_code=500,
                    detail=f"Failed to create item: {str(e)}"
                )
        
        @self.router.get("/{item_id}", response_model=self.response_schema)
        async def get_item(
            item_id: str = Path(..., description="Item ID"),
            current_user: User = Depends(current_active_user)
        ):
            """Get an item by ID."""
            try:
                result = await self.service.get_by_id(item_id)
                
                if not result:
                    raise HTTPException(
                        status_code=404,
                        detail=f"Item not found with ID: {item_id}"
                    )
                
                logger.debug(f"Retrieved item from {self.service.collection_name}: {item_id}")
                return JSONResponse(
                    status_code=200,
                    content={
                        "success": True,
                        "message": "Item retrieved successfully",
                        "data": result
                    }
                )
                
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"Failed to get item from {self.service.collection_name}: {e}")
                raise HTTPException(
                    status_code=500,
                    detail=f"Failed to get item: {str(e)}"
                )
        
        @self.router.get("/", response_model=List[self.response_schema])
        async def get_items(
            limit: int = Query(100, ge=1, le=1000, description="Number of items to return"),
            skip: int = Query(0, ge=0, description="Number of items to skip"),
            sort_field: str = Query("created_at", description="Field to sort by"),
            sort_direction: int = Query(-1, description="Sort direction (1 for ascending, -1 for descending)"),
            search: Optional[str] = Query(None, description="Search term"),
            current_user: User = Depends(current_active_user)
        ):
            """Get all items with optional filtering and pagination."""
            try:
                if search:
                    # Use search functionality
                    search_fields = ["title", "description", "name"]  # Common search fields
                    results = await self.service.search(search, search_fields, limit, skip)
                else:
                    # Use regular get_all
                    results = await self.service.get_all(
                        limit=limit,
                        skip=skip,
                        sort_field=sort_field,
                        sort_direction=sort_direction
                    )
                
                logger.debug(f"Retrieved {len(results)} items from {self.service.collection_name}")
                return JSONResponse(
                    status_code=200,
                    content={
                        "success": True,
                        "message": f"Retrieved {len(results)} items successfully",
                        "data": results,
                        "pagination": {
                            "limit": limit,
                            "skip": skip,
                            "total": len(results)
                        }
                    }
                )
                
            except Exception as e:
                logger.error(f"Failed to get items from {self.service.collection_name}: {e}")
                raise HTTPException(
                    status_code=500,
                    detail=f"Failed to get items: {str(e)}"
                )
        
        @self.router.put("/{item_id}", response_model=self.response_schema)
        async def update_item(
            item_id: str = Path(..., description="Item ID"),
            item_data: self.update_schema = None,
            current_user: User = Depends(current_active_user)
        ):
            """Update an item by ID."""
            try:
                # Convert Pydantic model to dict
                data = item_data.dict() if item_data else {}
                
                # Add user context if needed
                data["updated_by"] = str(current_user.id)
                
                # Update item
                result = await self.service.update(item_id, data)
                
                if not result:
                    raise HTTPException(
                        status_code=404,
                        detail=f"Item not found with ID: {item_id}"
                    )
                
                logger.info(f"Updated item in {self.service.collection_name}: {item_id}")
                return JSONResponse(
                    status_code=200,
                    content={
                        "success": True,
                        "message": "Item updated successfully",
                        "data": result
                    }
                )
                
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"Failed to update item in {self.service.collection_name}: {e}")
                raise HTTPException(
                    status_code=500,
                    detail=f"Failed to update item: {str(e)}"
                )
        
        @self.router.delete("/{item_id}")
        async def delete_item(
            item_id: str = Path(..., description="Item ID"),
            current_user: User = Depends(current_active_user)
        ):
            """Delete an item by ID."""
            try:
                result = await self.service.delete(item_id)
                
                if not result:
                    raise HTTPException(
                        status_code=404,
                        detail=f"Item not found with ID: {item_id}"
                    )
                
                logger.info(f"Deleted item from {self.service.collection_name}: {item_id}")
                return JSONResponse(
                    status_code=200,
                    content={
                        "success": True,
                        "message": "Item deleted successfully"
                    }
                )
                
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"Failed to delete item from {self.service.collection_name}: {e}")
                raise HTTPException(
                    status_code=500,
                    detail=f"Failed to delete item: {str(e)}"
                )
        
        @self.router.get("/count/total")
        async def get_total_count(
            current_user: User = Depends(current_active_user)
        ):
            """Get total count of items."""
            try:
                count = await self.service.count()
                
                logger.debug(f"Total count for {self.service.collection_name}: {count}")
                return JSONResponse(
                    status_code=200,
                    content={
                        "success": True,
                        "message": "Count retrieved successfully",
                        "data": {"count": count}
                    }
                )
                
            except Exception as e:
                logger.error(f"Failed to get count for {self.service.collection_name}: {e}")
                raise HTTPException(
                    status_code=500,
                    detail=f"Failed to get count: {str(e)}"
                )
        
        @self.router.get("/exists/{item_id}")
        async def check_item_exists(
            item_id: str = Path(..., description="Item ID"),
            current_user: User = Depends(current_active_user)
        ):
            """Check if an item exists by ID."""
            try:
                exists = await self.service.exists(item_id)
                
                logger.debug(f"Item exists check for {self.service.collection_name}: {item_id} = {exists}")
                return JSONResponse(
                    status_code=200,
                    content={
                        "success": True,
                        "message": "Existence check completed",
                        "data": {"exists": exists}
                    }
                )
                
            except Exception as e:
                logger.error(f"Failed to check item existence in {self.service.collection_name}: {e}")
                raise HTTPException(
                    status_code=500,
                    detail=f"Failed to check item existence: {str(e)}"
                )
    
    def add_custom_route(self, method: str, path: str, handler, **kwargs):
        """
        Add a custom route to the router.
        
        Args:
            method (str): HTTP method (GET, POST, PUT, DELETE, etc.)
            path (str): Route path
            handler: Route handler function
            **kwargs: Additional route parameters
        """
        try:
            if method.upper() == "GET":
                self.router.get(path, **kwargs)(handler)
            elif method.upper() == "POST":
                self.router.post(path, **kwargs)(handler)
            elif method.upper() == "PUT":
                self.router.put(path, **kwargs)(handler)
            elif method.upper() == "DELETE":
                self.router.delete(path, **kwargs)(handler)
            elif method.upper() == "PATCH":
                self.router.patch(path, **kwargs)(handler)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            
            logger.info(f"Added custom route: {method.upper()} {path}")
            
        except Exception as e:
            logger.error(f"Failed to add custom route {method.upper()} {path}: {e}")
            raise
    
    def get_router(self) -> APIRouter:
        """Get the FastAPI router instance."""
        return self.router