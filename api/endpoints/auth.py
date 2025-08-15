from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from models.user import User, UserCreate, Token
from repositories.user_repository import UserRepository, get_user_repository
from core.security import verify_password, create_access_token
from core.config import settings
from core.dependencies import get_current_user

router = APIRouter()

@router.post("/register", response_model=User)
async def register_user(
    user: UserCreate,
    user_repo: UserRepository = Depends(get_user_repository)
):
    # Check if user already exists
    existing_user = await user_repo.get_user(user.username)
    if existing_user:
        raise HTTPException(
            status_code=400,
            detail="Username already registered"
        )
    
    # Create new user
    db_user = await user_repo.create_user(user)
    
    # Return user without password
    return User(
        id=db_user.id,
        username=db_user.username,
        email=db_user.email,
        full_name=db_user.full_name,
        is_active=db_user.is_active,
        created_at=db_user.created_at,
        updated_at=db_user.updated_at
    )

@router.post("/token", response_model=Token)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    user_repo: UserRepository = Depends(get_user_repository)
):
    user = await user_repo.get_user(form_data.username)
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/me", response_model=User)
async def read_users_me(current_user: dict = Depends(get_current_user)):
    # In a real implementation, you'd fetch the full user from the database
    # For now, we'll return what we have from the token
    return current_user
