#!/usr/bin/env python3
"""
Properties Router
================
Handles property management and CRUD operations
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, List
import logging
import json
from app.database import db
from app.utils import verify_token

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/properties", tags=["properties"])

class Property(BaseModel):
    id: Optional[int] = None  # ✅ Add ID field
    user_id: str
    title: str
    type: Optional[str] = None
    bedrooms: Optional[str] = None
    price: Optional[float] = None
    price_unit: Optional[str] = None
    city: Optional[str] = None
    area: Optional[str] = None
    address: Optional[str] = None
    carpet_area: Optional[float] = None
    built_up_area: Optional[float] = None
    floor: Optional[str] = None
    furnishing: Optional[str] = None
    possession: Optional[str] = None
    amenities: Optional[List[str]] = None
    description: Optional[str] = None

class PropertyResponse(BaseModel):
    success: bool
    property: Optional[Property] = None
    properties: Optional[List[Property]] = None
    message: Optional[str] = None
    property_id: Optional[int] = None

@router.post("/", response_model=PropertyResponse)
async def create_property(property_data: Property):
    """Create a new property"""
    try:
        saved_property = db.save_property(property_data.dict())
        if saved_property:
            logger.info(f"✅ Property created: {saved_property['id']}")
            return PropertyResponse(
                success=True,
                property=Property(**saved_property),
                property_id=saved_property['id'],
                message="Property created successfully"
            )
        else:
            raise HTTPException(status_code=500, detail="Failed to create property")
            
    except Exception as e:
        logger.error(f"❌ Property creation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/user/{user_id}")  # ✅ Remove response_model temporarily
async def get_user_properties(user_id: str):
    """Get all properties for a specific user"""
    try:
        # ✅ Create new database instance directly to test
        from app.database import Database
        test_db = Database()
        properties = test_db.get_user_properties(user_id)
        print(f"🔍 PRINT: Database returned properties: {properties}")  # ✅ Simple print for debugging
        logger.info(f"🔍 Database returned properties: {properties}")
        
        # ✅ Return raw data without Pydantic model to test
        return {
            "success": True,
            "properties": properties,  # Raw database data
            "message": f"Retrieved {len(properties)} properties"
        }
        
    except Exception as e:
        logger.error(f"❌ Get properties error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{property_id}")
async def delete_property(property_id: int):
    """Delete a property (placeholder for future implementation)"""
    try:
        # TODO: Implement property deletion
        return {
            "success": True,
            "message": "Property deletion not yet implemented"
        }
    except Exception as e:
        logger.error(f"❌ Property deletion error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
