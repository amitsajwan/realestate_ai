"""
Performance Optimization Service
===============================
Comprehensive performance optimization and caching system.
"""

import asyncio
import logging
import time
from typing import Dict, List, Any, Optional, Callable
from datetime import datetime, timedelta
from functools import wraps
import json
import hashlib

logger = logging.getLogger(__name__)


class CacheService:
    """In-memory cache service with TTL support."""
    
    def __init__(self, default_ttl: int = 300):  # 5 minutes default
        self.cache: Dict[str, Dict[str, Any]] = {}
        self.default_ttl = default_ttl
        logger.info("Initialized CacheService")
    
    def _is_expired(self, cache_entry: Dict[str, Any]) -> bool:
        """Check if cache entry is expired."""
        return datetime.utcnow() > cache_entry["expires_at"]
    
    def _clean_expired(self):
        """Remove expired entries from cache."""
        current_time = datetime.utcnow()
        expired_keys = [
            key for key, entry in self.cache.items()
            if current_time > entry["expires_at"]
        ]
        
        for key in expired_keys:
            del self.cache[key]
        
        if expired_keys:
            logger.debug(f"Cleaned {len(expired_keys)} expired cache entries")
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        self._clean_expired()
        
        if key in self.cache:
            entry = self.cache[key]
            if not self._is_expired(entry):
                return entry["value"]
            else:
                del self.cache[key]
        
        return None
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Set value in cache with TTL."""
        ttl = ttl or self.default_ttl
        expires_at = datetime.utcnow() + timedelta(seconds=ttl)
        
        self.cache[key] = {
            "value": value,
            "expires_at": expires_at,
            "created_at": datetime.utcnow()
        }
    
    def delete(self, key: str) -> bool:
        """Delete key from cache."""
        if key in self.cache:
            del self.cache[key]
            return True
        return False
    
    def clear(self) -> None:
        """Clear all cache entries."""
        self.cache.clear()
        logger.info("Cache cleared")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        self._clean_expired()
        
        return {
            "total_entries": len(self.cache),
            "memory_usage_mb": sum(
                len(json.dumps(entry["value"]).encode()) 
                for entry in self.cache.values()
            ) / (1024 * 1024),
            "hit_rate": getattr(self, "_hit_rate", 0),
            "miss_rate": getattr(self, "_miss_rate", 0)
        }


class DatabaseOptimizer:
    """Database query optimization service."""
    
    def __init__(self):
        self.query_cache = CacheService(default_ttl=600)  # 10 minutes
        self.slow_queries: List[Dict[str, Any]] = []
        logger.info("Initialized DatabaseOptimizer")
    
    def optimize_query(self, query: str, params: Dict[str, Any] = None) -> str:
        """Optimize database query."""
        # Basic query optimization
        optimized = query.strip()
        
        # Remove extra whitespace
        optimized = " ".join(optimized.split())
        
        # Add query hints if needed
        if "SELECT" in optimized.upper() and "LIMIT" not in optimized.upper():
            # Add default limit for large result sets
            optimized += " LIMIT 1000"
        
        return optimized
    
    def should_use_cache(self, query: str, params: Dict[str, Any] = None) -> bool:
        """Determine if query should use cache."""
        # Cache SELECT queries only
        if not query.strip().upper().startswith("SELECT"):
            return False
        
        # Don't cache queries with user-specific data
        if params and any(key in str(params).lower() for key in ["user_id", "password", "token"]):
            return False
        
        return True
    
    def get_cache_key(self, query: str, params: Dict[str, Any] = None) -> str:
        """Generate cache key for query."""
        key_data = f"{query}:{json.dumps(params or {}, sort_keys=True)}"
        return hashlib.md5(key_data.encode()).hexdigest()
    
    def record_slow_query(self, query: str, duration: float, params: Dict[str, Any] = None):
        """Record slow query for analysis."""
        self.slow_queries.append({
            "query": query,
            "duration": duration,
            "params": params,
            "timestamp": datetime.utcnow()
        })
        
        # Keep only last 100 slow queries
        if len(self.slow_queries) > 100:
            self.slow_queries = self.slow_queries[-100:]
    
    def get_slow_queries(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get slowest queries."""
        return sorted(
            self.slow_queries,
            key=lambda x: x["duration"],
            reverse=True
        )[:limit]


class PerformanceOptimizer:
    """Main performance optimization service."""
    
    def __init__(self):
        self.cache = CacheService()
        self.db_optimizer = DatabaseOptimizer()
        self.optimization_rules = self._initialize_optimization_rules()
        logger.info("Initialized PerformanceOptimizer")
    
    def _initialize_optimization_rules(self) -> Dict[str, Any]:
        """Initialize performance optimization rules."""
        return {
            "enable_caching": True,
            "cache_ttl": 300,  # 5 minutes
            "max_cache_size": 1000,
            "enable_compression": True,
            "enable_pagination": True,
            "default_page_size": 50,
            "max_page_size": 1000,
            "enable_query_optimization": True,
            "slow_query_threshold": 100,  # ms
            "enable_connection_pooling": True,
            "max_connections": 20
        }
    
    def cache_result(self, key: str, result: Any, ttl: Optional[int] = None):
        """Cache a result."""
        if self.optimization_rules["enable_caching"]:
            self.cache.set(key, result, ttl or self.optimization_rules["cache_ttl"])
    
    def get_cached_result(self, key: str) -> Optional[Any]:
        """Get cached result."""
        if self.optimization_rules["enable_caching"]:
            return self.cache.get(key)
        return None
    
    def generate_cache_key(self, prefix: str, *args, **kwargs) -> str:
        """Generate cache key from arguments."""
        key_data = f"{prefix}:{':'.join(str(arg) for arg in args)}:{json.dumps(kwargs, sort_keys=True)}"
        return hashlib.md5(key_data.encode()).hexdigest()
    
    def optimize_database_query(self, query: str, params: Dict[str, Any] = None) -> str:
        """Optimize database query."""
        if self.optimization_rules["enable_query_optimization"]:
            return self.db_optimizer.optimize_query(query, params)
        return query
    
    def should_cache_query(self, query: str, params: Dict[str, Any] = None) -> bool:
        """Check if query should be cached."""
        return self.db_optimizer.should_use_cache(query, params)
    
    def get_query_cache_key(self, query: str, params: Dict[str, Any] = None) -> str:
        """Get cache key for database query."""
        return self.db_optimizer.get_cache_key(query, params)
    
    def record_query_performance(self, query: str, duration: float, params: Dict[str, Any] = None):
        """Record query performance."""
        if duration > self.optimization_rules["slow_query_threshold"]:
            self.db_optimizer.record_slow_query(query, duration, params)
    
    def get_performance_recommendations(self) -> List[Dict[str, str]]:
        """Get performance optimization recommendations."""
        recommendations = []
        
        # Check cache hit rate
        cache_stats = self.cache.get_stats()
        if cache_stats["total_entries"] > 0:
            hit_rate = cache_stats.get("hit_rate", 0)
            if hit_rate < 0.8:  # Less than 80% hit rate
                recommendations.append({
                    "category": "Caching",
                    "issue": f"Cache hit rate is {hit_rate:.2%}",
                    "recommendation": "Review cache TTL settings and cache key generation"
                })
        
        # Check slow queries
        slow_queries = self.db_optimizer.get_slow_queries(5)
        if slow_queries:
            recommendations.append({
                "category": "Database",
                "issue": f"Found {len(slow_queries)} slow queries",
                "recommendation": "Optimize slow queries and add database indexes"
            })
        
        # Check memory usage
        cache_memory = cache_stats.get("memory_usage_mb", 0)
        if cache_memory > 100:  # More than 100MB
            recommendations.append({
                "category": "Memory",
                "issue": f"Cache using {cache_memory:.2f}MB of memory",
                "recommendation": "Consider reducing cache TTL or implementing cache eviction"
            })
        
        return recommendations
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get comprehensive performance metrics."""
        cache_stats = self.cache.get_stats()
        slow_queries = self.db_optimizer.get_slow_queries(10)
        
        return {
            "cache": cache_stats,
            "slow_queries": slow_queries,
            "optimization_rules": self.optimization_rules,
            "recommendations": self.get_performance_recommendations(),
            "timestamp": datetime.utcnow().isoformat()
        }


# Global performance optimizer instance
performance_optimizer = PerformanceOptimizer()


def cached_result(ttl: int = 300, key_prefix: str = ""):
    """Decorator for caching function results."""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Generate cache key
            cache_key = performance_optimizer.generate_cache_key(
                f"{key_prefix}:{func.__name__}",
                *args,
                **kwargs
            )
            
            # Try to get from cache
            cached_result = performance_optimizer.get_cached_result(cache_key)
            if cached_result is not None:
                logger.debug(f"Cache hit for {func.__name__}")
                return cached_result
            
            # Execute function
            result = await func(*args, **kwargs)
            
            # Cache result
            performance_optimizer.cache_result(cache_key, result, ttl)
            logger.debug(f"Cached result for {func.__name__}")
            
            return result
        
        return wrapper
    return decorator


def optimize_database_query(func):
    """Decorator for optimizing database queries."""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        start_time = time.time()
        
        try:
            result = await func(*args, **kwargs)
            return result
        finally:
            duration = (time.time() - start_time) * 1000  # Convert to ms
            performance_optimizer.record_query_performance(
                func.__name__,
                duration,
                kwargs
            )
    
    return wrapper