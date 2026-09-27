import hashlib, secrets
from datetime import datetime, timezone
from fastapi import Depends, Header
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from argon2 import PasswordHasher
from fastapi import HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
import jwt
from .config import get_settings
from .database import get_db
from .models import ApiKey

hasher, bearer = PasswordHasher(), HTTPBearer(auto_error=False)
def token(): return secrets.token_urlsafe(24)
def hash_password(value: str): return hasher.hash(value)
def verify_password(value: str, hashed: str):
    try: return hasher.verify(hashed, value)
    except Exception: return False
def make_jwt(user_id: str): return jwt.encode({"sub": user_id}, get_settings().jwt_secret, algorithm="HS256")
async def current_user_id(credentials: HTTPAuthorizationCredentials = bearer, x_api_key: str | None = Header(default=None), db: AsyncSession = Depends(get_db)):
    if x_api_key:
        digest = hashlib.sha256(x_api_key.encode()).hexdigest()
        key = await db.scalar(select(ApiKey).where(ApiKey.key_hash == digest))
        if key and (not key.expires_at or key.expires_at > datetime.now(timezone.utc)):
            key.last_used_at = datetime.now(timezone.utc); await db.commit(); return str(key.owner_id)
        raise HTTPException(status_code=401, detail="Invalid API key")
    if not credentials: raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required")
    try: return jwt.decode(credentials.credentials, get_settings().jwt_secret, algorithms=["HS256"])["sub"]
    except jwt.InvalidTokenError: raise HTTPException(status_code=401, detail="Invalid access token")
