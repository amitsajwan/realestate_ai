from typing import Dict, Any
from fastapi import APIRouter, HTTPException, Depends, status
from app.schemas.onboarding import OnboardingStep, OnboardingComplete
from app.services.onboarding_service import OnboardingService
from app.api.v1.endpoints.auth import get_current_user

router = APIRouter()


def _ensure_user_access(path_user_id: str, current_user: Dict[str, Any]):
    current_id = current_user.get("id") or current_user.get("_id")
    if isinstance(current_id, dict) and "$oid" in current_id:
        current_id = current_id["$oid"]
    if not current_id or str(current_id) != str(path_user_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden: cannot access another user's onboarding")


@router.get("/onboarding/{user_id}", response_model=OnboardingStep)
async def get_onboarding_step(
    user_id: str,
    service: OnboardingService = Depends(),
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    _ensure_user_access(user_id, current_user)
    try:
        return await service.get_step(user_id)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/onboarding/{user_id}", response_model=OnboardingStep)
async def save_onboarding_step(
    user_id: str,
    step_data: OnboardingStep,
    service: OnboardingService = Depends(),
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    _ensure_user_access(user_id, current_user)
    try:
        return await service.save_step(user_id, step_data)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/onboarding/{user_id}/complete", response_model=OnboardingComplete)
async def complete_onboarding(
    user_id: str,
    service: OnboardingService = Depends(),
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    _ensure_user_access(user_id, current_user)
    try:
        return await service.complete_onboarding(user_id)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))