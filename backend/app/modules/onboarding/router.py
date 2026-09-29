"""POST /join/otp/request -> /join/otp/verify -> /join/site: phone to live website."""
from fastapi import APIRouter, Depends, HTTPException

from app.core.auth_backend import current_active_user, jwt_strategy
from app.core.config import settings
from app.core.database import get_database
from app.models.user import User

from .otp import ConsoleOTPProvider, OTPError, OTPService
from .schemas import LoginResult, OTPRequest, OTPRequested, OTPVerify, SiteCreate, SiteResult
from .service import BeanieUserStore, OnboardingService

router = APIRouter()


def get_service() -> OnboardingService:
    db = get_database()
    otp = OTPService(db, ConsoleOTPProvider(), settings.jwt_secret_key)
    return OnboardingService(db, otp, BeanieUserStore(), jwt_strategy.write_token, settings.public_site_url)


@router.post("/otp/request", response_model=OTPRequested)
async def request_otp(body: OTPRequest, svc: OnboardingService = Depends(get_service)):
    try:
        code = await svc.request_code(body.phone)
    except OTPError as e:
        raise HTTPException(status_code=e.status_code, detail=str(e))
    return OTPRequested(dev_code=code if settings.environment == "development" else None)


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
