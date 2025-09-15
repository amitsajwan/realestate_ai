from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional

from ....schemas.post_schemas import (
    TemplateCreateRequest, TemplateUpdateRequest, TemplateResponse, 
    TemplateFilters
)
from ....services.template_service import TemplateService
from ....utils.database import get_database
from ....auth.dependencies import get_current_user
from ....models.user import User

router = APIRouter()

def get_template_service() -> TemplateService:
    """Get template service instance"""
    db = get_database()
    return TemplateService(db)

@router.post("/", response_model=TemplateResponse)
async def create_template(
    template_data: TemplateCreateRequest,
    current_user: User = Depends(get_current_user)
):
    """Create a new post template"""
    try:
        service = get_template_service()
        template = await service.create_template(template_data, current_user.id)
        return template
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/", response_model=List[TemplateResponse])
async def get_templates(
    property_type: Optional[str] = Query(None, description="Filter by property type"),
    language: Optional[str] = Query(None, description="Filter by language"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    created_by: Optional[str] = Query(None, description="Filter by creator"),
    skip: int = Query(0, ge=0, description="Number of templates to skip"),
    limit: int = Query(20, ge=1, le=100, description="Number of templates to return"),
    current_user: User = Depends(get_current_user)
):
    """Get templates with optional filters"""
    try:
        filters = TemplateFilters(
            property_type=property_type,
            language=language,
            is_active=is_active,
            created_by=created_by,
            skip=skip,
            limit=limit
        )
        
        service = get_template_service()
        templates = await service.get_templates(filters)
        return templates
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{template_id}", response_model=TemplateResponse)
async def get_template(
    template_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get a specific template by ID"""
    try:
        service = get_template_service()
        template = await service.get_template(template_id)
        return template
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/{template_id}", response_model=TemplateResponse)
async def update_template(
    template_id: str,
    template_data: TemplateUpdateRequest,
    current_user: User = Depends(get_current_user)
):
    """Update an existing template"""
    try:
        service = get_template_service()
        template = await service.update_template(template_id, template_data, current_user.id)
        return template
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{template_id}")
async def delete_template(
    template_id: str,
    current_user: User = Depends(get_current_user)
):
    """Delete a template"""
    try:
        service = get_template_service()
        success = await service.delete_template(template_id, current_user.id)
        if not success:
            raise HTTPException(status_code=404, detail="Template not found")
        return {"message": "Template deleted successfully"}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/property-types/available")
async def get_available_property_types():
    """Get list of available property types"""
    try:
        service = get_template_service()
        property_types = await service.get_available_property_types()
        return {"property_types": property_types}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/languages/available")
async def get_available_languages():
    """Get list of available languages in templates"""
    try:
        service = get_template_service()
        languages = await service.get_available_languages()
        return {"languages": languages}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{template_id}/duplicate", response_model=TemplateResponse)
async def duplicate_template(
    template_id: str,
    new_name: str,
    current_user: User = Depends(get_current_user)
):
    """Duplicate an existing template"""
    try:
        service = get_template_service()
        template = await service.duplicate_template(template_id, new_name, current_user.id)
        return template
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{template_id}/activate")
async def activate_template(
    template_id: str,
    current_user: User = Depends(get_current_user)
):
    """Activate a template"""
    try:
        service = get_template_service()
        success = await service.activate_template(template_id, current_user.id)
        if not success:
            raise HTTPException(status_code=404, detail="Template not found")
        return {"message": "Template activated successfully"}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{template_id}/deactivate")
async def deactivate_template(
    template_id: str,
    current_user: User = Depends(get_current_user)
):
    """Deactivate a template"""
    try:
        service = get_template_service()
        success = await service.deactivate_template(template_id, current_user.id)
        if not success:
            raise HTTPException(status_code=404, detail="Template not found")
        return {"message": "Template deactivated successfully"}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{template_id}/usage-stats")
async def get_template_usage_stats(
    template_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get usage statistics for a template"""
    try:
        service = get_template_service()
        stats = await service.get_template_usage_stats(template_id)
        return stats
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
