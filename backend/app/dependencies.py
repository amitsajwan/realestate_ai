from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.services.auth_service import AuthService
from app.repositories.user_repository import UserRepository
from app.core.exceptions import AuthenticationError
from app.core.database import get_database

security = HTTPBearer()

def get_auth_service() -> AuthService:
    """Get authentication service instance"""
    db = get_database()
    user_repo = UserRepository(db)
    return AuthService(user_repo)

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    auth_service: AuthService = Depends(get_auth_service)
):
    """Get current authenticated user"""
    try:
        user = await auth_service.get_current_user(credentials.credentials)
        return user
    except AuthenticationError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"}
        )

async def get_current_user_id(current_user = Depends(get_current_user)) -> str:
    """Get current user ID"""
    return current_user.id  # FIXED: was current_user.idauth_service