"""Base repository class for Redis operations."""

import json
from typing import Any, Dict, List, Optional
from datetime import datetime


class BaseRepository:
    """Base repository with common Redis operations."""
    
    def __init__(self, redis_client):
        self.redis = redis_client
        self.prefix = "base"
    
    async def get(self, key: str) -> Optional[str]:
        """Get a value by key."""
        return await self.redis.get(key)
    
    async def set(self, key: str, value: str, expire_seconds: Optional[int] = None) -> bool:
        """Set a value with optional expiration."""
        if expire_seconds:
            return await self.redis.setex(key, expire_seconds, value)
        else:
            return await self.redis.set(key, value)
    
    async def delete(self, key: str) -> bool:
        """Delete a key."""
        return bool(await self.redis.delete(key))
    
    async def exists(self, key: str) -> bool:
        """Check if key exists."""
        return bool(await self.redis.exists(key))
    
    async def expire(self, key: str, seconds: int) -> bool:
        """Set expiration on a key."""
        return bool(await self.redis.expire(key, seconds))
    
    async def keys(self, pattern: str) -> List[str]:
        """Get keys matching pattern."""
        keys = await self.redis.keys(pattern)
        return [key.decode() if isinstance(key, bytes) else key for key in keys]
    
    async def hget(self, key: str, field: str) -> Optional[str]:
        """Get hash field value."""
        value = await self.redis.hget(key, field)
        return value.decode() if isinstance(value, bytes) else value
    
    async def hset(self, key: str, field: str, value: str) -> bool:
        """Set hash field value."""
        return bool(await self.redis.hset(key, field, value))
    
    async def hgetall(self, key: str) -> Dict[str, str]:
        """Get all hash fields."""
        result = await self.redis.hgetall(key)
        return {
            k.decode() if isinstance(k, bytes) else k: 
            v.decode() if isinstance(v, bytes) else v
            for k, v in result.items()
        }
    
    async def hdel(self, key: str, *fields: str) -> int:
        """Delete hash fields."""
        return await self.redis.hdel(key, *fields)
    
    async def hincrby(self, key: str, field: str, amount: int = 1) -> int:
        """Increment hash field by amount."""
        return await self.redis.hincrby(key, field, amount)
    
    async def sadd(self, key: str, *values: str) -> int:
        """Add values to set."""
        return await self.redis.sadd(key, *values)
    
    async def srem(self, key: str, *values: str) -> int:
        """Remove values from set."""
        return await self.redis.srem(key, *values)
    
    async def smembers(self, key: str) -> List[str]:
        """Get all set members."""
        members = await self.redis.smembers(key)
        return [member.decode() if isinstance(member, bytes) else member for member in members]
    
    async def sismember(self, key: str, value: str) -> bool:
        """Check if value is in set."""
        return bool(await self.redis.sismember(key, value))
    
    async def zadd(self, key: str, mapping: Dict[str, float]) -> int:
        """Add values to sorted set."""
        return await self.redis.zadd(key, mapping)
    
    async def zrem(self, key: str, *values: str) -> int:
        """Remove values from sorted set."""
        return await self.redis.zrem(key, *values)
    
    async def zrange(self, key: str, start: int, end: int, withscores: bool = False) -> List:
        """Get sorted set range."""
        return await self.redis.zrange(key, start, end, withscores=withscores)
    
    async def zrevrange(self, key: str, start: int, end: int, withscores: bool = False) -> List:
        """Get sorted set range in reverse order."""
        return await self.redis.zrevrange(key, start, end, withscores=withscores)
    
    async def zrangebyscore(self, key: str, min_score: float, max_score: float) -> List:
        """Get sorted set range by score."""
        return await self.redis.zrangebyscore(key, min_score, max_score)
    
    async def zscore(self, key: str, value: str) -> Optional[float]:
        """Get score of value in sorted set."""
        return await self.redis.zscore(key, value)
    
    def serialize_json(self, data: Any) -> str:
        """Serialize data to JSON string."""
        return json.dumps(data, default=self._json_serializer)
    
    def deserialize_json(self, data: str) -> Any:
        """Deserialize JSON string to data."""
        return json.loads(data)
    
    def _json_serializer(self, obj):
        """Custom JSON serializer for special types."""
        if isinstance(obj, datetime):
            return obj.isoformat()
        return str(obj)
