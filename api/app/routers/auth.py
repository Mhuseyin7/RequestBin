from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from ..database import get_db
from ..models import User
from ..schemas import LoginIn, RegisterIn
from ..security import hash_password, make_jwt, verify_password

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])
@router.post("/register", status_code=201)
async def register(payload: RegisterIn, db: AsyncSession = Depends(get_db)):
    if await db.scalar(select(User).where(User.email == payload.email.lower())): raise HTTPException(409, "Email already registered")
    user = User(email=payload.email.lower(), password_hash=hash_password(payload.password)); db.add(user); await db.commit(); await db.refresh(user)
    return {"access_token": make_jwt(str(user.id)), "token_type": "bearer"}
@router.post("/login")
async def login(payload: LoginIn, db: AsyncSession = Depends(get_db)):
    user = await db.scalar(select(User).where(User.email == payload.email.lower()))
    if not user or not verify_password(payload.password, user.password_hash): raise HTTPException(401, "Invalid email or password")
    return {"access_token": make_jwt(str(user.id)), "token_type": "bearer"}
