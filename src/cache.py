"""Redis caching service for SmartShopper AI."""

import json
import logging
from typing import Optional, Any
import hashlib

try:
    import redis
    HAS_REDIS = True
except ImportError:
    HAS_REDIS = False

from .config import settings

logger = logging.getLogger(__name__)


class CacheService:
    """Redis-based caching service."""
    
    def __init__(self):
        """Initialize Redis client."""
        self.redis_available = False
        self.client = None
        
        if HAS_REDIS:
            try:
                self.client = redis.from_url(settings.redis_url, decode_responses=True)
                # Test connection
                self.client.ping()
                self.redis_available = True
                logger.info("Redis cache initialized successfully")
            except Exception as e:
                logger.warning(f"Failed to initialize Redis cache: {e}")
    
    def _generate_cache_key(self, prefix: str, data: Any) -> str:
        """Generate a cache key from data."""
        # Create a hash of the data for consistent key generation
        data_str = json.dumps(data, sort_keys=True, default=str)
        data_hash = hashlib.md5(data_str.encode()).hexdigest()
        return f"{prefix}:{data_hash}"
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        if not self.redis_available:
            return None
        
        try:
            value = self.client.get(key)
            if value:
                return json.loads(value)
            return None
        except Exception as e:
            logger.warning(f"Cache get error for key {key}: {e}")
            return None
    
    async def set(self, key: str, value: Any, ttl: int = None) -> bool:
        """Set value in cache with optional TTL."""
        if not self.redis_available:
            return False
        
        try:
            ttl = ttl or settings.cache_ttl
            serialized_value = json.dumps(value, default=str)
            result = self.client.setex(key, ttl, serialized_value)
            return bool(result)
        except Exception as e:
            logger.warning(f"Cache set error for key {key}: {e}")
            return False
    
    async def delete(self, key: str) -> bool:
        """Delete value from cache."""
        if not self.redis_available:
            return False
        
        try:
            result = self.client.delete(key)
            return bool(result)
        except Exception as e:
            logger.warning(f"Cache delete error for key {key}: {e}")
            return False
    
    async def get_search_results(self, search_request: Any) -> Optional[Any]:
        """Get cached search results."""
        cache_key = self._generate_cache_key("search", search_request.model_dump())
        return await self.get(cache_key)
    
    async def cache_search_results(self, search_request: Any, search_response: Any, ttl: int = 300) -> bool:
        """Cache search results with shorter TTL (5 minutes default)."""
        cache_key = self._generate_cache_key("search", search_request.model_dump())
        return await self.set(cache_key, search_response.model_dump(), ttl)
    
    async def get_product(self, product_id: str) -> Optional[Any]:
        """Get cached product data."""
        cache_key = f"product:{product_id}"
        return await self.get(cache_key)
    
    async def cache_product(self, product_id: str, product_data: Any, ttl: int = 3600) -> bool:
        """Cache product data with longer TTL (1 hour default)."""
        cache_key = f"product:{product_id}"
        return await self.set(cache_key, product_data, ttl)
    
    async def get_chat_context(self, session_id: str) -> Optional[Any]:
        """Get cached chat context for a session."""
        cache_key = f"chat_context:{session_id}"
        return await self.get(cache_key)
    
    async def cache_chat_context(self, session_id: str, context: Any, ttl: int = 1800) -> bool:
        """Cache chat context with medium TTL (30 minutes default)."""
        cache_key = f"chat_context:{session_id}"
        return await self.set(cache_key, context, ttl)
    
    async def health_check(self) -> bool:
        """Check if Redis is healthy."""
        if not self.redis_available:
            return False
        
        try:
            response = self.client.ping()
            return response is True
        except Exception as e:
            logger.error(f"Redis health check failed: {e}")
            return False
    
    async def clear_cache(self, pattern: str = None) -> int:
        """Clear cache entries matching pattern."""
        if not self.redis_available:
            return 0
        
        try:
            if pattern:
                keys = self.client.keys(pattern)
                if keys:
                    return self.client.delete(*keys)
            else:
                return self.client.flushdb()
            return 0
        except Exception as e:
            logger.error(f"Cache clear error: {e}")
            return 0


# Global cache service instance
cache_service = CacheService()