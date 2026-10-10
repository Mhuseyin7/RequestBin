from fastapi import HTTPException, Request
from redis.asyncio import Redis
from ..config import get_settings

_redis: Redis | None = None
async def redis_client() -> Redis:
    global _redis
    if _redis is None: _redis = Redis.from_url(get_settings().redis_url, decode_responses=True, socket_connect_timeout=1, socket_timeout=1)
    return _redis
async def enforce(request: Request, bucket: str, limit: int) -> None:
    identity = request.client.host if request.client else "unknown"
    key = f"rbx:rate:{bucket}:{identity}"
    try:
        client = await redis_client(); count = await client.incr(key)
        if count == 1: await client.expire(key, 60)
    except Exception as exc:
        raise HTTPException(503, "Rate limiting service is temporarily unavailable") from exc
    if count > limit: raise HTTPException(429, "Rate limit exceeded. Try again shortly.")
