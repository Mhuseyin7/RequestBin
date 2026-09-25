"""Retention worker: keeps captured request data from surviving endpoint expiry."""
import asyncio
import logging
from datetime import datetime, timezone
from sqlalchemy import select
from .database import SessionLocal
from .models import CapturedRequest, Endpoint
from .services.storage import storage

logger = logging.getLogger("requestbinx.worker")

async def prune_expired() -> int:
    async with SessionLocal() as db:
        expired = (await db.scalars(select(Endpoint).where(Endpoint.expires_at.is_not(None), Endpoint.expires_at < datetime.now(timezone.utc)))).all()
        for endpoint in expired:
            items = (await db.scalars(select(CapturedRequest).where(CapturedRequest.endpoint_id == endpoint.id))).all()
            for item in items:
                if item.body_path:
                    try: (storage.root / item.body_path).unlink(missing_ok=True)
                    except OSError as exc: logger.warning("body_delete_failed endpoint=%s error=%s", endpoint.id, exc)
            await db.delete(endpoint)
        await db.commit()
        return len(expired)

async def main():
    while True:
        try:
            count = await prune_expired()
            if count: logger.info("retention_pruned_endpoints=%s", count)
        except Exception:
            logger.exception("retention_worker_failed")
        await asyncio.sleep(300)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
    asyncio.run(main())
