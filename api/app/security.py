import secrets
from argon2 import PasswordHasher
from fastapi import HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
import jwt
from .config import get_settings

hasher, bearer = PasswordHasher(), HTTPBearer(auto_error=False)
def token(): return secrets.token_urlsafe(24)
def hash_password(value: str): return hasher.hash(value)
def verify_password(value: str, hashed: str):
    try: return hasher.verify(hashed, value)
    except Exception: return False
def make_jwt(user_id: str): return jwt.encode({"sub": user_id}, get_settings().jwt_secret, algorithm="HS256")
def current_user_id(credentials: HTTPAuthorizationCredentials = bearer):
    if not credentials: raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required")
    try: return jwt.decode(credentials.credentials, get_settings().jwt_secret, algorithms=["HS256"])["sub"]
    except jwt.InvalidTokenError: raise HTTPException(status_code=401, detail="Invalid access token")
