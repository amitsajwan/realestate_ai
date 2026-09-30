"""POST /join/otp/request -> /join/otp/verify -> /join/site: phone to live website."""
from fastapi import APIRouter, Depends, HTTPException
from fastapi_users.authentication import JWTStrategy

from app.core.auth_backend import current_active_user
from app.core.config import settings
from app.core.database import get_database
from app.models.user import User

from .invites import InviteService
from .otp import ConsoleOTPProvider, OTPError, OTPService
from .schemas import LoginResult, OTPRequest, OTPRequested, OTPVerify, SiteCreate, SiteResult, SiteUpdate
from .service import BeanieUserStore, OnboardingError, OnboardingService

router = APIRouter()


def _agent_jwt() -> JWTStrategy:
    # Same secret/algorithm as the app-wide strategy, longer expiry: tokens validate everywhere
    # because expiry is read from the token's own `exp` claim.
    return JWTStrategy(secret=settings.jwt_secret_key, algorithm=settings.jwt_algorithm,
                       lifetime_seconds=settings.join_token_days * 86400)


def get_service() -> OnboardingService:
    db = get_database()
    if settings.join_mode == "invite":
        verifier = InviteService(db, settings.jwt_secret_key)
    else:
        verifier = OTPService(db, ConsoleOTPProvider(), settings.jwt_secret_key)
    return OnboardingService(db, verifier, BeanieUserStore(), _agent_jwt().write_token, settings.public_site_url)


@router.post("/otp/request", response_model=OTPRequested)
async def request_otp(body: OTPRequest, svc: OnboardingService = Depends(get_service)):
    try:
        code = await svc.request_code(body.phone)
    except OTPError as e:
        raise HTTPException(status_code=e.status_code, detail=str(e))
    return OTPRequested(dev_code=code if code and settings.environment == "development" else None,
                        mode="invite" if settings.join_mode == "invite" else "otp")


@router.post("/otp/verify", response_model=LoginResult)
async def verify_otp(body: OTPVerify, svc: OnboardingService = Depends(get_service)):
    try:
        return await svc.verify_and_login(body.phone, body.code)
    except OTPError as e:
        raise HTTPException(status_code=e.status_code, detail=str(e))


@router.post("/site", response_model=SiteResult)
async def create_site(body: SiteCreate, user: User = Depends(current_active_user),
                      svc: OnboardingService = Depends(get_service)):
    return await svc.create_site(user, body)


@router.patch("/site")
async def update_site(body: SiteUpdate, user: User = Depends(current_active_user),
                      svc: OnboardingService = Depends(get_service)):
    try:
        return await svc.update_site(user, body)
    except OnboardingError as e:
        raise HTTPException(status_code=e.status_code, detail=str(e))
