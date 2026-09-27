import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from ..models import AuditLog

async def audit(db: AsyncSession, actor_id: str | None, action: str, resource_type: str, resource_id: str, metadata: dict | None = None) -> None:
    db.add(AuditLog(actor_id=uuid.UUID(actor_id) if actor_id else None, action=action, resource_type=resource_type, resource_id=resource_id, metadata_=metadata or {}))
