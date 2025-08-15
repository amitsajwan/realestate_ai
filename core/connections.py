import redis
import redis.asyncio
from arq import create_pool
from arq.connections import RedisSettings

from .config import settings

async def get_redis_pool():
    try:
        return await redis.asyncio.from_url(f"redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}")
    except (ImportError, AttributeError):
        # Fallback to synchronous Redis if asyncio is not available
        return redis.Redis(host=settings.REDIS_HOST, port=settings.REDIS_PORT, decode_responses=True)

async def get_arq_pool():
    try:
        return await create_pool(
            RedisSettings(host=settings.REDIS_HOST, port=settings.REDIS_PORT)
        )
    except ImportError:
        return None
