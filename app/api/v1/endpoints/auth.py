from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.schemas.user import UserCreate, UserLogin, UserResponse, Token
from app.services.auth_service import AuthService
from app.repositories.user_repository import UserRepository
from app.core.exceptions import AuthenticationError, ValidationError, ConflictError

router = APIRouter()
security = HTTPBearer()

def get_auth_service() -> AuthService:
    user_repo = UserRepository()
    return AuthService(user_repo)

@router.post("/register", response_model=Token)
async def register(
    user_data: UserCreate,
    auth_service: AuthService = Depends(get_auth_service)
):
    """Register a new user and return access token"""
    try:
        user = await auth_service.register_user(user_data)
        # Create access token for the newly registered user
        access_token = auth_service.create_access_token(user.id, user.email)
        
        return Token(
            access_token=access_token,
            user=user
        )
    except (ValidationError, ConflictError) as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail=str(e)
        )

@router.post("/login", response_model=Token)
async def login(
    user_data: UserLogin,
    auth_service: AuthService = Depends(get_auth_service)
):
    """Login user and return access token"""
    user = await auth_service.authenticate_user(user_data.email, user_data.password)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
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
    """Get current user profile"""
    try:
        user = await auth_service.get_current_user(credentials.credentials)
        return user
    except AuthenticationError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail=str(e)
        )

@router.post("/logout")
async def logout():
    """Logout endpoint"""
    return {"message": "Logged out successfully"}
