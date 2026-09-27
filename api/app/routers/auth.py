from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from ..database import get_db
from ..models import Membership, Organization, User
from ..schemas import LoginIn, RegisterIn
from ..security import hash_password, make_jwt, verify_password
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
    return {"access_token": make_jwt(str(user.id)), "token_type": "bearer"}
