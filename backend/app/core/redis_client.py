import json
from typing import Any, Optional
import redis.asyncio as aioredis
import structlog

from app.core.config import settings

logger = structlog.get_logger(__name__)

_redis_pool: Optional[aioredis.ConnectionPool] = None
_redis_client: Optional[aioredis.Redis] = None


def create_redis_pool() -> aioredis.ConnectionPool:
    return aioredis.ConnectionPool.from_url(
        settings.REDIS_URL,
        max_connections=settings.REDIS_MAX_CONNECTIONS,
        decode_responses=True,
    )


async def get_redis() -> aioredis.Redis:
    global _redis_pool, _redis_client
    if _redis_client is None:
        if _redis_pool is None:
            _redis_pool = create_redis_pool()
        _redis_client = aioredis.Redis(connection_pool=_redis_pool)
    return _redis_client


async def init_redis() -> None:
    logger.info("Initializing Redis connection")
    client = await get_redis()
    await client.ping()
    logger.info("Redis connection established")


async def close_redis() -> None:
    global _redis_pool, _redis_client
    logger.info("Closing Redis connections")
    if _redis_client is not None:
        await _redis_client.aclose()
        _redis_client = None
    if _redis_pool is not None:
        await _redis_pool.aclose()
        _redis_pool = None
    logger.info("Redis connections closed")


async def cache_get(key: str) -> Optional[Any]:
    try:
        client = await get_redis()
        value = await client.get(key)
        if value is None:
            return None
        return json.loads(value)
    except Exception as e:
        logger.warning("Cache get failed", key=key, error=str(e))
        return None


async def cache_set(
    key: str,
    value: Any,
    ttl: int = settings.CACHE_DEFAULT_TTL,
) -> bool:
    try:
        client = await get_redis()
        serialized = json.dumps(value, default=str)
        await client.setex(key, ttl, serialized)
        return True
    except Exception as e:
        logger.warning("Cache set failed", key=key, error=str(e))
        return False


async def cache_delete(key: str) -> bool:
    try:
        client = await get_redis()
        result = await client.delete(key)
        return result > 0
    except Exception as e:
        logger.warning("Cache delete failed", key=key, error=str(e))
        return False


async def cache_delete_pattern(pattern: str) -> int:
    try:
        client = await get_redis()
        keys = await client.keys(pattern)
        if not keys:
            return 0
        deleted = await client.delete(*keys)
        return deleted
    except Exception as e:
        logger.warning("Cache delete pattern failed", pattern=pattern, error=str(e))
        return 0


async def cache_exists(key: str) -> bool:
    try:
        client = await get_redis()
        result = await client.exists(key)
        return result > 0
    except Exception as e:
        logger.warning("Cache exists check failed", key=key, error=str(e))
        return False


async def cache_increment(key: str, amount: int = 1, ttl: Optional[int] = None) -> Optional[int]:
    try:
        client = await get_redis()
        value = await client.incrby(key, amount)
        if ttl is not None and value == amount:
            await client.expire(key, ttl)
        return value
    except Exception as e:
        logger.warning("Cache increment failed", key=key, error=str(e))
        return None
