import hashlib, secrets
from datetime import datetime, timedelta, timezone
from fastapi import Depends, Header, Request
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
def make_jwt(user_id: str):
    issued = datetime.now(timezone.utc)
    claims = {"sub": user_id, "iat": issued, "exp": issued + timedelta(minutes=get_settings().access_token_ttl_minutes)}
    return jwt.encode(claims, get_settings().jwt_secret, algorithm="HS256")
def required_api_scope(request: Request) -> str | None:
    method, path = request.method, request.url.path
    if path.endswith("/api-keys"): return "bins:read" if method == "GET" else None
    if "/replay" in path: return "requests:replay"
    if path.endswith("/requests") or "/requests/" in path: return "requests:delete" if method == "DELETE" else "requests:read"
    if "/endpoints" in path and method in {"POST", "DELETE"}: return "bins:write"
    return None
async def current_user_id(request: Request, credentials: HTTPAuthorizationCredentials = bearer, x_api_key: str | None = Header(default=None), db: AsyncSession = Depends(get_db)):
    if x_api_key:
        digest = hashlib.sha256(x_api_key.encode()).hexdigest()
        key = await db.scalar(select(ApiKey).where(ApiKey.key_hash == digest))
        if key and (not key.expires_at or key.expires_at > datetime.now(timezone.utc)):
            required = required_api_scope(request)
            if required and required not in (key.scopes or []): raise HTTPException(status_code=403, detail=f"API key scope required: {required}")
            key.last_used_at = datetime.now(timezone.utc); await db.commit(); return str(key.owner_id)
        raise HTTPException(status_code=401, detail="Invalid API key")
    if not credentials: raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required")
    try: return jwt.decode(credentials.credentials, get_settings().jwt_secret, algorithms=["HS256"])["sub"]
    except jwt.InvalidTokenError: raise HTTPException(status_code=401, detail="Invalid access token")
