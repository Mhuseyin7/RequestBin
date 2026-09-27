import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from ..database import get_db
from ..models import Membership, Organization, User
from ..schemas import MemberIn, OrganizationIn
from ..security import current_user_id
from ..services.audit import audit

router = APIRouter(prefix="/api/v1/organizations", tags=["organizations"])
async def require_role(org_id: uuid.UUID, user_id: str, db: AsyncSession, allowed: set[str]) -> Membership:
    member = await db.scalar(select(Membership).where(Membership.organization_id == org_id, Membership.user_id == uuid.UUID(user_id)))
    if not member or member.role not in allowed: raise HTTPException(403, "Insufficient organization permission")
    return member
@router.get("")
async def list_organizations(user_id: str = Depends(current_user_id), db: AsyncSession = Depends(get_db)):
    rows = (await db.execute(select(Organization, Membership.role).join(Membership).where(Membership.user_id == uuid.UUID(user_id)))).all()
    return [{"id":str(o.id),"name":o.name,"role":role,"created_at":o.created_at} for o, role in rows]
@router.post("", status_code=201)
async def create_organization(payload: OrganizationIn, user_id: str = Depends(current_user_id), db: AsyncSession = Depends(get_db)):
    org = Organization(name=payload.name); db.add(org); await db.flush(); db.add(Membership(organization_id=org.id, user_id=uuid.UUID(user_id), role="OWNER")); await audit(db, user_id, "organization.create", "organization", str(org.id)); await db.commit()
    return {"id":str(org.id),"name":org.name,"role":"OWNER"}
@router.get("/{org_id}/members")
async def members(org_id: uuid.UUID, user_id: str = Depends(current_user_id), db: AsyncSession = Depends(get_db)):
    await require_role(org_id, user_id, db, {"OWNER","ADMIN","DEVELOPER","VIEWER"})
    rows = (await db.execute(select(User.email, Membership.role, Membership.id).join(Membership).where(Membership.organization_id == org_id))).all()
    return [{"id":str(mid),"email":email,"role":role} for email,role,mid in rows]
@router.post("/{org_id}/members", status_code=201)
async def add_member(org_id: uuid.UUID, payload: MemberIn, user_id: str = Depends(current_user_id), db: AsyncSession = Depends(get_db)):
    await require_role(org_id, user_id, db, {"OWNER","ADMIN"}); member_user = await db.scalar(select(User).where(User.email == payload.email.lower()))
    if not member_user: raise HTTPException(404, "User must register before being added")
    if await db.scalar(select(Membership).where(Membership.organization_id == org_id, Membership.user_id == member_user.id)): raise HTTPException(409, "User is already a member")
    item = Membership(organization_id=org_id, user_id=member_user.id, role=payload.role); db.add(item); await audit(db, user_id, "organization.member_add", "organization", str(org_id), {"email":payload.email,"role":payload.role}); await db.commit()
    return {"id":str(item.id),"email":member_user.email,"role":item.role}
