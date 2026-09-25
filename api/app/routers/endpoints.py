import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from ..database import get_db
from ..models import CapturedRequest, Endpoint
from ..schemas import EndpointIn
from ..security import current_user_id, token
from ..services.redaction import redact_headers

router = APIRouter(prefix="/api/v1", tags=["endpoints"])
async def owned(endpoint_id: uuid.UUID, user_id: str, db: AsyncSession) -> Endpoint:
    endpoint = await db.scalar(select(Endpoint).where(Endpoint.id == endpoint_id, Endpoint.owner_id == uuid.UUID(user_id)))
    if not endpoint: raise HTTPException(404, "Endpoint not found")
    return endpoint
@router.get("/endpoints")
async def list_endpoints(user_id: str = Depends(current_user_id), db: AsyncSession = Depends(get_db)):
    rows = (await db.scalars(select(Endpoint).where(Endpoint.owner_id == uuid.UUID(user_id)).order_by(Endpoint.created_at.desc()))).all()
    return [{"id": str(e.id), "name": e.name, "token": e.token, "enabled": e.enabled, "created_at": e.created_at} for e in rows]
@router.post("/endpoints", status_code=201)
async def create_endpoint(payload: EndpointIn, user_id: str = Depends(current_user_id), db: AsyncSession = Depends(get_db)):
    endpoint = Endpoint(owner_id=uuid.UUID(user_id), name=payload.name, token=token(), max_body_size=payload.max_body_size, expires_at=payload.expires_at)
    db.add(endpoint); await db.commit(); await db.refresh(endpoint)
    return {"id": str(endpoint.id), "name": endpoint.name, "token": endpoint.token, "receive_url": f"/h/{endpoint.token}"}
@router.get("/endpoints/{endpoint_id}/requests")
async def requests(endpoint_id: uuid.UUID, user_id: str = Depends(current_user_id), db: AsyncSession = Depends(get_db)):
    await owned(endpoint_id, user_id, db)
    rows = (await db.scalars(select(CapturedRequest).where(CapturedRequest.endpoint_id == endpoint_id).order_by(CapturedRequest.received_at.desc()).limit(200))).all()
    return [{"id": str(r.id), "method": r.method, "path": r.path, "headers": redact_headers(r.headers), "body_preview": r.body_preview, "body_size": r.body_size, "source_ip": r.source_ip, "content_type": r.content_type, "received_at": r.received_at} for r in rows]
@router.get("/requests/{request_id}")
async def request_detail(request_id: uuid.UUID, user_id: str = Depends(current_user_id), db: AsyncSession = Depends(get_db)):
    row = await db.scalar(select(CapturedRequest).join(Endpoint).where(CapturedRequest.id == request_id, Endpoint.owner_id == uuid.UUID(user_id)))
    if not row: raise HTTPException(404, "Request not found")
    return {"id":str(row.id), "method":row.method, "path":row.path, "query":row.query, "headers":redact_headers(row.headers), "cookies":row.cookies, "body":row.body_preview, "body_size":row.body_size, "source_ip":row.source_ip, "content_type":row.content_type, "protocol":row.protocol, "user_agent":row.user_agent, "received_at":row.received_at}
