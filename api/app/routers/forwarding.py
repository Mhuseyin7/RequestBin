import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from ..database import get_db
from ..models import Delivery, Endpoint, ForwardingRule
from ..schemas import ForwardingRuleIn
from ..security import current_user_id
from ..services.audit import audit
from ..services.ssrf import validate_target

router = APIRouter(prefix="/api/v1/endpoints/{endpoint_id}/forwarding-rules", tags=["forwarding"])
async def endpoint_for_user(endpoint_id: uuid.UUID, user_id: str, db: AsyncSession) -> Endpoint:
    item = await db.scalar(select(Endpoint).where(Endpoint.id == endpoint_id, Endpoint.owner_id == uuid.UUID(user_id)))
    if not item: raise HTTPException(404, "Endpoint not found")
    return item
@router.get("")
async def list_rules(endpoint_id: uuid.UUID, user_id: str = Depends(current_user_id), db: AsyncSession = Depends(get_db)):
    await endpoint_for_user(endpoint_id, user_id, db); rows = (await db.scalars(select(ForwardingRule).where(ForwardingRule.endpoint_id == endpoint_id))).all()
    return [{"id":str(x.id),"name":x.name,"target_url":x.target_url,"enabled":x.enabled,"condition":x.condition,"transforms":x.transforms,"headers":x.headers,"retry_count":x.retry_count} for x in rows]
@router.post("", status_code=201)
async def create_rule(endpoint_id: uuid.UUID, payload: ForwardingRuleIn, user_id: str = Depends(current_user_id), db: AsyncSession = Depends(get_db)):
    await endpoint_for_user(endpoint_id, user_id, db); validate_target(str(payload.target_url))
    item = ForwardingRule(endpoint_id=endpoint_id, **payload.model_dump(mode="json")); db.add(item); await audit(db, user_id, "forwarding_rule.create", "forwarding_rule", str(item.id)); await db.commit(); await db.refresh(item)
    return {"id":str(item.id),"name":item.name,"target_url":item.target_url,"enabled":item.enabled}
@router.delete("/{rule_id}", status_code=204)
async def delete_rule(endpoint_id: uuid.UUID, rule_id: uuid.UUID, user_id: str = Depends(current_user_id), db: AsyncSession = Depends(get_db)):
    await endpoint_for_user(endpoint_id, user_id, db); item = await db.scalar(select(ForwardingRule).where(ForwardingRule.id == rule_id, ForwardingRule.endpoint_id == endpoint_id))
    if not item: raise HTTPException(404, "Forwarding rule not found")
    await audit(db, user_id, "forwarding_rule.delete", "forwarding_rule", str(item.id)); await db.delete(item); await db.commit()
@router.get("/deliveries")
async def deliveries(endpoint_id: uuid.UUID, user_id: str = Depends(current_user_id), db: AsyncSession = Depends(get_db)):
    await endpoint_for_user(endpoint_id, user_id, db); rows = (await db.execute(select(Delivery, ForwardingRule.name).join(ForwardingRule).where(ForwardingRule.endpoint_id == endpoint_id).order_by(Delivery.created_at.desc()).limit(100))).all()
    return [{"id":str(d.id),"rule":name,"state":d.state,"attempt":d.attempt,"status_code":d.status_code,"latency_ms":d.latency_ms,"error":d.error,"created_at":d.created_at} for d,name in rows]
