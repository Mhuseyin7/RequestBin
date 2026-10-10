import time, uuid
import httpx
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from ..database import get_db
from ..models import CapturedRequest, Endpoint, Membership, Replay
from ..schemas import ReplayIn
from ..security import current_user_id
from ..services.ssrf import validate_target
from ..services.storage import storage

router = APIRouter(prefix="/api/v1", tags=["replays"])
@router.post("/requests/{request_id}/replay", status_code=201)
async def replay(request_id: uuid.UUID, payload: ReplayIn, user_id: str = Depends(current_user_id), db: AsyncSession = Depends(get_db)):
    member_orgs = select(Membership.organization_id).where(Membership.user_id == uuid.UUID(user_id))
    original = await db.scalar(select(CapturedRequest).join(Endpoint).where(CapturedRequest.id == request_id, or_(Endpoint.owner_id == uuid.UUID(user_id), Endpoint.organization_id.in_(member_orgs))))
    if not original: raise HTTPException(404, "Request not found")
    endpoint = await db.get(Endpoint, original.endpoint_id)
    member = await db.scalar(select(Membership).where(Membership.organization_id == endpoint.organization_id, Membership.user_id == uuid.UUID(user_id))) if endpoint and endpoint.organization_id else None
    if endpoint and endpoint.owner_id != uuid.UUID(user_id) and (not member or member.role not in {"OWNER", "ADMIN", "DEVELOPER"}): raise HTTPException(403, "Insufficient replay permission")
    validate_target(str(payload.target_url)); record = Replay(request_id=request_id, target_url=str(payload.target_url)); db.add(record); await db.flush()
    started = time.perf_counter()
    try:
        async with httpx.AsyncClient(follow_redirects=False, trust_env=False, timeout=10) as client:
            content = payload.body if payload.body is not None else (storage.get(original.body_path) if original.body_path else None)
            response = await client.request(payload.method, str(payload.target_url), headers=payload.headers, content=content)
        record.status_code, record.response_headers, record.response_body = response.status_code, dict(response.headers), response.text[:100_000]
    except httpx.HTTPError as exc: record.error = str(exc)
    record.latency_ms = int((time.perf_counter()-started)*1000); await db.commit(); await db.refresh(record)
    return {"id":str(record.id), "status_code":record.status_code, "headers":record.response_headers, "body":record.response_body, "latency_ms":record.latency_ms, "error":record.error}
