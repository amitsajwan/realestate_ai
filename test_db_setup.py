"""Database setup with FakeRedis for testing."""

import fakeredis
import asyncio
from core.config import settings

class AsyncFakeRedis:
    """Async wrapper for FakeRedis."""
    
    def __init__(self):
        self.redis = fakeredis.FakeRedis(decode_responses=True)
    
    async def hset(self, key, mapping=None, **kwargs):
        if mapping:
            return self.redis.hset(key, mapping=mapping)
        return self.redis.hset(key, **kwargs)
    
    async def hget(self, key, field):
        return self.redis.hget(key, field)
    
    async def hgetall(self, key):
        return self.redis.hgetall(key)
    
    async def zadd(self, key, mapping):
        return self.redis.zadd(key, mapping)
    
    async def zrevrange(self, key, start, end):
        return self.redis.zrevrange(key, start, end)
    
    async def zrangebyscore(self, key, min_score, max_score):
        return self.redis.zrangebyscore(key, min_score, max_score)
    
    async def sadd(self, key, *values):
        return self.redis.sadd(key, *values)
    
    async def srem(self, key, *values):
        return self.redis.srem(key, *values)
    
    async def smembers(self, key):
        return self.redis.smembers(key)
    
    async def hincrby(self, key, field, amount=1):
        return self.redis.hincrby(key, field, amount)
    
    async def delete(self, key):
        return self.redis.delete(key)
    
    async def exists(self, key):
        return self.redis.exists(key)

# Override Redis connection for testing
import core.connections

async def get_test_redis_pool():
    """Override Redis pool for testing."""
    return AsyncFakeRedis()

# Replace the real Redis connection with fake for testing
core.connections.get_redis_pool = get_test_redis_pool
