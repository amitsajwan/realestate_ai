from typing import Dict, Any
from fastapi import APIRouter, HTTPException, Depends, status
from app.schemas.onboarding import OnboardingStep, OnboardingComplete
from app.services.onboarding_service import OnboardingService
from app.core.auth_backend import current_active_user
from app.models.user import User

router = APIRouter()


def _ensure_user_access(path_user_id: str, current_user: User):
    current_id = str(current_user.id)
    if not current_id or current_id != str(path_user_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden: cannot access another user's onboarding")


@router.get("/{user_id}", response_model=OnboardingStep)
async def get_onboarding_step(
    user_id: str,
    service: OnboardingService = Depends(),
    current_user: User = Depends(current_active_user),
):
    _ensure_user_access(user_id, current_user)
    try:
        return await service.get_step(user_id)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{user_id}", response_model=OnboardingStep)
async def save_onboarding_step(
    user_id: str,
    step_data: OnboardingStep,
    service: OnboardingService = Depends(),
    current_user: User = Depends(current_active_user),
):
    _ensure_user_access(user_id, current_user)
    try:
        return await service.save_step(user_id, step_data)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{user_id}/complete", response_model=OnboardingComplete)
async def complete_onboarding(
    user_id: str,
    service: OnboardingService = Depends(),
    current_user: User = Depends(current_active_user),
):
    _ensure_user_access(user_id, current_user)
    try:
        return await service.complete_onboarding(user_id)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))