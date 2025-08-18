"""
FastAPI Dependencies
====================
Centralized dependency injection for app services and user retrieval.
"""
from __future__ import annotations
from app.services.lead_service import LeadService     
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import logging


from app.services.auth_service import AuthService
from app.repositories.user_repository import UserRepository

security = HTTPBearer()
logger = logging.getLogger(__name__)


def get_auth_service() -> AuthService:
    user_repo = UserRepository()
    return AuthService(user_repo)


async def get_current_user_id(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    auth_service: AuthService = Depends(get_auth_service)
) -> str:
    try:
        user = await auth_service.get_current_user(credentials.credentials)
        return user.id
    except Exception as e:
        logger.error(f"Invalid authentication credentials: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials"
        )


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    auth_service: AuthService = Depends(get_auth_service)
):
    try:
        return await auth_service.get_current_user(credentials.credentials)
    except Exception as e:
        logger.error(f"Invalid authentication credentials: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials"
        )


def get_lead_service() -> "LeadService":
    from app.services.lead_service import LeadService
    from app.repositories.lead_repository import LeadRepository
    lead_repo = LeadRepository()
    return LeadService(lead_repo)
