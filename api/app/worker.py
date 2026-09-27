"""Retention and safe outbound forwarding worker."""
import asyncio, json, logging, time
from datetime import datetime, timedelta, timezone
import httpx
from sqlalchemy import select
from .database import SessionLocal
from .models import CapturedRequest, Delivery, Endpoint, ForwardingRule
from .services.ssrf import validate_target
from .services.storage import storage
from .services.transforms import apply

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
        await db.commit(); return len(expired)
async def dispatch_deliveries() -> int:
    async with SessionLocal() as db:
        due = (await db.scalars(select(Delivery).where(Delivery.state == "PENDING", Delivery.next_attempt_at <= datetime.now(timezone.utc)).order_by(Delivery.created_at).limit(50))).all()
        for delivery in due:
            request, rule = await db.get(CapturedRequest, delivery.request_id), await db.get(ForwardingRule, delivery.rule_id)
            if not request or not rule or not rule.enabled: delivery.state = "CANCELLED"; continue
            delivery.attempt += 1; started = time.perf_counter()
            try:
                validate_target(rule.target_url); body_value: object = request.body_preview or ""
                if request.content_type and "json" in request.content_type:
                    try: body_value = json.loads(request.body_preview or "")
                    except json.JSONDecodeError: pass
                body_value, headers = apply(body_value, {**request.headers, **rule.headers}, rule.transforms)
                content = json.dumps(body_value) if isinstance(body_value, (dict, list)) else str(body_value)
                async with httpx.AsyncClient(follow_redirects=False, timeout=rule.timeout_seconds) as client: response = await client.request(request.method, rule.target_url, headers=headers, content=content)
                delivery.status_code = response.status_code; delivery.state = "SUCCEEDED" if response.is_success else "FAILED"
                if not response.is_success: delivery.error = f"Target returned HTTP {response.status_code}"
            except (httpx.HTTPError, ValueError) as exc: delivery.error = str(exc); delivery.state = "FAILED"
            delivery.latency_ms = int((time.perf_counter() - started) * 1000)
            if delivery.state == "FAILED" and delivery.attempt <= rule.retry_count:
                delivery.state = "PENDING"; delivery.next_attempt_at = datetime.now(timezone.utc) + timedelta(seconds=2 ** delivery.attempt)
        await db.commit(); return len(due)
async def main():
    while True:
        try:
            count, delivered = await prune_expired(), await dispatch_deliveries()
            if count: logger.info("retention_pruned_endpoints=%s", count)
            if delivered: logger.info("forwarding_deliveries_processed=%s", delivered)
        except Exception: logger.exception("worker_iteration_failed")
        await asyncio.sleep(5)
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s"); asyncio.run(main())
