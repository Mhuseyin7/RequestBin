import pyotp
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from ..database import get_db
from ..models import Membership, Organization, User
from ..schemas import LoginIn, RegisterIn
from ..security import current_user_id, hash_password, make_jwt, verify_password
from ..config import get_settings
from ..services.rate_limit import enforce

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])
@router.post("/register", status_code=201)
async def register(payload: RegisterIn, request: Request, db: AsyncSession = Depends(get_db)):
    await enforce(request, "register", get_settings().rate_limit_auth_per_minute)
    if await db.scalar(select(User).where(User.email == payload.email.lower())): raise HTTPException(409, "Email already registered")
    user = User(email=payload.email.lower(), password_hash=hash_password(payload.password)); db.add(user); await db.flush()
    organization = Organization(name=f"{payload.email.split('@')[0]}'s workspace"); db.add(organization); await db.flush(); db.add(Membership(organization_id=organization.id, user_id=user.id, role="OWNER")); await db.commit(); await db.refresh(user)
    return {"access_token": make_jwt(str(user.id)), "token_type": "bearer"}
@router.post("/login")
async def login(payload: LoginIn, request: Request, db: AsyncSession = Depends(get_db)):
    await enforce(request, "login", get_settings().rate_limit_auth_per_minute)
    user = await db.scalar(select(User).where(User.email == payload.email.lower()))
    if not user or not verify_password(payload.password, user.password_hash): raise HTTPException(401, "Invalid email or password")
    if user.totp_secret and (not payload.totp_code or not pyotp.TOTP(user.totp_secret).verify(payload.totp_code)): raise HTTPException(401, "A valid authenticator code is required")
    return {"access_token": make_jwt(str(user.id)), "token_type": "bearer"}
@router.post("/totp/setup")
async def setup_totp(user_id: str = Depends(current_user_id), db: AsyncSession = Depends(get_db)):
    user = await db.get(User, user_id)
    if not user: raise HTTPException(404, "User not found")
    user.totp_secret = pyotp.random_base32(); await db.commit()
    return {"secret":user.totp_secret,"otpauth_url":pyotp.TOTP(user.totp_secret).provisioning_uri(name=user.email, issuer_name="RequestBinX")}
@router.post("/totp/disable")
async def disable_totp(user_id: str = Depends(current_user_id), db: AsyncSession = Depends(get_db)):
    user = await db.get(User, user_id)
    if not user: raise HTTPException(404, "User not found")
    user.totp_secret = None; await db.commit(); return {"enabled":False}
