import redis.asyncio as aioredis
from fastapi import HTTPException, Request
from config import get_settings

settings = get_settings()
_redis = None

async def get_redis():
    global _redis
    if _redis is None:
        _redis = await aioredis.from_url(settings.REDIS_URL, decode_responses=True)
    return _redis

async def check_rate_limit(identifier: str, limit: int = 60, window: int = 60):
    """Sliding window rate limiter. identifier = user_id or api_key_id."""
    try:
        r   = await get_redis()
        key = f"ratelimit:{identifier}:{window}"
        current = await r.incr(key)
        if current == 1:
            await r.expire(key, window)
        if current > limit:
            ttl = await r.ttl(key)
            raise HTTPException(
                status_code=429,
                detail=f"Rate limit exceeded. Retry after {ttl}s",
                headers={"Retry-After": str(ttl)}
            )
    except HTTPException:
        raise
    except Exception:
        pass  # Redis down → don't block requests
