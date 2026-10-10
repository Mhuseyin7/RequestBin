import uuid
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import and_, delete, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from ..database import get_db
from ..models import CapturedRequest, Delivery, Endpoint, Membership
from ..security import current_user_id
from ..services.audit import audit
from ..services.codegen import snippets
from ..services.redaction import redact_headers
from ..services.storage import storage

router = APIRouter(prefix="/api/v1", tags=["requests"])
async def owned_request(request_id: uuid.UUID, user_id: str, db: AsyncSession) -> CapturedRequest:
    member_orgs = select(Membership.organization_id).where(Membership.user_id == uuid.UUID(user_id))
    row = await db.scalar(select(CapturedRequest).join(Endpoint).where(CapturedRequest.id == request_id, or_(Endpoint.owner_id == uuid.UUID(user_id), Endpoint.organization_id.in_(member_orgs))))
    if not row: raise HTTPException(404, "Request not found")
    return row
@router.get("/requests/search")
async def search(method: str | None = None, content_type: str | None = None, source_ip: str | None = None, limit: int = Query(50, ge=1, le=200), user_id: str = Depends(current_user_id), db: AsyncSession = Depends(get_db)):
    member_orgs = select(Membership.organization_id).where(Membership.user_id == uuid.UUID(user_id))
    clauses = [or_(Endpoint.owner_id == uuid.UUID(user_id), Endpoint.organization_id.in_(member_orgs))]
    if method: clauses.append(CapturedRequest.method == method.upper())
    if content_type: clauses.append(CapturedRequest.content_type == content_type)
    if source_ip: clauses.append(CapturedRequest.source_ip == source_ip)
    rows = (await db.scalars(select(CapturedRequest).join(Endpoint).where(and_(*clauses)).order_by(CapturedRequest.received_at.desc()).limit(limit))).all()
    return [{"id":str(x.id),"endpoint_id":str(x.endpoint_id),"method":x.method,"path":x.path,"source_ip":x.source_ip,"content_type":x.content_type,"body_size":x.body_size,"received_at":x.received_at} for x in rows]
@router.delete("/requests/{request_id}", status_code=204)
async def delete_request(request_id: uuid.UUID, user_id: str = Depends(current_user_id), db: AsyncSession = Depends(get_db)):
    row = await owned_request(request_id, user_id, db); endpoint = await db.get(Endpoint, row.endpoint_id)
    member = await db.scalar(select(Membership).where(Membership.organization_id == endpoint.organization_id, Membership.user_id == uuid.UUID(user_id))) if endpoint and endpoint.organization_id else None
    if endpoint and endpoint.owner_id != uuid.UUID(user_id) and (not member or member.role not in {"OWNER", "ADMIN", "DEVELOPER"}): raise HTTPException(403, "Insufficient request deletion permission")
    storage.delete(row.body_path); await db.execute(delete(Delivery).where(Delivery.request_id == row.id)); await audit(db,user_id,"request.delete","request",str(request_id)); await db.delete(row); await db.commit()
@router.get("/requests/{request_id}/export")
async def export_request(request_id: uuid.UUID, user_id: str = Depends(current_user_id), db: AsyncSession = Depends(get_db)):
    row = await owned_request(request_id,user_id,db); url = f"{row.path}"; headers = redact_headers(row.headers)
    return {"request":{"method":row.method,"url":url,"headers":headers,"query":row.query,"cookies":row.cookies,"body":row.body_preview,"body_size":row.body_size,"received_at":row.received_at},"snippets":snippets(row.method,url,row.headers,row.body_preview)}
@router.get("/requests/compare")
async def compare(first: uuid.UUID, second: uuid.UUID, user_id: str = Depends(current_user_id), db: AsyncSession = Depends(get_db)):
    a,b = await owned_request(first,user_id,db), await owned_request(second,user_id,db)
    def diff(left: dict, right: dict): return {key:{"left":left.get(key),"right":right.get(key)} for key in set(left)|set(right) if left.get(key)!=right.get(key)}
    return {"headers":diff(redact_headers(a.headers),redact_headers(b.headers)),"query":diff(a.query,b.query),"body":{"left":a.body_preview,"right":b.body_preview,"equal":a.body_preview==b.body_preview}}
