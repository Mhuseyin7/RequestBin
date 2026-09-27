from fastapi import HTTPException, Request
from redis.asyncio import Redis
from ..config import get_settings

_redis: Redis | None = None
async def redis_client() -> Redis:
    global _redis
    if _redis is None: _redis = Redis.from_url(get_settings().redis_url, decode_responses=True)
    return _redis
async def enforce(request: Request, bucket: str, limit: int) -> None:
    identity = request.client.host if request.client else "unknown"
    key = f"rbx:rate:{bucket}:{identity}"
    try:
        client = await redis_client(); count = await client.incr(key)
        if count == 1: await client.expire(key, 60)
    except Exception:
        # Do not make capture unavailable if Redis is temporarily unavailable; emit structured failure at caller level.
        return
    if count > limit: raise HTTPException(429, "Rate limit exceeded. Try again shortly.")
