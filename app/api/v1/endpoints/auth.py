"""
Authentication Endpoints
========================
Handles user registration, login, logout, and profile retrieval.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.schemas.user import UserCreate, UserLogin, UserResponse, Token
from app.services.auth_service import AuthService
from app.repositories.user_repository import UserRepository
from app.core.exceptions import AuthenticationError, ValidationError

router = APIRouter()
security = HTTPBearer()


def get_auth_service() -> AuthService:
    """Provide authentication service with repository."""
    user_repo = UserRepository()
    return AuthService(user_repo)


@router.post("/register", response_model=UserResponse)
async def register(
    user_data: UserCreate,
    auth_service: AuthService = Depends(get_auth_service)
):
    """Register a new user."""
    try:
        user = await auth_service.register_user(user_data)
        return user
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/login", response_model=Token)
async def login(
    user_data: UserLogin,
    auth_service: AuthService = Depends(get_auth_service)
):
    """Authenticate user and return access token."""
    user = await auth_service.authenticate_user(user_data.email, user_data.password)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )
    
    access_token = auth_service.create_access_token(user.id, user.email)
    
    return Token(
        access_token=access_token,
        user=user
    )


@router.get("/profile", response_model=UserResponse)
async def get_profile(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    auth_service: AuthService = Depends(get_auth_service)
):
    """Get current authenticated user profile."""
    try:
        user = await auth_service.get_current_user(credentials.credentials)
        return user
    except AuthenticationError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))


@router.post("/logout")
async def logout():
    """Logout endpoint (token blacklisting can be added here)."""
    return {"message": "Logged out successfully"}
