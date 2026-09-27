import hashlib, secrets, uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from ..database import get_db
from ..models import ApiKey
from ..schemas import ApiKeyIn
from ..security import current_user_id
from ..services.audit import audit

router = APIRouter(prefix="/api/v1/api-keys", tags=["api keys"])
@router.get("")
async def list_keys(user_id: str = Depends(current_user_id), db: AsyncSession = Depends(get_db)):
    items = (await db.scalars(select(ApiKey).where(ApiKey.owner_id == uuid.UUID(user_id)).order_by(ApiKey.created_at.desc()))).all()
    return [{"id":str(x.id),"name":x.name,"prefix":x.prefix,"scopes":x.scopes,"last_used_at":x.last_used_at,"created_at":x.created_at} for x in items]
@router.post("", status_code=201)
async def create_key(payload: ApiKeyIn, user_id: str = Depends(current_user_id), db: AsyncSession = Depends(get_db)):
    secret = "rbx_" + secrets.token_urlsafe(32); item = ApiKey(owner_id=uuid.UUID(user_id), name=payload.name, prefix=secret[:12], key_hash=hashlib.sha256(secret.encode()).hexdigest(), scopes=payload.scopes)
    db.add(item); await audit(db, user_id, "api_key.create", "api_key", str(item.id), {"scopes":payload.scopes}); await db.commit(); await db.refresh(item)
    return {"id":str(item.id), "name":item.name, "key":secret, "warning":"Store this key now; it will not be shown again."}
@router.delete("/{key_id}", status_code=204)
async def revoke_key(key_id: uuid.UUID, user_id: str = Depends(current_user_id), db: AsyncSession = Depends(get_db)):
    item = await db.scalar(select(ApiKey).where(ApiKey.id == key_id, ApiKey.owner_id == uuid.UUID(user_id)))
    if not item: raise HTTPException(404, "API key not found")
    await audit(db, user_id, "api_key.revoke", "api_key", str(item.id)); await db.delete(item); await db.commit()
